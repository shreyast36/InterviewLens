"""1.B Audio capture — Person B (Audio/Speech Engineer)."""
from __future__ import annotations

from collections.abc import Iterator

import numpy as np

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None


class AudioStream:
    """Yields fixed-size mono PCM chunks from the microphone."""

    def __init__(self, sample_rate: int = 16000, chunk_seconds: float = 1.0):
        self.sample_rate = sample_rate
        self.chunk_samples = int(sample_rate * chunk_seconds)

    def chunks(self) -> Iterator[np.ndarray]:
        if sd is None:
            raise RuntimeError("sounddevice is required for live capture")
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as stream:
            while True:
                data, _ = stream.read(self.chunk_samples)
                yield data.reshape(-1)


def synthetic_audio(duration_s: float = 10.0, sample_rate: int = 16000) -> np.ndarray:
    """Deterministic fake waveform for tests / demo_mode."""
    rng = np.random.default_rng(7)
    n = int(duration_s * sample_rate)
    t = np.linspace(0, duration_s, n, endpoint=False)
    tone = 0.05 * np.sin(2 * np.pi * 220 * t)
    noise = rng.normal(0, 0.01, n)
    return (tone + noise).astype(np.float32)
