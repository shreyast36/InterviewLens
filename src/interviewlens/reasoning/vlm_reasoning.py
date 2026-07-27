"""5. VISION-LANGUAGE MODEL (evidence-grounded reasoning) — Person C.

Wraps a VLM (default: Qwen2.5-VL-3B-Instruct) with a strict prompt template
that forces evidence-grounded, structured JSON output: observations,
explanations, suggestions. Never let the model free-write prose here —
downstream evidence validation (6.) depends on the JSON schema.
"""
from __future__ import annotations

from interviewlens.common.schemas import EvidencePackage, ReasoningOutput

SYSTEM_PROMPT = """You are an interview-coaching assistant. You are given
timestamped visual events, audio delivery metrics, and a transcript from a
single interview answer. You must ONLY comment on things directly supported
by the evidence provided — never invent behavior you were not given.

Return STRICT JSON with this shape:
{
  "observations": ["..."],
  "explanations": ["..."],
  "suggestions": ["..."]
}
"""


def build_prompt(evidence: EvidencePackage) -> str:
    return (
        f"Question: {evidence.question}\n\n"
        f"Transcript: {evidence.transcript.text}\n\n"
        f"Audio metrics: wpm={evidence.audio_metrics.words_per_minute}, "
        f"fillers={evidence.audio_metrics.filler_word_count}, "
        f"long_pauses={evidence.audio_metrics.long_pause_count}\n\n"
        f"Visual events: {evidence.event_timestamps.get('visual_events', [])}\n\n"
        f"Selected frame indices: {evidence.selected_frames}\n"
    )


class VLMReasoner:
    """TODO(Person C): load Qwen2.5-VL-3B-Instruct (or similar) via
    transformers/vLLM and pass `evidence.selected_frames` images + the
    prompt built by `build_prompt`. Keep `reason()`'s return type stable."""

    def __init__(
        self,
        model_name: str = "Qwen2.5-VL-3B-Instruct",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._model = None  # TODO: load real model/pipeline

    def reason(self, evidence: EvidencePackage) -> ReasoningOutput:
        build_prompt(evidence)  # TODO(Person C): feed this + images to the real VLM
        if self._model is None:
            raw = _mock_reasoning(evidence)
        else:
            raise NotImplementedError("Wire up real VLM inference here")

        return ReasoningOutput(
            observations=raw["observations"],
            explanations=raw["explanations"],
            suggestions=raw["suggestions"],
            raw_json=raw,
        )


def _mock_reasoning(evidence: EvidencePackage) -> dict:
    """Deterministic, evidence-grounded placeholder so Person D can build
    the coaching report before the real VLM is wired in."""
    observations: list[str] = []
    explanations: list[str] = []
    suggestions: list[str] = []

    if evidence.audio_metrics.filler_word_count > 0:
        observations.append(
            f"{evidence.audio_metrics.filler_word_count} filler words detected."
        )
        explanations.append("Frequent filler words can reduce perceived confidence.")
        suggestions.append("Pause silently instead of using filler words.")

    for event in evidence.visual_events:
        observations.append(
            f"{event.signal_type.value.replace('_', ' ').title()} detected "
            f"between {event.start_time_s:.1f}s and {event.end_time_s:.1f}s."
        )
        suggestions.append(f"Try to reduce {event.signal_type.value.replace('_', ' ')}.")

    if not observations:
        observations.append("No significant distracting signals detected.")

    return {
        "observations": observations,
        "explanations": explanations or ["No issues strong enough to explain."],
        "suggestions": suggestions or ["Keep up the steady delivery."],
    }
