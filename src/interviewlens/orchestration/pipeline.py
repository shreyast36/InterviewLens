"""End-to-end pipeline orchestrator — Person D (Platform/Infra Engineer)
owns this file, but it imports from every subsystem, so it doubles as the
integration contract test for the whole team.
"""
from __future__ import annotations

from interviewlens.audio_pipeline.asr import build_asr_model
from interviewlens.audio_pipeline.capture import synthetic_audio
from interviewlens.audio_pipeline.delivery_analytics import compute_metrics
from interviewlens.audio_pipeline.postprocessing import normalize_disfluencies
from interviewlens.audio_pipeline.preprocessing import preprocess
from interviewlens.common.config import AppConfig, load_config
from interviewlens.common.schemas import CoachingReport, Transcript
from interviewlens.reasoning.evidence_assembly import assemble_evidence
from interviewlens.reasoning.evidence_validation import validate
from interviewlens.reasoning.vlm_reasoning import VLMReasoner
from interviewlens.reporting.coaching_report import build_coaching_report
from interviewlens.video_pipeline.capture import synthetic_frames
from interviewlens.video_pipeline.keypoint_processor import normalize_frame, valid_tracking_pct
from interviewlens.video_pipeline.pose_estimation import build_pose_estimator
from interviewlens.video_pipeline.signal_detection import build_signal_detector
from interviewlens.video_pipeline.temporal_sequence import RollingWindowBuilder


def run_pipeline(question: str, config: AppConfig | None = None) -> CoachingReport:
    """Runs the full InterviewLens pipeline in demo_mode (synthetic
    audio/video, mocked model outputs) and returns a CoachingReport.

    Swap `demo_mode: false` in configs/config.yaml once each team member
    has wired their real model into their subsystem — this function's
    control flow does not need to change.
    """
    config = config or load_config()

    # ---- 2. Visual pipeline (Person A) ----------------------------------
    pose_estimator = build_pose_estimator(config.video.pose_model)
    signal_detector = build_signal_detector("champion")
    window_builder = RollingWindowBuilder(
        fps=config.video.fps,
        window_seconds=config.video.window_seconds,
        stride_seconds=config.video.stride_seconds,
    )

    visual_events = []
    pose_frames = []
    all_frames: dict[int, object] = {}  # frame_index → raw BGR numpy array for VLM
    n_frames = config.video.fps * 8  # ~8s synthetic clip
    for frame, timestamp in synthetic_frames(n_frames, fps=config.video.fps):
        frame_idx = int(timestamp * config.video.fps)
        all_frames[frame_idx] = frame  # store raw frame for evidence assembly
        pose_frame = pose_estimator.estimate(frame, frame_idx, timestamp)
        pose_frame = normalize_frame(pose_frame)
        pose_frames.append(pose_frame)
        window = window_builder.push(pose_frame)
        if window is not None:
            visual_events.extend(signal_detector.detect(window))

    tracking_pct = valid_tracking_pct(pose_frames)

    # ---- 3. Audio pipeline (Person B) -----------------------------------
    asr_model = build_asr_model(config.audio.asr_model)
    raw_audio = synthetic_audio(duration_s=8.0, sample_rate=config.audio.sample_rate)
    segments = preprocess(raw_audio, config.audio.sample_rate)

    transcripts = [asr_model.transcribe(seg) for seg in segments]
    combined_words = [w for t in transcripts for w in t.words]
    transcript = normalize_disfluencies(
        Transcript(text=" ".join(t.text for t in transcripts), words=combined_words)
    )
    audio_metrics = compute_metrics(transcript, total_duration_s=8.0)

    # ---- 4. Multimodal fusion & evidence assembly (Person C) ------------
    evidence = assemble_evidence(
        question=question,
        transcript=transcript,
        audio_metrics=audio_metrics,
        visual_events=visual_events,
        fps=config.video.fps,
        all_frames=all_frames,
    )

    # ---- 5. VLM reasoning (Person C) ------------------------------------
    reasoner = VLMReasoner(
        model_name=config.reasoning.vlm_model,
        max_tokens=config.reasoning.max_output_tokens,
        temperature=config.reasoning.temperature,
    )
    reasoning_output = reasoner.reason(evidence)

    # ---- 6. Evidence validation (Person C) ------------------------------
    validation = validate(evidence, reasoning_output)

    # ---- 7. Coaching report (Person D) -----------------------------------
    report = build_coaching_report(
        duration_s=8.0,
        valid_tracking_pct=tracking_pct,
        audio_metrics=audio_metrics,
        visual_events=visual_events,
        reasoning=reasoning_output,
        validation=validation,
    )
    return report
