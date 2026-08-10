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

from interviewlens.common.schemas import EvidencePackage, ReasoningOutput, SignalType

logger = logging.getLogger(__name__)

# Closed vocabulary the VLM is allowed to talk about, generated from the enum so it can
# never drift out of sync with what evidence_validation.py's ALLOWED_KEYWORDS actually
# accepts. Interpolated into SYSTEM_PROMPT below.
_SIGNAL_VOCAB = ", ".join(s.value for s in SignalType)

# The frame images are attached for the VLM to judge *severity/timing* of the listed
# events -- not as a general scene to caption. A 3B model given real photos will default
# to describing whatever is visually salient (clothing, food, decor) unless explicitly
# told not to; earlier testing against a real Qwen2.5-VL-3B run produced observations
# like "wearing a white towel" / "sandwich and coffee on the counter" that referenced
# nothing in the evidence and were correctly rejected by evidence_validation.py (0.25
# reliability, category_check_failed on 5/6 claims).
#
# A first fix attempt added a worked "GOOD vs BAD" example sentence pair to this prompt.
# That made things worse, not better: Qwen2.5-VL-3B just echoed the example verbatim as
# its actual output (word-for-word, including the sentence explicitly labeled BAD) instead
# of reasoning about this clip's real evidence -- a known small-model failure mode where a
# complete, well-formed example in context gets copied rather than used as a pattern. The
# REQUIRED_FORMAT rule below replaces that: it forces every claim to start with one of the
# dynamically-listed real signal names, which cannot be satisfied by copying a static
# example, only by actually reading the evidence for this clip.
SYSTEM_PROMPT = f"""You are an interview-coaching assistant. You are given
timestamped visual events, audio delivery metrics, and a transcript from a single
interview answer, plus a few sample video frames.

The frames are ONLY there to help you judge the severity and timing of the events
listed in the evidence below -- they are NOT a scene to describe. You MUST NOT mention
the person's appearance, clothing, hairstyle, facial features, food, drink, furniture,
or any object/detail visible in the frames that is not explicitly named in the evidence
text you are given. If nothing in the evidence supports a comment, do not make it.

REQUIRED FORMAT: every string in "observations" must start with "<signal_type>: " using
one of these exact tokens (choose only ones that actually appear in the evidence given to
you for THIS clip -- do not use a token just because it's in this list):
{_SIGNAL_VOCAB}

REQUIRED COVERAGE: the evidence you are given below will tell you exactly which signal
types are present in this clip. You must produce one observation for every one of them,
not just the first one or two -- do not stop early.

LIGHTING SUGGESTIONS: if low_light, overexposed, or backlit_face is among the signals
present, your "suggestions" entry for it must include a concrete fix, not a vague
comment: for low_light, add or move toward a light source in front of you; for
overexposed, reduce or diffuse the light source that is too strong; for backlit_face,
the light behind you (e.g. a window) is brighter than your face -- turn to face that
light source instead, or add a light in front of you to balance it.

AUDIO SUGGESTIONS: if low_mic_level or intermittent_audio is among the signals present,
your "suggestions" entry for it must include a concrete fix: for low_mic_level, move
closer to the microphone or increase input gain; for intermittent_audio, check the
network/microphone connection and consider a wired connection instead of wifi/bluetooth.

Return STRICT JSON with this shape:
{{
  "observations": ["<signal_type>: what happened and when, using only the evidence given"],
  "explanations": ["why that matters for the interview, tied to the same signal_type"],
  "suggestions": ["a concrete suggestion tied to the same signal_type"]
}}
"""


