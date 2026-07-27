"""1.A Video capture — Person A (Visual/Pose Engineer).

Wraps OpenCV VideoCapture so the rest of the visual pipeline only ever sees
plain numpy frames + timestamps, regardless of camera/backend.
"""
from __future__ import annotations

import time
from collections.abc import Iterator

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover - optional at dev time
    cv2 = None


class VideoStream:
    """Iterates (frame, timestamp_s) tuples from a webcam or video file."""

    def __init__(self, source: int | str = 0, fps: int = 30):
        self.source = source
        self.fps = fps
        self._cap = None

    def __enter__(self) -> "VideoStream":
        if cv2 is None:
            raise RuntimeError("opencv-python is required for live capture")
        self._cap = cv2.VideoCapture(self.source)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)
        return self

    def __exit__(self, *exc):
        if self._cap is not None:
            self._cap.release()

    def frames(self) -> Iterator[tuple[np.ndarray, float]]:
        start = time.time()
        frame_idx = 0
        while True:
            ok, frame = self._cap.read()
            if not ok:
                break
            timestamp = frame_idx / self.fps
            yield frame, timestamp
            frame_idx += 1


def synthetic_frames(n_frames: int = 120, fps: int = 30, size=(720, 1280, 3)):
    """Deterministic fake frames for tests / demo_mode — no camera required."""
    rng = np.random.default_rng(42)
    for i in range(n_frames):
        yield rng.integers(0, 255, size=size, dtype=np.uint8), i / fps
