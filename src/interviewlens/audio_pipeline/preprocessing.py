"""3.1 AUDIO PREPROCESSING — Person B.

Cleans raw microphone audio before it reaches ASR: noise reduction, level
normalization, voice-activity-detection (VAD) based speech segmentation,
and framing/buffering into ASR-ready chunks.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SpeechSegment:
    audio: np.ndarray
    start_time_s: float
    end_time_s: float


def reduce_noise(audio: np.ndarray) -> np.ndarray:
    """TODO(Person B): swap for a real spectral-gating / RNNoise model.
    Placeholder: simple DC-offset removal + soft clipping."""
    audio = audio - np.mean(audio)
    return np.clip(audio, -1.0, 1.0)


def normalize_level(audio: np.ndarray, target_peak: float = 0.9) -> np.ndarray:
    peak = np.max(np.abs(audio)) + 1e-8
    return audio * (target_peak / peak)


def detect_speech_segments(
    audio: np.ndarray,
    sample_rate: int,
    frame_ms: int = 30,
    energy_threshold: float = 0.01,
    min_silence_ms: float = 300,
    min_speech_ms: float = 150,
) -> list[SpeechSegment]:
    """Small energy-based VAD placeholder.
    TODO(Person B): replace with webrtcvad / silero-vad for production.

    Real (noisy) audio has energy flickering above/below `energy_threshold`
    every frame, so a naive frame-by-frame toggle fragments a single spoken
    phrase into dozens of 30-200ms segments. Each of those pays faster-whisper's
    fixed per-call overhead (~1-2s on CPU) independent of segment length, and
    Whisper tends to hallucinate stock phrases ("Thank you.") on near-silent
    clips -- on a 29s test clip this produced 69 segments and ~90s of transcribe
    time. Two passes fix it: (1) bridge silence gaps shorter than
    `min_silence_ms` so brief pauses within a sentence don't split it, then
    (2) drop whatever is still shorter than `min_speech_ms` as noise.
    """
    frame_len = max(1, int(sample_rate * frame_ms / 1000))
    raw_runs: list[tuple[int, int]] = []
    in_speech = False
    seg_start = 0

    for i in range(0, max(len(audio) - frame_len, 0), frame_len):
        frame = audio[i:i + frame_len]
        energy = float(np.mean(frame ** 2))
        is_speech = energy > energy_threshold

        if is_speech and not in_speech:
            seg_start = i
            in_speech = True
        elif not is_speech and in_speech:
            raw_runs.append((seg_start, i))
            in_speech = False

    if in_speech:
        raw_runs.append((seg_start, len(audio)))

    if not raw_runs:
        return []

    min_silence_samples = int(sample_rate * min_silence_ms / 1000)
    merged_runs: list[list[int]] = [list(raw_runs[0])]
    for start, end in raw_runs[1:]:
        if start - merged_runs[-1][1] <= min_silence_samples:
            merged_runs[-1][1] = end
        else:
            merged_runs.append([start, end])

    min_speech_samples = int(sample_rate * min_speech_ms / 1000)
    return [
        SpeechSegment(
            audio=audio[start:end],
            start_time_s=start / sample_rate,
            end_time_s=end / sample_rate,
        )
        for start, end in merged_runs
        if end - start >= min_speech_samples
    ]


def preprocess(audio: np.ndarray, sample_rate: int) -> list[SpeechSegment]:
    clean = normalize_level(reduce_noise(audio))
    return detect_speech_segments(clean, sample_rate)
