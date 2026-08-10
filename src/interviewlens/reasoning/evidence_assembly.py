"""4. MULTIMODAL FUSION & EVIDENCE ASSEMBLY — Person C (ML/Reasoning Engineer).

Aligns visual events and audio metrics by timestamp and packages everything
the VLM needs into a single EvidencePackage. This is the hand-off point
between Person A/B's pipelines and Person C's reasoning stage — keep the
EvidencePackage contract (see common/schemas.py) stable.
"""
from __future__ import annotations

import logging

import numpy as np

from interviewlens.common.schemas import (
    AudioMetrics,
    EvidencePackage,
    SignalType,
    Transcript,
    VisualEvent,
)

logger = logging.getLogger(__name__)

MAX_SELECTED_FRAMES = 6  # per architecture diagram: "Selected Frames (6-12)"


def select_representative_frames(
    visual_events: list[VisualEvent], fps: int, max_frames: int = MAX_SELECTED_FRAMES,
) -> list[int]:
    """Pick frame indices around each event's midpoint, capped at max_frames,
    so the VLM only has to look at a handful of representative images.
    """
    frames: list[int] = []
    for event in visual_events:
        midpoint = (event.start_time_s + event.end_time_s) / 2
        frames.append(int(midpoint * fps))
    seen: set[int] = set()
    unique = [f for f in frames if not (f in seen or seen.add(f))]
    return unique[:max_frames]


def _extract_frame_crops(
    frame_indices: list[int],
    all_frames: dict[int, np.ndarray],
) -> list:
    """Convert selected numpy frames (OpenCV BGR) to RGB PIL Images.

    The VLM expects standard PIL Images; OpenCV stores channels as BGR,
    so we reverse the channel axis before wrapping in PIL.
    """
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not installed — frame images will be empty.")
        return []

    crops = []
    for idx in frame_indices:
        frame = all_frames.get(idx)
        if frame is not None:
            rgb = frame[..., ::-1].copy()  # BGR → RGB (copy makes it contiguous)
            crops.append(Image.fromarray(rgb))
        else:
            logger.debug("Frame index %d not found in all_frames, skipping.", idx)
    return crops


def assemble_evidence(
    question: str,
    transcript: Transcript,
    audio_metrics: AudioMetrics,
    visual_events: list[VisualEvent],
    fps: int = 30,
    all_frames: dict[int, np.ndarray] | None = None,
) -> EvidencePackage:
    """Assemble all pipeline outputs into a single EvidencePackage for the VLM.

    Pass *all_frames* (a dict mapping frame_index → BGR numpy array from the
    video pipeline) to populate frame_images with actual PIL Image crops.
    When omitted the package still works but frame_images will be empty and
    the VLM will fall back to text-only / mock reasoning.
    """
    selected_frames = select_representative_frames(visual_events, fps)
    frame_images = _extract_frame_crops(selected_frames, all_frames) if all_frames else []

    event_timestamps = {
        "visual_events": [
            {
                "type": e.signal_type.value,
                "start": e.start_time_s,
                "end": e.end_time_s,
                "confidence": e.confidence,
            }
            for e in visual_events
        ],
        "long_pauses": audio_metrics.long_pause_timestamps,
    }

    return EvidencePackage(
        question=question,
        transcript=transcript,
        audio_metrics=audio_metrics,
        visual_events=visual_events,
        selected_frames=selected_frames,
        event_timestamps=event_timestamps,
        frame_images=frame_images,
    )


# ---------------------------------------------------------------------------
# Adapter for A/B's fused_evidence.json hand-off format
# ---------------------------------------------------------------------------

_FLAG_TO_SIGNAL: dict[str, SignalType] = {
    "headroom_too_loose":    SignalType.HEADROOM_TOO_LOOSE,
    "off_center":            SignalType.OFF_CENTER,
    "tilted":                SignalType.TILTED,
    "background_distracting": SignalType.BACKGROUND_DISTRACTING,
    # original temporal-model signals, if A ever emits them via flags too
    "repetitive_hand_movement": SignalType.REPETITIVE_HAND_MOVEMENT,
    "frequent_posture_shifting": SignalType.FREQUENT_POSTURE_SHIFTING,
    "hand_to_face_activity":     SignalType.HAND_TO_FACE_ACTIVITY,
    # rule-based pose signals (00_master_pipeline.ipynb §5) — see schemas.py
    "hands_near_face":    SignalType.HANDS_NEAR_FACE,
    "self_grooming":      SignalType.SELF_GROOMING,
    "arms_crossed":       SignalType.ARMS_CROSSED,
    "hands_not_visible":  SignalType.HANDS_NOT_VISIBLE,
    "head_drop":          SignalType.HEAD_DROP,
    "shoulders_raised":   SignalType.SHOULDERS_RAISED,
    "head_turned_away":   SignalType.HEAD_TURNED_AWAY,
    "looking_down":       SignalType.LOOKING_DOWN,
    "head_tilt":          SignalType.HEAD_TILT,
    "body_lean":          SignalType.BODY_LEAN,
    "leaning_in":         SignalType.LEANING_IN,
    "leaning_out":        SignalType.LEANING_OUT,
    "fidgeting":          SignalType.FIDGETING,
    "frozen":             SignalType.FROZEN,
    "sudden_movement":    SignalType.SUDDEN_MOVEMENT,
    "swaying":            SignalType.SWAYING,
    "nodding":            SignalType.NODDING,
    "unstable_tracking":  SignalType.UNSTABLE_TRACKING,
    "transient_object":   SignalType.TRANSIENT_OBJECT,
}


