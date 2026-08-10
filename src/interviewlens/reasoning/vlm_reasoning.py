"""5. VISION-LANGUAGE MODEL (evidence-grounded reasoning) — Person C.

Wraps a VLM (default: Qwen2.5-VL-3B-Instruct) with a strict prompt template
that forces evidence-grounded, structured JSON output: observations,
explanations, suggestions. Never let the model free-write prose here —
downstream evidence validation (6.) depends on the JSON schema.
"""
from __future__ import annotations

import json
import logging
import re

from interviewlens.common.schemas import EvidencePackage, ReasoningOutput

logger = logging.getLogger(__name__)

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
    """Wraps Qwen2.5-VL-3B-Instruct for multimodal interview coaching.

    Model loading is attempted at construction time and falls back silently
    to mock reasoning when transformers/GPU are unavailable, so the rest of
    the pipeline is never blocked by VLM hardware requirements.
    """

    def __init__(
        self,
        model_name: str = "Qwen2.5-VL-3B-Instruct",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._model = None
        self._processor = None
        self._device = "cpu"
        self._load_model()

    def _load_model(self) -> None:
        """Load Qwen2.5-VL via transformers.  Logs a warning and leaves
        self._model = None if the import or weight download fails."""
        try:
            import torch
            from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Loading %s on %s …", self.model_name, self._device)

            dtype = torch.float16 if self._device == "cuda" else torch.float32
            self._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                device_map="auto" if self._device == "cuda" else None,
            )
            self._processor = AutoProcessor.from_pretrained(self.model_name)

            if self._device == "cpu":
                self._model = self._model.to(self._device)

            logger.info("VLM loaded successfully.")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not load VLM (%s). Falling back to mock reasoning.", exc
            )
            self._model = None
            self._processor = None

    def reason(self, evidence: EvidencePackage) -> ReasoningOutput:
        if self._model is not None and evidence.frame_images:
            raw = self._run_inference(evidence)
        else:
            if self._model is not None and not evidence.frame_images:
                logger.warning(
                    "VLM loaded but no frame images in EvidencePackage — "
                    "falling back to mock reasoning."
                )
            raw = _mock_reasoning(evidence)

        return ReasoningOutput(
            observations=raw["observations"],
            explanations=raw["explanations"],
            suggestions=raw["suggestions"],
            raw_json=raw,
        )

    def _run_inference(self, evidence: EvidencePackage) -> dict:
        """Run a forward pass through Qwen2.5-VL with frame images + text."""
        import torch

        prompt = build_prompt(evidence)

        # Build the multimodal chat message: one image entry per frame, then text.
        image_content = [
            {"type": "image", "image": img} for img in evidence.frame_images
        ]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [*image_content, {"type": "text", "text": prompt}],
            },
        ]

        text = self._processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._processor(
            text=[text],
            images=evidence.frame_images,
            return_tensors="pt",
        ).to(self._device)

        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=self.temperature > 0,
            )

        # Slice off the prompt tokens so we only decode the generated part.
        generated_ids = [
            out[len(inp):]
            for inp, out in zip(inputs.input_ids, output_ids)
        ]
        response = self._processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]

        return _parse_json_response(response, evidence)


def _parse_json_response(response: str, evidence: EvidencePackage) -> dict:
    """Extract the JSON block from the VLM's raw text output.

    Handles markdown code fences (```json ... ```) that some checkpoints
    emit. Falls back to mock reasoning on any parse error.
    """
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", response).strip()
    try:
        parsed = json.loads(cleaned)
        return {
            "observations": list(parsed.get("observations", [])),
            "explanations": list(parsed.get("explanations", [])),
            "suggestions":  list(parsed.get("suggestions", [])),
        }
    except (json.JSONDecodeError, AttributeError):
        logger.warning("VLM returned non-JSON output; falling back to mock.")
        return _mock_reasoning(evidence)


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
