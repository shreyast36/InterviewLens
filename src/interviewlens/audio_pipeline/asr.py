"""3.2 SPEECH RECOGNITION — Person B.

Champion model: Whisper-small (faster-whisper, real inference)
Challenger model: Wav2Vec 2.0 (not wired up yet)

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
    """Champion. Real speech-to-text via faster-whisper on the interview
    response's actual audio track."""

    _MODEL_SIZE = "small"

    def __init__(self, model_path: str | None = None, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel  # noqa: PLC0415
            except ImportError as exc:
                raise RuntimeError(
                    "faster-whisper is required for transcription. "
                    "Install it with: uv pip install faster-whisper"
                ) from exc
            compute_type = "int8" if self.device == "cpu" else "float16"
            self._model = WhisperModel(
                self.model_path or self._MODEL_SIZE,
                device=self.device,
                compute_type=compute_type,
            )
        return self._model

    def transcribe(self, segment: SpeechSegment) -> Transcript:
        model = self._get_model()
        segments, _info = model.transcribe(
            segment.audio, language="en", word_timestamps=True,
        )
        words: list[WordTiming] = []
        text_parts: list[str] = []
        for seg in segments:
            seg_text = seg.text.strip()
            if seg_text:
                text_parts.append(seg_text)
            for w in seg.words or []:
                words.append(WordTiming(
                    word=w.word.strip(),
                    start_time_s=segment.start_time_s + w.start,
                    end_time_s=segment.start_time_s + w.end,
                    confidence=float(w.probability),
                ))
        return Transcript(text=" ".join(text_parts), words=words)


class Wav2Vec2ASR(ASRModel):
    """Challenger. TODO(Person B): load facebook/wav2vec2-base-960h or similar."""

    def __init__(self, model_path: str | None = None, device: str = "cpu"):
        self.model_path = model_path
        self.device = device

    def transcribe(self, segment: SpeechSegment) -> Transcript:
        raise NotImplementedError(
            "Wav2Vec2 challenger ASR is not wired up. "
            "Use asr_model='whisper-small' (champion) instead."
        )


def build_asr_model(model_name: str) -> ASRModel:
    if model_name in ("whisper-small", "champion"):
        return WhisperSmallASR()
    if model_name in ("wav2vec2.0", "wav2vec2", "challenger"):
        return Wav2Vec2ASR()
    raise ValueError(f"Unknown asr_model: {model_name}")