def _collapse_flag_spans(timeline: list[dict], step: float) -> list[tuple[str, str, float, float]]:
    """Merge consecutive fused-timeline ticks carrying the same flag into one
    (key, detail, start_s, end_s) span instead of one entry per tick.

    fused_evidence.json repeats a still-active flag (e.g. a laptop that sits
    in frame for the whole clip) at every sampled timestamp — reading it
    naively turns one real event into dozens of near-duplicate VisualEvents
    (a "laptop detected" observation once per timestamp). This reconstructs
    the actual event boundaries the notebook's own hysteresis/track-window
    logic already establishes.
    """
    open_spans: dict[tuple[str, str], tuple[float, float]] = {}  # key -> (start, last_seen)
    closed: list[tuple[str, str, float, float]] = []

    for entry in timeline:
        t = float(entry["timestamp_s"])
        active_now: set[tuple[str, str]] = set()
        for flag in entry.get("flags", []):
            key, _, detail = flag.partition(":")
            active_now.add((key, detail))
            start, _ = open_spans.get((key, detail), (t, t))
            open_spans[(key, detail)] = (start, t)
        for span_key in list(open_spans):
            if span_key not in active_now:
                start, last = open_spans.pop(span_key)
                closed.append((*span_key, start, last + step))

    for (key, detail), (start, last) in open_spans.items():
        closed.append((key, detail, start, last + step))

    closed.sort(key=lambda e: e[2])
    return closed


def from_fused_evidence_json(
    data: dict,
    question: str,
    transcript: Transcript,
    audio_metrics: AudioMetrics,
    all_frames: dict[int, np.ndarray] | None = None,
) -> EvidencePackage:
    """Convert A/B's fused_evidence.json timeline into an EvidencePackage.

    *data* is the parsed JSON dict produced by A/B's notebook fusion step.
    The per-timestamp flags are mapped to VisualEvent objects; framing
    metrics and background detections are carried through in event_timestamps
    so build_prompt() can include them in the VLM context.
    """
    fps_fused: int = int(data.get("fps_fused", 3))
    step: float = 1.0 / fps_fused

    unknown_flags: set[str] = set()
    visual_events: list[VisualEvent] = []
    background_objects: list[dict] = []
    for key, detail, start, end in _collapse_flag_spans(data.get("timeline", []), step):
        signal = _FLAG_TO_SIGNAL.get(key)
        if signal is None:
            unknown_flags.add(key)
            continue
        visual_events.append(
            VisualEvent(signal_type=signal, start_time_s=start, end_time_s=end, confidence=1.0)
        )
        if signal in (SignalType.BACKGROUND_DISTRACTING, SignalType.TRANSIENT_OBJECT) and detail:
            background_objects.append({
                "object": detail, "tier": "distracting" if signal == SignalType.BACKGROUND_DISTRACTING else "transient",
                "start_s": start, "end_s": end,
            })
    if unknown_flags:
        logger.warning("Unmapped flag(s) from fused_evidence.json — add to _FLAG_TO_SIGNAL: %s", sorted(unknown_flags))

    # Framing metrics, one row per fused timestamp — kept dense (not collapsed
    # into spans) since these are continuous measurements, not discrete events.
    framing_summary = [
        {**entry["pose"]["framing"], "timestamp_s": float(entry["timestamp_s"])}
        for entry in data.get("timeline", [])
        if entry.get("pose", {}).get("framing") is not None
    ]

    selected_frames = select_representative_frames(visual_events, fps_fused)
    frame_images = _extract_frame_crops(selected_frames, all_frames) if all_frames else []

    event_timestamps = {
        "visual_events": [
            {"type": e.signal_type.value, "start": e.start_time_s,
             "end": e.end_time_s, "confidence": e.confidence}
            for e in visual_events
        ],
        "long_pauses":        audio_metrics.long_pause_timestamps,
        "framing_summary":    framing_summary,
        "background_objects": background_objects,
        # Pass A/B's own aggregate straight through when present (added
        # alongside the rule-based signals) so build_prompt() can cite
        # counts/durations instead of restating every individual event.
        "signal_summary":     data.get("signal_summary"),
    }

    return EvidencePackage(
        question=question,
        transcript=transcript,
        audio_metrics=audio_metrics,
        visual_events=visual_events,
        selected_frames=selected_frames,
        event_timestamps=event_timestamps,
        frame_images=frame_images,
    )
