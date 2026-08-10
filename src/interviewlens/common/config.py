"""Central configuration loader — keep all tunable knobs here so the four
subsystems don't hardcode magic numbers in their own modules.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import yaml


@dataclass
class VideoConfig:
    fps: int = 30
    resolution: tuple[int, int] = (1280, 720)
    pose_model: str = "rtmpose-s"       # champion; "simplebaseline" = challenger
    window_seconds: int = 4
    stride_seconds: int = 1


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    asr_model: str = "whisper-small"    # champion; "wav2vec2.0" = challenger


@dataclass
class ReasoningConfig:
    # Full HF Hub repo id (org/name) -- see configs/config.yaml for why the "Qwen/"
    # prefix is required (from_pretrained() 404s and silently falls back to mock
    # reasoning without it).
    vlm_model: str = "Qwen/Qwen2.5-VL-3B-Instruct"
    max_output_tokens: int = 1024
    temperature: float = 0.2


@dataclass
class AppConfig:
    video: VideoConfig = field(default_factory=VideoConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    reasoning: ReasoningConfig = field(default_factory=ReasoningConfig)
    demo_mode: bool = True   # True => pipelines use lightweight/mocked models


_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "configs", "config.yaml",
)


def load_config(path: str | None = None) -> AppConfig:
    """Load configs/config.yaml, falling back to defaults for any missing key."""
    cfg = AppConfig()
    path = path or _DEFAULT_CONFIG_PATH
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if "video" in raw:
            cfg.video = VideoConfig(**{**cfg.video.__dict__, **raw["video"]})
        if "audio" in raw:
            cfg.audio = AudioConfig(**{**cfg.audio.__dict__, **raw["audio"]})
        if "reasoning" in raw:
            cfg.reasoning = ReasoningConfig(**{**cfg.reasoning.__dict__, **raw["reasoning"]})
        cfg.demo_mode = raw.get("demo_mode", cfg.demo_mode)
    return cfg
