"""7. COACHING REPORT (post-response) — Person D (Platform/Product Engineer).

Combines everything upstream (audio metrics, visual events, VLM reasoning,
validation result) into the final user-facing CoachingReport.
"""
from __future__ import annotations

from interviewlens.common.schemas import (
    AudioMetrics,
    CoachingReport,
    ReasoningOutput,
    ValidationResult,
    VisualEvent,
)


def build_delivery_snapshot(
    duration_s: float,
    valid_tracking_pct: float,
    audio_metrics: AudioMetrics,
    visual_events: list[VisualEvent],
) -> dict:
    return {
        "response_duration_s": round(duration_s, 1),
        "valid_tracking_pct": round(valid_tracking_pct, 1),
        "speaking_rate_wpm": audio_metrics.words_per_minute,
        "filler_words": audio_metrics.filler_word_count,
        "long_pauses": audio_metrics.long_pause_count,
        "detected_signals": len(visual_events),
    }


def build_practice_recommendation(
    audio_metrics: AudioMetrics, visual_events: list[VisualEvent],
) -> str:
    """TODO(Person D): replace with a richer, personalized recommendation
    (e.g. pick the single highest-impact issue and suggest a targeted
    micro-exercise). Placeholder picks the most obviously actionable issue."""
    if audio_metrics.filler_word_count >= 3:
        return "Practice pausing silently instead of using filler words."
    if visual_events:
        top = max(visual_events, key=lambda e: e.confidence)
        return (
            f"Re-record the segment between {top.start_time_s:.0f}s and "
            f"{top.end_time_s:.0f}s, focusing on reducing "
            f"{top.signal_type.value.replace('_', ' ')}."
        )
    return "Solid delivery overall — keep practicing under time pressure."


def build_coaching_report(
    duration_s: float,
    valid_tracking_pct: float,
    audio_metrics: AudioMetrics,
    visual_events: list[VisualEvent],
    reasoning: ReasoningOutput,
    validation: ValidationResult,
) -> CoachingReport:
    snapshot = build_delivery_snapshot(duration_s, valid_tracking_pct, audio_metrics, visual_events)

    timeline = [
        {"time_s": e.start_time_s, "label": e.signal_type.value}
        for e in visual_events
    ] + [
        {"time_s": start, "label": "long_pause"}
        for start, _end in audio_metrics.long_pause_timestamps
    ]
    timeline.sort(key=lambda x: x["time_s"])

    strengths = reasoning.observations[:3] if validation.passed else []
    improvements = reasoning.suggestions[:3] if validation.passed else [
        "Reasoning output failed validation — see failed_checks for details."
    ]

    return CoachingReport(
        duration_s=snapshot["response_duration_s"],
        valid_tracking_pct=snapshot["valid_tracking_pct"],
        speaking_rate_wpm=snapshot["speaking_rate_wpm"],
        filler_word_count=snapshot["filler_words"],
        long_pause_count=snapshot["long_pauses"],
        detected_signals=snapshot["detected_signals"],
        strengths=strengths,
        improvements=improvements,
        timeline=timeline,
        reliability_score=validation.reliability_score,
    )
