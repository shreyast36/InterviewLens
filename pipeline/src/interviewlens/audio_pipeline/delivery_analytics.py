"""3.4 DELIVERY ANALYTICS — Person B.

Turns a raw Transcript into the AudioMetrics contract consumed by the
multimodal fusion stage (Person C) and the coaching-report stage (Person D).
"""
from __future__ import annotations

from interviewlens.audio_pipeline.postprocessing import (
    LONG_PAUSE_THRESHOLD_S,
    detect_pauses,
    identify_filler_words,
)
from interviewlens.common.schemas import AudioMetrics, Transcript


def compute_metrics(transcript: Transcript, total_duration_s: float) -> AudioMetrics:
    words = transcript.words
    if not words:
        return AudioMetrics(
            words_per_minute=0.0, filler_word_count=0, filler_word_rate=0.0,
            long_pause_count=0, long_pause_timestamps=[], speaking_time_s=0.0,
        )

    speaking_time_s = words[-1].end_time_s - words[0].start_time_s
    minutes = max(speaking_time_s / 60.0, 1e-6)
    wpm = len(words) / minutes

    fillers = identify_filler_words(transcript)
    filler_rate = len(fillers) / max(len(words), 1)

    pauses = detect_pauses(transcript, LONG_PAUSE_THRESHOLD_S)

    return AudioMetrics(
        words_per_minute=round(wpm, 1),
        filler_word_count=len(fillers),
        filler_word_rate=round(filler_rate, 3),
        long_pause_count=len(pauses),
        long_pause_timestamps=pauses,
        speaking_time_s=round(speaking_time_s, 2),
        confidence_scores=[w.confidence for w in words],
    )
