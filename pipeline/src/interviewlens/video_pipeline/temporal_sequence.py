"""2.3 TEMPORAL SEQUENCE BUILDER — Person A.

Maintains a rolling window buffer of pose frames and emits fixed-size
(T, 11, 3) windows every `stride_seconds` for the temporal signal-detection
model (2.4) to consume.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Iterator

import numpy as np

from interviewlens.common.schemas import PoseFrame, PoseWindow


class RollingWindowBuilder:
    def __init__(self, fps: int = 30, window_seconds: int = 4, stride_seconds: int = 1):
        self.window_size = max(1, fps * window_seconds)
        self.stride = max(1, fps * stride_seconds)
        self._buffer: deque[PoseFrame] = deque(maxlen=self.window_size)
        self._since_last_emit = 0

    def push(self, frame: PoseFrame) -> PoseWindow | None:
        self._buffer.append(frame)
        self._since_last_emit += 1

        if len(self._buffer) < self.window_size:
            return None
        if self._since_last_emit < self.stride:
            return None

        self._since_last_emit = 0
        frames = list(self._buffer)
        return PoseWindow(
            start_time_s=frames[0].timestamp_s,
            end_time_s=frames[-1].timestamp_s,
            frames=frames,
        )

    def stream(self, frames: Iterator[PoseFrame]) -> Iterator[PoseWindow]:
        for f in frames:
            window = self.push(f)
            if window is not None:
                yield window


def window_to_array(window: PoseWindow) -> np.ndarray:
    """(T, J, 3) array — T=len(frames), J=11 joints, 3=[x, y, confidence]."""
    from interviewlens.video_pipeline.keypoint_processor import to_array
    return np.stack([to_array(f) for f in window.frames], axis=0)
