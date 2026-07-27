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
) -> list[SpeechSegment]:
    """Very small energy-based VAD placeholder.
    TODO(Person B): replace with webrtcvad / silero-vad for production."""
    frame_len = max(1, int(sample_rate * frame_ms / 1000))
    segments: list[SpeechSegment] = []
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
            segments.append(SpeechSegment(
                audio=audio[seg_start:i],
                start_time_s=seg_start / sample_rate,
                end_time_s=i / sample_rate,
            ))
            in_speech = False

    if in_speech:
        segments.append(SpeechSegment(
            audio=audio[seg_start:],
            start_time_s=seg_start / sample_rate,
            end_time_s=len(audio) / sample_rate,
        ))
    return segments


def preprocess(audio: np.ndarray, sample_rate: int) -> list[SpeechSegment]:
    clean = normalize_level(reduce_noise(audio))
    return detect_speech_segments(clean, sample_rate)
