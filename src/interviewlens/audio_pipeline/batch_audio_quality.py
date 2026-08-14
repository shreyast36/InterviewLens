"""Batch audio-quality signal detection for uploaded videos — Person B.

Lightweight, signal-level audio-quality checks -- NOT ASR/transcription (that's a
separate concern in asr.py / delivery_analytics.py; see
orchestration/pipeline.py::run_pipeline_from_video, which now reuses
`extract_audio_samples` from this module as the real audio source for ASR too).
This module answers a narrower question: "is the interviewee's audio usable at
all?" -- too quiet, or cutting in and out -- using plain RMS-energy analysis, no
model.

Extracts the uploaded video's real audio track via ffmpeg/ffprobe (external system
binaries, not Python packages -- both are already present on this machine; deployment
environments need them on PATH too). If the video has no audio track at all, or ffmpeg
is unavailable, this returns an empty result -- never raises -- per the explicit
requirement that a video without audio must not error out the pipeline.
"""
from __future__ import annotations

import logging
import shutil
import subprocess

import numpy as np

from interviewlens.video_pipeline.batch_pose import events_from_boolean_series

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
WINDOW_S = 0.5              # RMS analysis window
SILENCE_RMS_DBFS = -40.0    # below this -> counted as silence for transition detection
LOW_MIC_RMS_DBFS = -30.0    # sustained level below this -> mic too quiet
LOW_MIC_MIN_CONSEC_S = 2.0  # how long "too quiet" must persist before it's a real event
INTERMITTENT_ROLLING_WINDOW_S = 20.0   # window used to compute the silence<->signal transition rate
INTERMITTENT_TRANSITIONS_PER_MIN = 20.0  # above this rate = choppy/dropping audio, not natural pauses
INTERMITTENT_MIN_CONSEC_S = 2.0

_EMPTY_RESULT = {"has_audio": False, "signal_events": []}


def _has_audio_stream(video_path: str) -> bool:
    if shutil.which("ffprobe") is None:
        logger.warning("ffprobe not found on PATH -- skipping audio quality analysis.")
        return False
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
             "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return bool(result.stdout.strip())


def extract_audio_samples(video_path: str, sample_rate: int = SAMPLE_RATE) -> np.ndarray | None:
    """Decodes the video's real audio track to mono float32 PCM via ffmpeg.

    Public so other subsystems (ASR) can reuse the same real audio instead
    of falling back to synthetic placeholders. Returns None if the video has
    no audio track, ffmpeg is unavailable, or decoding fails.
    """
    if shutil.which("ffmpeg") is None:
        logger.warning("ffmpeg not found on PATH -- skipping audio quality analysis.")
        return None
    try:
        proc = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(video_path), "-vn",
             "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "1", "-ar", str(sample_rate), "-"],
            capture_output=True, timeout=120,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        logger.warning("ffmpeg audio extraction failed (%s) -- skipping audio quality analysis.", exc)
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    return np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def _windowed_rms_dbfs(samples: np.ndarray, sample_rate: int, window_s: float) -> tuple[np.ndarray, np.ndarray]:
    win = max(1, int(window_s * sample_rate))
    n_windows = len(samples) // win
    ts = np.arange(n_windows) * window_s
    rms_db = np.full(n_windows, -120.0)
    for i in range(n_windows):
        chunk = samples[i * win:(i + 1) * win]
        rms = np.sqrt(np.mean(chunk.astype(np.float64) ** 2))
        if rms > 1e-9:
            rms_db[i] = 20 * np.log10(rms)
    return ts, rms_db


def _rolling_count(flags: np.ndarray, w: int) -> np.ndarray:
    csum = np.cumsum(flags.astype(float))
    out = np.zeros(len(flags))
    for i in range(len(flags)):
        lo = max(0, i - w + 1)
        out[i] = csum[i] - (csum[lo - 1] if lo > 0 else 0.0)
    return out


def extract_audio_quality_evidence(video_path: str) -> dict:
    """Returns {"has_audio": bool, "signal_events": [{"type","start_s","end_s"}, ...]}.

    signal_events uses the same shape as batch_pose.detect_signal_events() /
    batch_background's lighting events, so ab_fusion.fuse_evidence() can merge all
    three sources identically.
    """
    if not _has_audio_stream(video_path):
        return dict(_EMPTY_RESULT)

    samples = extract_audio_samples(video_path)
    if samples is None or len(samples) == 0:
        return dict(_EMPTY_RESULT)

    ts, rms_db = _windowed_rms_dbfs(samples, SAMPLE_RATE, WINDOW_S)
    if len(ts) == 0:
        return dict(_EMPTY_RESULT)

    signal_events: list[dict] = []

    low_mic_min_consec = max(1, round(LOW_MIC_MIN_CONSEC_S / WINDOW_S))
    low_mic_flags = (rms_db < LOW_MIC_RMS_DBFS).tolist()
    signal_events += events_from_boolean_series("low_mic_level", low_mic_flags, ts, low_mic_min_consec)

    # Intermittent audio: a high rate of silence<->signal transitions in a rolling
    # window suggests audio cutting in and out (dropped connection), as opposed to a
    # normal conversation's handful of longer pauses.
    is_silent = rms_db < SILENCE_RMS_DBFS
    transitions = np.abs(np.diff(is_silent.astype(int)))
    transitions = np.concatenate([[0], transitions]).astype(float)
    roll_win = max(1, round(INTERMITTENT_ROLLING_WINDOW_S / WINDOW_S))
    trans_count = _rolling_count(transitions, roll_win)
    trans_per_min = trans_count / (roll_win * WINDOW_S) * 60.0
    intermittent_min_consec = max(1, round(INTERMITTENT_MIN_CONSEC_S / WINDOW_S))
    intermittent_flags = (trans_per_min > INTERMITTENT_TRANSITIONS_PER_MIN).tolist()
    signal_events += events_from_boolean_series("intermittent_audio", intermittent_flags, ts, intermittent_min_consec)

    signal_events.sort(key=lambda e: (e["start_s"], e["type"]))
    return {"has_audio": True, "signal_events": signal_events}
