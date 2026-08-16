"""5. LLM REASONING (evidence-grounded reasoning) — Person C.

Wraps an Ollama-hosted LLM (default: nvidia/nemotron-mini-4b-instruct via the
"nemotron-mini" Ollama tag) with a strict prompt template that forces
evidence-grounded, structured JSON output: observations, explanations,
suggestions.  Never let the model free-write prose here — downstream evidence
validation (6.) depends on the JSON schema.

Prerequisites:
    pip install ollama
    ollama pull nemotron-mini   # downloads ~2.7 GB once

Ollama must be running locally (ollama serve) before the reasoner is called.
When the ollama package is missing or the server is unreachable, the reasoner
falls back to deterministic mock output so the rest of the pipeline is
never blocked.
"""
from __future__ import annotations

import json
import logging
import re

from interviewlens.common.schemas import EvidencePackage, ReasoningOutput, SignalType

logger = logging.getLogger(__name__)

# Closed vocabulary the LLM is allowed to talk about, generated from the enum so it can
# never drift out of sync with what evidence_validation.py's ALLOWED_KEYWORDS actually
# accepts. Interpolated into SYSTEM_PROMPT below.
_SIGNAL_VOCAB = ", ".join(s.value for s in SignalType)
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

COACHING INTENSITY SCALES WITH THE EVIDENCE: the prompt below includes a signal summary
with event counts and the percent of the clip flagged. Use it to calibrate how forceful
your suggestions are:
- Few, brief, low-recurrence signals (e.g. one event lasting under 2s, or under 15% of
  the clip flagged): light touch -- a short, encouraging note is enough.
- Several recurring signals, or 15-40% of the clip flagged: name the pattern explicitly
  (how many times, roughly how much of the clip) and give one concrete drill to fix it.
