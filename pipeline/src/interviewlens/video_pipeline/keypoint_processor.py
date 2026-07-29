"""2.2 KEYPOINT OUTPUT — Person A.

Normalizes raw pose-estimator output into the fixed (11, 3) array contract
described in the architecture doc: [x, y, confidence] per joint, plus a
visibility flag derived from a confidence threshold.
"""
from __future__ import annotations

import numpy as np

from interviewlens.common.schemas import PoseFrame

VISIBILITY_THRESHOLD = 0.3


def to_array(pose_frame: PoseFrame) -> np.ndarray:
    """Returns an (11, 3) array: [x, y, confidence] per joint."""
    return np.array(
        [[kp.x, kp.y, kp.confidence] for kp in pose_frame.keypoints],
        dtype=np.float32,
    )


def visibility_flags(pose_frame: PoseFrame, threshold: float = VISIBILITY_THRESHOLD) -> np.ndarray:
    return np.array(
        [kp.confidence >= threshold for kp in pose_frame.keypoints],
        dtype=bool,
    )


def normalize_frame(pose_frame: PoseFrame, threshold: float = VISIBILITY_THRESHOLD) -> PoseFrame:
    """Attach visibility flags in place and clip coordinates to [0, 1]."""
    for kp in pose_frame.keypoints:
        kp.x = float(np.clip(kp.x, 0.0, 1.0))
        kp.y = float(np.clip(kp.y, 0.0, 1.0))
    pose_frame.visibility = visibility_flags(pose_frame, threshold).tolist()
    return pose_frame


def valid_tracking_pct(frames: list[PoseFrame], threshold: float = VISIBILITY_THRESHOLD) -> float:
    """Percentage of frames where every joint is above the visibility
    threshold. Used for the coaching report's 'Valid Tracking %' metric."""
    if not frames:
        return 0.0
    fully_visible = sum(
        1 for f in frames if all(v for v in visibility_flags(f, threshold))
    )
    return round(100.0 * fully_visible / len(frames), 1)
