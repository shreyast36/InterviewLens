"""2.1 POSE ESTIMATION — Person A.

Champion model: RTMPose-S (fast, good accuracy)
Challenger model: SimpleBaseline

Both models implement `PoseEstimator.estimate(frame) -> PoseFrame`. Swap
champion/challenger via `configs/config.yaml: video.pose_model`.
"""
from __future__ import annotations

import abc

import numpy as np

from interviewlens.common.schemas import Keypoint, PoseFrame

# 11 upper-body keypoints, per architecture spec (block 2.2)
UPPER_BODY_JOINTS = [
    "nose", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip", "left_eye", "right_eye",
]


class PoseEstimator(abc.ABC):
    @abc.abstractmethod
    def estimate(self, frame: np.ndarray, frame_index: int, timestamp_s: float) -> PoseFrame:
        ...


class RTMPoseEstimator(PoseEstimator):
    """Champion model. TODO(Person A): load real RTMPose-S weights + inference."""

    def __init__(self, model_path: str | None = None, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self._model = None  # TODO: load real checkpoint here

    def estimate(self, frame: np.ndarray, frame_index: int, timestamp_s: float) -> PoseFrame:
        if self._model is None:
            return _mock_pose_frame(frame_index, timestamp_s)
        raise NotImplementedError("Wire up real RTMPose inference here")


class SimpleBaselineEstimator(PoseEstimator):
    """Challenger model. TODO(Person A): load real SimpleBaseline weights."""

    def __init__(self, model_path: str | None = None, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self._model = None

    def estimate(self, frame: np.ndarray, frame_index: int, timestamp_s: float) -> PoseFrame:
        if self._model is None:
            return _mock_pose_frame(frame_index, timestamp_s)
        raise NotImplementedError("Wire up real SimpleBaseline inference here")


def build_pose_estimator(model_name: str) -> PoseEstimator:
    if model_name in ("rtmpose-s", "champion"):
        return RTMPoseEstimator()
    if model_name in ("simplebaseline", "challenger"):
        return SimpleBaselineEstimator()
    raise ValueError(f"Unknown pose_model: {model_name}")


def _mock_pose_frame(frame_index: int, timestamp_s: float) -> PoseFrame:
    """Deterministic placeholder output so downstream code is testable
    before a real pose model is wired in."""
    rng = np.random.default_rng(frame_index)
    keypoints = [
        Keypoint(name=j, x=float(rng.uniform(0, 1)), y=float(rng.uniform(0, 1)),
                 confidence=float(rng.uniform(0.6, 1.0)))
        for j in UPPER_BODY_JOINTS
    ]
    return PoseFrame(frame_index=frame_index, timestamp_s=timestamp_s, keypoints=keypoints)
