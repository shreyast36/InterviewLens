"""
Shared data contracts for the InterviewLens pipeline.

Every team member owns one or more pipeline stages (see ROLES.md). These
dataclasses are the ONLY thing that should be considered a stable contract
between stages — if you need to change one, coordinate with whoever consumes
it (add new fields as optional/defaulted rather than changing existing ones).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SignalType(str, Enum):
    # Original gesture/posture signals (A's temporal model)
    REPETITIVE_HAND_MOVEMENT = "repetitive_hand_movement"
    FREQUENT_POSTURE_SHIFTING = "frequent_posture_shifting"
    HAND_TO_FACE_ACTIVITY    = "hand_to_face_activity"
    # Framing signals — derived from RTMPose-S bounding-box analysis (A)
    HEADROOM_TOO_LOOSE       = "headroom_too_loose"
    OFF_CENTER               = "off_center"
    TILTED                   = "tilted"
    # Background signals — derived from YOLO-World-S object detection (A)
    BACKGROUND_DISTRACTING   = "background_distracting"
    # Rule-based pose signals — geometry over reviewed RTMPose-S keypoints,
    # 00_master_pipeline.ipynb §5 (architecture block 2.4, no extra model).
    # Kept granular rather than folded into the three signals above: a coach
    # (and the VLM) can say something more specific than "posture shifting".
    HANDS_NEAR_FACE          = "hands_near_face"
    SELF_GROOMING            = "self_grooming"
    ARMS_CROSSED             = "arms_crossed"
    HANDS_NOT_VISIBLE        = "hands_not_visible"
    HEAD_DROP                = "head_drop"
    SHOULDERS_RAISED         = "shoulders_raised"
    HEAD_TURNED_AWAY         = "head_turned_away"
    LOOKING_DOWN             = "looking_down"
    HEAD_TILT                = "head_tilt"
    BODY_LEAN                = "body_lean"
    LEANING_IN               = "leaning_in"
    LEANING_OUT              = "leaning_out"
    FIDGETING                = "fidgeting"
    FROZEN                   = "frozen"
    SUDDEN_MOVEMENT          = "sudden_movement"
    SWAYING                  = "swaying"
    NODDING                  = "nodding"
    UNSTABLE_TRACKING        = "unstable_tracking"
    # Background: object enters/exits mid-clip rather than sitting static —
    # derived in the fusion stage from YOLO-World-S + ByteTrack track windows.
    TRANSIENT_OBJECT         = "transient_object"


@dataclass
class Keypoint:
    name: str
    x: float
    y: float
    confidence: float


@dataclass
class PoseFrame:
    """Output of 2.2 KEYPOINT OUTPUT (per frame)."""

    frame_index: int
    timestamp_s: float
    keypoints: list[Keypoint]
    visibility: list[bool] = field(default_factory=list)


@dataclass
class PoseWindow:
    """Output of 2.3 TEMPORAL SEQUENCE BUILDER (rolling window)."""

    start_time_s: float
    end_time_s: float
    frames: list[PoseFrame]


@dataclass
class VisualEvent:
    """Output of 2.4 DISTRACTING-SIGNAL DETECTION (temporal model)."""

    signal_type: SignalType
    start_time_s: float
    end_time_s: float
    confidence: float


@dataclass
class WordTiming:
    word: str
    start_time_s: float
    end_time_s: float
    confidence: float


@dataclass
class Transcript:
    """Output of 3.2 SPEECH RECOGNITION (streaming)."""

    text: str
    words: list[WordTiming]


@dataclass
class AudioMetrics:
    """Output of 3.4 DELIVERY ANALYTICS."""

    words_per_minute: float
    filler_word_count: int
    filler_word_rate: float
    long_pause_count: int
    long_pause_timestamps: list[tuple[float, float]]
    speaking_time_s: float
    confidence_scores: list[float] = field(default_factory=list)


@dataclass
class EvidencePackage:
    """Output of 4. MULTIMODAL FUSION & EVIDENCE ASSEMBLY."""

    question: str
    transcript: Transcript
    audio_metrics: AudioMetrics
    visual_events: list[VisualEvent]
    selected_frames: list[int]
    event_timestamps: dict[str, Any] = field(default_factory=dict)
    # PIL Images corresponding to selected_frames, ready to pass to the VLM.
    # Empty when running in demo/test mode without real video frames.
    frame_images: list = field(default_factory=list)


@dataclass
class ReasoningOutput:
    """Output of 5. VISION-LANGUAGE MODEL (evidence-grounded reasoning)."""

    observations: list[str]
    explanations: list[str]
    suggestions: list[str]
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Output of 6. EVIDENCE VALIDATION LAYER."""

    passed: bool
    reliability_score: float
    failed_checks: list[str] = field(default_factory=list)


@dataclass
class CoachingReport:
    """Output of 7. COACHING REPORT (post-response)."""

    duration_s: float
    valid_tracking_pct: float
    speaking_rate_wpm: float
    filler_word_count: int
    long_pause_count: int
    detected_signals: int
    strengths: list[str]
    improvements: list[str]
    timeline: list[dict[str, Any]]
    reliability_score: float