- Many signals, a high per-type event count, or over 40% of the clip flagged: this is a
  candidate who needs real help, not a pat on the back. For every such signal, state the
  frequency plainly and give a specific, practical exercise (e.g. "record yourself for
  60 seconds keeping both hands on the desk", "do 3 practice run-throughs timing your
  pauses"), not a vague platitude like "try to reduce this." Prioritize the highest-count
  or longest-duration signal first.
Never invent severity language for a signal that isn't in the evidence.

BASELINE COVERAGE -- NEVER return empty arrays. Even when this clip has few or no
flagged visual signals, you still have audio delivery metrics (words-per-minute,
filler-word count, long-pause count) and a transcript to work with, and the candidate
always deserves real feedback:
- Always include at least one "observations" entry about the speaking pace (state the
  actual wpm and whether it is inside/outside the 120-160 wpm target range) or the
  filler/pause counts -- use the literal "delivery: " prefix for this one instead of a
  visual signal token, since it isn't a visual signal.
- Always include at least one specific strength grounded only in the metrics/transcript
  you were given (e.g. "delivery: speaking pace was a steady 135 wpm, inside the target
  range" or "delivery: no filler words detected") -- never a generic line like "keep up
  the good work" with nothing underneath it.
- Always include at least one concrete, actionable suggestion, even for a clean clip
  (e.g. a specific thing to practice next, tied to whatever in the transcript or metrics
  has the most room to improve -- content structure, pacing, pause placement).
Do not pad with vague filler text ("nothing notable", "keep practicing") that isn't
tied to a specific number or event from the evidence above.

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
    #
    # Capped at MAX_COVERAGE_TYPES, prioritized by total flagged duration: a clip with
    # degraded pose tracking can spuriously trip a dozen-plus distinct rule types at
    # once (most of them borderline/low-signal), and demanding a correctly-formatted,
    # individually-prefixed observation for *every one* of them from a small local
    # model reliably produces several malformed/unprefixed entries -- each one fails
    # evidence_validation's category-grounding check and costs 0.15 reliability, so a
    # clip with enough distinct types was tanking the score to 0 regardless of how
    # sound any individual observation was. Covering the handful of most significant
    # signals well beats covering all of them badly.
    MAX_COVERAGE_TYPES = 6
    per_type_durations = (summary or {}).get("per_type", {})
    present_types = sorted({e["type"] for e in evidence.event_timestamps.get("visual_events", [])})
    if len(present_types) > MAX_COVERAGE_TYPES:
        present_types = sorted(
            present_types,
            key=lambda t: per_type_durations.get(t, {}).get("total_s", 0.0),
            reverse=True,
        )[:MAX_COVERAGE_TYPES]
    coverage_line = ""
    if present_types:
        coverage_line = (
            f"REQUIRED COVERAGE: at minimum, include one observation for EACH of these "
            f"signal types (the most significant ones in this clip): "
            f"{', '.join(present_types)}. You may mention other signal types from the "
            f"evidence too, but do not stop before covering all of the ones listed "
            f"here.\n\n"
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

    question_line = f"Question: {evidence.question}\n\n" if evidence.question else ""
    return (
        f"{question_line}"
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


class LLMReasoner:
    """Ollama LLM reasoner for interview coaching (local inference).

    Uses the Ollama Python client to call a locally-hosted LLM
    (default: nemotron-mini — NVIDIA Nemotron Mini 4B Instruct).
    All evidence is passed as structured text.

    Falls back to deterministic mock reasoning when the ollama package is
    not installed or the Ollama server is unreachable, so the pipeline
    always runs without a running server.
    """

    def __init__(
        self,
        model_name: str = "nemotron-mini",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None
        self._load_client()

    def _load_client(self) -> None:
        """Probe the Ollama server.  Leaves self._client = None when the
        ollama package is missing or the server is not reachable."""
        try:
            import ollama  # noqa: PLC0415
            client = ollama.Client()
            # A lightweight list-models call confirms the server is up.
            client.list()
            self._client = client
            logger.info("Ollama client ready (model=%s).", self.model_name)
        except ImportError:
            logger.warning(
                "ollama package not installed — falling back to mock reasoning. "
                "Run: pip install ollama"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Ollama server unreachable (%s) — falling back to mock reasoning. "
                "Start it with: ollama serve",
                exc,
            )

    def reason(self, evidence: EvidencePackage) -> ReasoningOutput:
        if self._client is not None:
            raw = self._run_inference(evidence)
        else:
            raw = _mock_reasoning(evidence)

        return ReasoningOutput(
            observations=raw["observations"],
            explanations=raw["explanations"],
            suggestions=raw["suggestions"],
            raw_json=raw,
        )

    def _run_inference(self, evidence: EvidencePackage) -> dict:
        """Call the Ollama chat endpoint with text-only evidence."""
        prompt = build_prompt(evidence)
        try:
            response = self._client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                format="json",
                options={
                    "num_predict": self.max_tokens,
                    "temperature": self.temperature,
                },
            )
            raw_text = response["message"]["content"] if isinstance(response, dict) else response.message.content
            return _parse_json_response(raw_text or "", evidence)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ollama call failed (%s) — falling back to mock.", exc)
            return _mock_reasoning(evidence)


def _coerce_str_list(value, field_name: str) -> list[str]:
    """Coerce a JSON value into list[str], tolerating models that occasionally nest an
    object per item (e.g. {"signal_type": "head_tilt", "text": "..."}) instead of a
    flat string -- observed in real Qwen2.5-VL-3B-Instruct output once REQUIRED
    COVERAGE started asking it to enumerate several signal types at once. Silently
    trusting the shape here used to crash validate() downstream with
    AttributeError: 'dict' object has no attribute 'lower'.

    JSON `null` entries and empty strings are dropped rather than stringified --
    small local models (nemotron-mini) occasionally pad these arrays with nulls
    to hit a perceived length, and str(None) used to leak the literal text
    "None" into the UI as a repeated card for every null entry."""
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if item is None:
            continue
        if isinstance(item, str):
            text = item.strip()
            if text:
                out.append(text)
        elif isinstance(item, dict):
            logger.warning("LLM returned a dict instead of a string in %r: %r — coercing.", field_name, item)
            text = " ".join(str(v) for v in item.values() if v is not None).strip()
            if text:
                out.append(text)
        else:
            logger.warning("LLM returned an unexpected %s in %r: %r — coercing.", type(item).__name__, field_name, item)
            text = str(item).strip()
            if text:
                out.append(text)
    return out


def _parse_json_response(response: str, evidence: EvidencePackage) -> dict:
    """Extract the JSON block from the LLM's raw text output.

    Handles markdown code fences (```json ... ```) that some models
    emit. Falls back to mock reasoning on any parse error.
    """
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", response).strip()
    try:
        parsed = json.loads(cleaned)
        result = {
            "observations": _coerce_str_list(parsed.get("observations", []), "observations"),
            "explanations": _coerce_str_list(parsed.get("explanations", []), "explanations"),
            "suggestions":  _coerce_str_list(parsed.get("suggestions", []), "suggestions"),
        }
    except (json.JSONDecodeError, AttributeError):
        logger.warning("LLM returned non-JSON output; falling back to mock.")
        return _mock_reasoning(evidence)

    # A small local model can return syntactically valid JSON that is still useless --
    # empty (or near-empty) arrays despite there being real transcript/audio evidence to
    # comment on. That produced a coaching report with nothing but generic placeholder
    # text ("Nothing notable detected" / "Keep up the steady delivery") for every clip.
    # Deterministic mock reasoning is always evidence-grounded (see _mock_reasoning), so
    # use it to fill in whichever fields the model left empty instead of showing nothing.
    if not result["observations"] or not result["suggestions"]:
        logger.warning(
            "LLM returned thin output (observations=%d, suggestions=%d) — "
            "backfilling with deterministic evidence-grounded reasoning.",
            len(result["observations"]), len(result["suggestions"]),
        )
        mock = _mock_reasoning(evidence)
        for key in ("observations", "explanations", "suggestions"):
            if not result[key]:
                result[key] = mock[key]
    return result


def _mock_reasoning(evidence: EvidencePackage) -> dict:
    """Deterministic, evidence-grounded placeholder used when Ollama is
    unavailable. Scales how forceful the suggestions are with how much
    evidence there is, same principle as the live-LLM prompt's "coaching
    intensity" rule -- one stray event gets a light note, a recurring
    pattern gets a named frequency and a concrete drill."""
    observations: list[str] = []
    explanations: list[str] = []
    suggestions: list[str] = []

    # Always ground at least one observation/suggestion in the delivery metrics --
    # these exist for every clip with any speech at all, unlike visual_events, so this
    # is what keeps a clean clip (no flagged body-language/background signals) from
    # producing a report with nothing in it but generic placeholder text.
    wpm = evidence.audio_metrics.words_per_minute
    if wpm > 0:
        in_range = 120 <= wpm <= 160
        observations.append(
            f"delivery: speaking pace was {wpm:.0f} wpm "
            f"({'inside' if in_range else 'outside'} the 120-160 wpm target range)."
        )
        explanations.append(
            f"Speaking at {wpm:.0f} wpm, inside the target range, reads as confident "
            f"and is easy for an interviewer to follow."
            if in_range else
            f"Speaking at {wpm:.0f} wpm, outside the target range, can make an answer "
            f"feel rushed or dragging, which affects delivery confidence."
        )
        if in_range:
            suggestions.append(f"Pace ({wpm:.0f} wpm) is solid -- keep this pace in future answers.")
        else:
            direction = "slow down" if wpm > 160 else "add more energy/pace"
            suggestions.append(
                f"Pace was {wpm:.0f} wpm, {'above' if wpm > 160 else 'below'} the "
                f"120-160 wpm target -- practice a few timed run-throughs to {direction}."
            )

    if evidence.audio_metrics.filler_word_count > 0:
        n = evidence.audio_metrics.filler_word_count
        observations.append(f"{n} filler words detected.")
        explanations.append("Frequent filler words can reduce perceived confidence.")
        if n >= 5:
            suggestions.append(
                f"{n} filler words is enough to be noticeable -- practice pausing "
                "silently instead, and try 2-3 timed run-throughs of this answer "
                "counting your fillers out loud afterward."
            )
        else:
            suggestions.append("Pause silently instead of using filler words.")

    counts: dict[str, int] = {}
    total_dur: dict[str, float] = {}
    for event in evidence.visual_events:
        counts[event.signal_type] = counts.get(event.signal_type, 0) + 1
        total_dur[event.signal_type] = (
            total_dur.get(event.signal_type, 0.0) + (event.end_time_s - event.start_time_s)
        )

    for signal_type, n in sorted(counts.items(), key=lambda kv: total_dur[kv[0]], reverse=True):
        label = signal_type.value.replace("_", " ")
        dur = total_dur[signal_type]
        if n >= 3 or dur >= 10.0:
            suggestions.append(
                f"{label.capitalize()} showed up {n} times ({dur:.0f}s total) -- this is a "
                f"pattern, not a one-off. Record a one-minute practice answer focused only on "
                f"eliminating {label}, then compare it to this clip."
            )
        else:
            suggestions.append(f"Try to reduce {label}.")
        observations.append(
            f"{label.capitalize()} detected {n} time(s), {dur:.1f}s total."
        )

    if not observations:
        observations.append("No significant distracting signals detected.")

    return {
        "observations": observations,
        "explanations": explanations or ["No signal-level issues detected in this clip."],
        "suggestions": suggestions or ["Keep up the steady delivery."],
    }
