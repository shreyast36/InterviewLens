import pytest

from interviewlens.audio_pipeline.asr import build_asr_model
from interviewlens.audio_pipeline.capture import synthetic_audio
from interviewlens.audio_pipeline.delivery_analytics import compute_metrics
from interviewlens.audio_pipeline.preprocessing import SpeechSegment, preprocess


def test_preprocess_returns_segments():
    audio = synthetic_audio(duration_s=3.0, sample_rate=16000)
    segments = preprocess(audio, sample_rate=16000)
    assert isinstance(segments, list)


def _whisper_or_skip():
    """Real faster-whisper model, skipped if the package/weights aren't
    available (no network / not installed) rather than falling back to
    fake data — see asr.py, the mock ASR path was removed."""
    model = build_asr_model("whisper-small")
    try:
        model._get_model()
    except RuntimeError as exc:
        pytest.skip(str(exc))
    return model


def test_asr_transcribe_returns_transcript_shape():
    seg = SpeechSegment(audio=synthetic_audio(2.0), start_time_s=0.0, end_time_s=2.0)
    model = _whisper_or_skip()
    transcript = model.transcribe(seg)
    assert isinstance(transcript.text, str)
    assert isinstance(transcript.words, list)


def test_delivery_metrics_shape():
    seg = SpeechSegment(audio=synthetic_audio(2.0), start_time_s=0.0, end_time_s=2.0)
    model = _whisper_or_skip()
    transcript = model.transcribe(seg)
    metrics = compute_metrics(transcript, total_duration_s=2.0)
    assert metrics.words_per_minute >= 0
