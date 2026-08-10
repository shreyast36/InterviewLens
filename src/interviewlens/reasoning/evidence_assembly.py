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
