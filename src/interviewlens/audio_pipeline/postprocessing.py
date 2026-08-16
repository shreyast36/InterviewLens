"""3.3 AUDIO POST-PROCESSING — Person B.

Cleans up raw ASR output: word-level alignment refinement, disfluency
normalization, filler-word tagging, and pause detection between words.
"""
from __future__ import annotations

from interviewlens.common.schemas import Transcript, WordTiming

FILLER_WORDS = {"um", "uh", "like", "you know", "so", "actually", "basically"}
LONG_PAUSE_THRESHOLD_S = 1.0


def identify_filler_words(transcript: Transcript) -> list[WordTiming]:
    return [w for w in transcript.words if w.word.lower().strip(",.") in FILLER_WORDS]


def detect_pauses(
    transcript: Transcript, threshold_s: float = LONG_PAUSE_THRESHOLD_S,
) -> list[tuple[float, float]]:
    """Returns list of (start, end) gaps between consecutive words >= threshold."""
    pauses = []
    words = transcript.words
    for a, b in zip(words, words[1:]):
        gap = b.start_time_s - a.end_time_s
        if gap >= threshold_s:
            pauses.append((a.end_time_s, b.start_time_s))
    return pauses


def normalize_disfluencies(transcript: Transcript) -> Transcript:
    """TODO(Person B): replace with a real disfluency-removal model
    (e.g. a fine-tuned seq2seq or rule-based grammar). Placeholder strips
    filler words from the display text but keeps them in `words` for
    delivery-analytics scoring.

    Filters filler tokens out of `transcript.text` directly rather than
    rebuilding it by joining `transcript.words` -- faster-whisper occasionally
    returns segment-level text without matching word-level timestamps (an
    empty/partial `words` list for that segment), and reconstructing the display
    text purely from `words` silently dropped those segments entirely, which is
    what was producing incomplete transcripts even though the un-normalized
    `transcript.text` (built by joining every segment's `seg.text`) had the
    full content."""
    clean_tokens = [
        token for token in transcript.text.split()
        if token.lower().strip(",.") not in FILLER_WORDS
    ]
    return Transcript(text=" ".join(clean_tokens), words=transcript.words)
