"""3.2 SPEECH RECOGNITION — Person B.

Champion model: Whisper-small
Challenger model: Wav2Vec 2.0

Both implementations expose `ASRModel.transcribe(segment) -> Transcript`
(with word-level timestamps) so downstream post-processing never has to
know which backend produced the text.
"""
from __future__ import annotations

import abc

from interviewlens.audio_pipeline.preprocessing import SpeechSegment
from interviewlens.common.schemas import Transcript, WordTiming


class ASRModel(abc.ABC):
    @abc.abstractmethod
    def transcribe(self, segment: SpeechSegment) -> Transcript:
        ...


class WhisperSmallASR(ASRModel):
    """Champion. TODO(Person B): load faster-whisper / openai-whisper 'small'."""

    def __init__(self, model_path: str | None = None, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self._model = None

    def transcribe(self, segment: SpeechSegment) -> Transcript:
        if self._model is None:
            return _mock_transcript(segment)
        raise NotImplementedError("Wire up real Whisper-small inference here")


class Wav2Vec2ASR(ASRModel):
    """Challenger. TODO(Person B): load facebook/wav2vec2-base-960h or similar."""

    def __init__(self, model_path: str | None = None, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self._model = None

    def transcribe(self, segment: SpeechSegment) -> Transcript:
        if self._model is None:
            return _mock_transcript(segment)
        raise NotImplementedError("Wire up real Wav2Vec2 inference here")


def build_asr_model(model_name: str) -> ASRModel:
    if model_name in ("whisper-small", "champion"):
        return WhisperSmallASR()
    if model_name in ("wav2vec2.0", "wav2vec2", "challenger"):
        return Wav2Vec2ASR()
    raise ValueError(f"Unknown asr_model: {model_name}")


_MOCK_SENTENCE = "I worked on a project where we had to".split()


def _mock_transcript(segment: SpeechSegment) -> Transcript:
    """Evenly spaces mock words across the segment's duration so the rest
    of the pipeline (word-level alignment, filler detection, WPM) has
    something realistic to operate on before real ASR is wired in."""
    duration = segment.end_time_s - segment.start_time_s
    n = len(_MOCK_SENTENCE)
    step = duration / max(n, 1)
    words = [
        WordTiming(
            word=w,
            start_time_s=segment.start_time_s + i * step,
            end_time_s=segment.start_time_s + (i + 1) * step,
            confidence=0.9,
        )
        for i, w in enumerate(_MOCK_SENTENCE)
    ]
    return Transcript(text=" ".join(_MOCK_SENTENCE), words=words)
