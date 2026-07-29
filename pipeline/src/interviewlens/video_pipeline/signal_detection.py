"""2.4 DISTRACTING-SIGNAL DETECTION — Person A.

Champion model: PoseFormerV2-inspired Transformer
Challenger model: ST-GCN

Both consume a (T, J, 3) pose window and emit VisualEvent objects for the
three tracked signals. Swap champion/challenger during evaluation; keep the
public `SignalDetector.detect(window) -> list[VisualEvent]` interface stable
so Person C's fusion code never has to change.
"""
from __future__ import annotations

import abc

import numpy as np

from interviewlens.common.schemas import PoseWindow, SignalType, VisualEvent
from interviewlens.video_pipeline.temporal_sequence import window_to_array


class SignalDetector(abc.ABC):
    @abc.abstractmethod
    def detect(self, window: PoseWindow) -> list[VisualEvent]:
        ...


class PoseFormerV2Detector(SignalDetector):
    """Champion. TODO(Person A): load real PoseFormerV2-inspired transformer."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self._model = None

    def detect(self, window: PoseWindow) -> list[VisualEvent]:
        arr = window_to_array(window)
        if self._model is None:
            return _mock_signals(window, arr)
        raise NotImplementedError("Wire up real PoseFormerV2 inference here")


class STGCNDetector(SignalDetector):
    """Challenger. TODO(Person A): load real ST-GCN checkpoint."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self._model = None

    def detect(self, window: PoseWindow) -> list[VisualEvent]:
        arr = window_to_array(window)
        if self._model is None:
            return _mock_signals(window, arr)
        raise NotImplementedError("Wire up real ST-GCN inference here")


def build_signal_detector(model_name: str) -> SignalDetector:
    if model_name in ("poseformerv2", "champion"):
        return PoseFormerV2Detector()
    if model_name in ("st-gcn", "stgcn", "challenger"):
        return STGCNDetector()
    raise ValueError(f"Unknown signal model: {model_name}")


def _mock_signals(window: PoseWindow, arr: np.ndarray) -> list[VisualEvent]:
    """Simple heuristic placeholder: flags high joint-position variance as
    'repetitive hand movement' so the rest of the pipeline has real-looking
    events to fuse/report on before the real model is trained."""
    variance = float(np.var(arr[:, :, :2]))
    events: list[VisualEvent] = []
    if variance > 0.05:
        events.append(VisualEvent(
            signal_type=SignalType.REPETITIVE_HAND_MOVEMENT,
            start_time_s=window.start_time_s,
            end_time_s=window.end_time_s,
            confidence=min(0.99, variance),
        ))
    return events
