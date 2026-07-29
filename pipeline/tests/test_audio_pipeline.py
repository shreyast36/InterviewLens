from interviewlens.audio_pipeline.asr import build_asr_model
from interviewlens.audio_pipeline.capture import synthetic_audio
from interviewlens.audio_pipeline.delivery_analytics import compute_metrics
from interviewlens.audio_pipeline.preprocessing import SpeechSegment, preprocess


def test_preprocess_returns_segments():
    audio = synthetic_audio(duration_s=3.0, sample_rate=16000)
    segments = preprocess(audio, sample_rate=16000)
    assert isinstance(segments, list)


def test_asr_mock_transcribe():
    seg = SpeechSegment(audio=synthetic_audio(2.0), start_time_s=0.0, end_time_s=2.0)
    model = build_asr_model("whisper-small")
    transcript = model.transcribe(seg)
    assert transcript.text
    assert len(transcript.words) > 0


def test_delivery_metrics_shape():
    seg = SpeechSegment(audio=synthetic_audio(2.0), start_time_s=0.0, end_time_s=2.0)
    model = build_asr_model("whisper-small")
    transcript = model.transcribe(seg)
    metrics = compute_metrics(transcript, total_duration_s=2.0)
    assert metrics.words_per_minute >= 0
