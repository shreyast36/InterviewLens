"""7. COACHING REPORT (post-response) — Person D (Platform/Product Engineer).

Combines everything upstream (audio metrics, visual events, LLM reasoning,
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

    # Carries both start_s and end_s (not just a point-in-time) so the Gantt chart can
    # draw each event's real span instead of reconstructing it by guessing where the
    # next differently-labeled point happens to fall -- that guess breaks as soon as two
    # signal types overlap in time, which they routinely do (e.g. hand_to_face during a
    # long_pause).
    timeline = [
        {"start_s": e.start_time_s, "end_s": e.end_time_s, "label": e.signal_type.value}
        for e in visual_events
    ] + [
        {"start_s": start, "end_s": end, "label": "long_pause"}
        for start, end in audio_metrics.long_pause_timestamps
    ]
    timeline.sort(key=lambda x: x["start_s"])

    # Always show the coaching content — reliability_score communicates how much
    # to trust it.  Only fall back to an error message when reliability is very
    # low (< 0.3), indicating serious hallucination risk.
    MIN_SHOW_RELIABILITY = 0.3
    if validation.reliability_score >= MIN_SHOW_RELIABILITY:
        strengths    = reasoning.observations[:3]
        improvements = reasoning.suggestions[:3] or ["Keep up the steady delivery."]
    else:
        strengths    = []
        improvements = ["Reasoning output could not be verified — see failed_checks for details."]

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
