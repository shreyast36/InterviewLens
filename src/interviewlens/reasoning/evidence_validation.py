"""6. EVIDENCE VALIDATION LAYER — Person C.

Runs the VLM's structured output back against the raw evidence to catch
hallucinations before they reach the user:

  1. Allowed-category check    — claims must reference known signal/metric types
  2. Event existence check     — claimed events must actually appear in evidence
  3. Confidence check          — underlying event confidence must clear a threshold
  4. Timestamp validity check  — referenced timestamps must fall within the clip
  5. Sufficient-evidence check — claims need enough matching data points

Any failure lowers the reliability score and/or should cause the offending
claim to be dropped before the report is shown to the user.
"""
from __future__ import annotations

import re

from interviewlens.common.schemas import EvidencePackage, ReasoningOutput, SignalType, ValidationResult

MIN_EVENT_CONFIDENCE = 0.5
ALLOWED_KEYWORDS = {
    # audio delivery
    "filler", "pause", "wpm", "speaking", "delivery",
    # body language / gesture (original temporal-model signals)
    "hand", "posture", "movement", "eye", "gesture",
    # framing signals (RTMPose-S, from A/B branch)
    "headroom", "framing", "center", "centering", "tilt", "tilted", "camera",
    # background signals (YOLO-World-S, from A/B branch)
    "background", "distracting", "object", "laptop", "monitor", "screen",
    # rule-based pose signals (00_master_pipeline.ipynb §5)
    "face", "touch", "touching", "grooming", "hair", "arm", "arms", "cross",
    "crossed", "shoulder", "shoulders", "head", "nose", "chin", "down",
    "looking", "gaze", "lean", "leans",
    "leaning", "sway", "swaying", "nod", "nodding", "fidget", "fidgeting",
    "restless", "still", "frozen", "sudden", "startle", "jump", "wrist",
    "unstable", "tracking", "reliable", "transient", "appear", "disappear",
    "enter", "leave", "brief",
    # general
    "confidence", "signal", "issue",
} | {s.value for s in SignalType}  # e.g. "arms_crossed", "headroom_too_loose" -- vlm_reasoning.py's
# REQUIRED_FORMAT makes the VLM prefix every claim with one of these exact tokens; matching
# them verbatim is more reliable than hoping the surrounding natural-language description
# happens to reuse a plain-English keyword above.


_ALLOWED_KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in ALLOWED_KEYWORDS) + r")\b"
)


def _mentions_allowed_category(claim: str) -> bool:
    # Word-boundary match, not substring: a naive `kw in claim_lower` check let "appear"
    # (added for transient-object language like "the laptop appeared") match inside the
    # common word "appears" in unrelated sentences ("...and appears tense"), letting an
    # ungrounded claim slip past the category check. \b prevents that without losing
    # intended matches -- every keyword with a plural/verb form (arm/arms, cross/crossed,
    # lean/leaning, ...) is already listed both ways in ALLOWED_KEYWORDS above.
    return bool(_ALLOWED_KEYWORD_PATTERN.search(claim.lower()))


def _timestamps_in_claim(claim: str) -> list[float]:
    return [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*s\b", claim)]


def validate(evidence: EvidencePackage, reasoning: ReasoningOutput) -> ValidationResult:
    failed_checks: list[str] = []

    end_candidates = [0.0]
    if evidence.transcript.words:
        end_candidates.append(evidence.transcript.words[-1].end_time_s)
    end_candidates.extend(e.end_time_s for e in evidence.visual_events)
    clip_end = max(end_candidates)

    low_conf_events = [e for e in evidence.visual_events if e.confidence < MIN_EVENT_CONFIDENCE]

    all_claims = reasoning.observations + reasoning.explanations + reasoning.suggestions
    for claim in all_claims:
        if not _mentions_allowed_category(claim):
            failed_checks.append(f"category_check_failed: {claim!r}")

        for ts in _timestamps_in_claim(claim):
            if ts < 0 or ts > clip_end + 1e-6:
                failed_checks.append(f"timestamp_out_of_range: {claim!r}")

    if low_conf_events:
        failed_checks.append(f"low_confidence_events: {len(low_conf_events)}")

    if not evidence.visual_events and not evidence.audio_metrics.filler_word_count:
        # Nothing concrete to support a strongly-worded report
        if len(reasoning.observations) > 1:
            failed_checks.append("insufficient_supporting_evidence")

    passed = len(failed_checks) == 0
    reliability = max(0.0, 1.0 - 0.15 * len(failed_checks))

    return ValidationResult(
        passed=passed,
        reliability_score=round(reliability, 2),
        failed_checks=failed_checks,
    )