def build_prompt(evidence: EvidencePackage) -> str:
    framing    = evidence.event_timestamps.get("framing_summary", [])
    background = evidence.event_timestamps.get("background_objects", [])
    summary    = evidence.event_timestamps.get("signal_summary")

    # Force full coverage: list the *actual* distinct signal types present for this
    # clip (not the whole static vocabulary -- most won't apply to any given video)
    # and require one observation per type. Without this, a model will happily stop
    # after 1-2 signals even when several are present (seen in testing: a clip with
    # 7 distinct flagged signal types got only 2 covered).
    present_types = sorted({e["type"] for e in evidence.event_timestamps.get("visual_events", [])})
    coverage_line = ""
    if present_types:
        coverage_line = (
            f"REQUIRED COVERAGE: this clip's evidence contains these signal types: "
            f"{', '.join(present_types)}. You MUST include at least one observation "
            f"for EACH one listed here -- do not stop after covering only some of "
            f"them.\n\n"
        )

    summary_line = ""
    if summary:
        counts = ", ".join(
            f"{sig_type} x{s['events']} ({s['total_s']}s total)"
            for sig_type, s in summary.get("per_type", {}).items()
        )
        summary_line = (
            f"Signal summary: {counts or 'no recurring signals'}. "
            f"{summary.get('pct_timestamps_flagged', 0)}% of the clip has at least one flag. "
            f"Longest clean streak: {summary.get('longest_clean_streak_s', 0)}s.\n\n"
        )

    return (
        f"Question: {evidence.question}\n\n"
        f"Transcript: {evidence.transcript.text}\n\n"
        f"Audio metrics: wpm={evidence.audio_metrics.words_per_minute}, "
        f"fillers={evidence.audio_metrics.filler_word_count}, "
        f"long_pauses={evidence.audio_metrics.long_pause_count}\n\n"
        f"{summary_line}"
        f"{coverage_line}"
        f"Visual events (each already merged into one span per continuous "
        f"occurrence — do not treat repeated entries as separate incidents): "
        f"{evidence.event_timestamps.get('visual_events', [])}\n\n"
        f"Framing issues (headroom_pct, centering_offset, roll_deg): "
        f"{framing if framing else 'none detected'}\n\n"
        f"Background objects (tier='distracting': persistent; "
        f"tier='transient': entered/left mid-clip): "
        f"{background if background else 'none detected'}\n\n"
        f"Selected frame indices: {evidence.selected_frames}\n\n"
        f"Reminder: only comment on the events/metrics listed above, by their exact "
        f"names. Do not describe appearance, clothing, food, drink, or surroundings "
        f"visible in the attached frames unless they appear in the evidence text above."
        + (f"\n\nYou still need one observation for each of: {', '.join(present_types)}."
           if present_types else "")
    )


class VLMReasoner:
    """Wraps Qwen2.5-VL-3B-Instruct for multimodal interview coaching.

    Model loading is attempted at construction time and falls back silently
    to mock reasoning when transformers/GPU are unavailable, so the rest of
    the pipeline is never blocked by VLM hardware requirements.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-VL-3B-Instruct",
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
                device_map="auto" if self._device == "cuda" else None
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


def _coerce_str_list(value, field_name: str) -> list[str]:
    """Coerce a JSON value into list[str], tolerating models that occasionally nest an
    object per item (e.g. {"signal_type": "head_tilt", "text": "..."}) instead of a
    flat string -- observed in real Qwen2.5-VL-3B-Instruct output once REQUIRED
    COVERAGE started asking it to enumerate several signal types at once. Silently
    trusting the shape here used to crash validate() downstream with
    AttributeError: 'dict' object has no attribute 'lower'."""
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            logger.warning("VLM returned a dict instead of a string in %r: %r — coercing.", field_name, item)
            out.append(" ".join(str(v) for v in item.values()))
        else:
            logger.warning("VLM returned an unexpected %s in %r: %r — coercing.", type(item).__name__, field_name, item)
            out.append(str(item))
    return out


def _parse_json_response(response: str, evidence: EvidencePackage) -> dict:
    """Extract the JSON block from the VLM's raw text output.

    Handles markdown code fences (```json ... ```) that some checkpoints
    emit. Falls back to mock reasoning on any parse error.
    """
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", response).strip()
    try:
        parsed = json.loads(cleaned)
        return {
            "observations": _coerce_str_list(parsed.get("observations", []), "observations"),
            "explanations": _coerce_str_list(parsed.get("explanations", []), "explanations"),
            "suggestions":  _coerce_str_list(parsed.get("suggestions", []), "suggestions"),
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
