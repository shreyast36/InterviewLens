from interviewlens.common.schemas import AudioMetrics, ReasoningOutput, ValidationResult
from interviewlens.reporting.coaching_report import build_coaching_report


def test_build_coaching_report():
    metrics = AudioMetrics(
        words_per_minute=140, filler_word_count=3, filler_word_rate=0.1,
        long_pause_count=2, long_pause_timestamps=[(1.0, 2.2), (4.0, 5.5)],
        speaking_time_s=110,
    )
    reasoning = ReasoningOutput(
        observations=["Spoke at a steady pace."],
        explanations=["Consistent pacing aids clarity."],
        suggestions=["Reduce filler words."],
    )
    validation = ValidationResult(passed=True, reliability_score=0.9)

    report = build_coaching_report(
        duration_s=118, valid_tracking_pct=92.0, audio_metrics=metrics,
        visual_events=[], reasoning=reasoning, validation=validation,
    )
    assert report.reliability_score == 0.9
    assert report.strengths
