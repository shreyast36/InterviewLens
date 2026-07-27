"""4. MULTIMODAL FUSION & EVIDENCE ASSEMBLY — Person C (ML/Reasoning Engineer).

Aligns visual events and audio metrics by timestamp and packages everything
the VLM needs into a single EvidencePackage. This is the hand-off point
between Person A/B's pipelines and Person C's reasoning stage — keep the
EvidencePackage contract (see common/schemas.py) stable.
"""
from __future__ import annotations

from interviewlens.common.schemas import (
    AudioMetrics,
    EvidencePackage,
    Transcript,
    VisualEvent,
)

MAX_SELECTED_FRAMES = 6  # per architecture diagram: "Selected Frames (6-12)"


def select_representative_frames(
    visual_events: list[VisualEvent], fps: int, max_frames: int = MAX_SELECTED_FRAMES,
) -> list[int]:
    """Pick frame indices around each event's midpoint, capped at max_frames,
    so the VLM only has to look at a handful of representative images.

    TODO(Person C): once real video frames are available end-to-end, extend
    this to also return the actual image crops (not just indices) for the
    VLM to consume.
    """
    frames: list[int] = []
    for event in visual_events:
        midpoint = (event.start_time_s + event.end_time_s) / 2
        frames.append(int(midpoint * fps))
    seen: set[int] = set()
    unique = [f for f in frames if not (f in seen or seen.add(f))]
    return unique[:max_frames]


def assemble_evidence(
    question: str,
    transcript: Transcript,
    audio_metrics: AudioMetrics,
    visual_events: list[VisualEvent],
    fps: int = 30,
) -> EvidencePackage:
    selected_frames = select_representative_frames(visual_events, fps)

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
    )
