"""End-to-end pipeline orchestrator — Person D (Platform/Infra Engineer)
owns this file, but it imports from every subsystem, so it doubles as the
integration contract test for the whole team.
"""
from __future__ import annotations

from interviewlens.audio_pipeline.asr import build_asr_model
from interviewlens.audio_pipeline.batch_audio_quality import extract_audio_quality_evidence
from interviewlens.audio_pipeline.capture import synthetic_audio
from interviewlens.audio_pipeline.delivery_analytics import compute_metrics
from interviewlens.audio_pipeline.postprocessing import normalize_disfluencies
from interviewlens.audio_pipeline.preprocessing import preprocess
from interviewlens.common.config import AppConfig, load_config
from interviewlens.common.schemas import CoachingReport, Transcript
from interviewlens.reasoning.evidence_assembly import assemble_evidence, from_fused_evidence_json
from interviewlens.reasoning.evidence_validation import validate
from interviewlens.reasoning.llm_reasoning import LLMReasoner
from interviewlens.reporting.coaching_report import build_coaching_report
from interviewlens.video_pipeline.ab_fusion import fuse_evidence
from interviewlens.video_pipeline.batch_background import extract_background_evidence
from interviewlens.video_pipeline.batch_pose import detect_signal_events, extract_pose_evidence, grab_frames, valid_tracking_pct as batch_valid_tracking_pct
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
    all_frames: dict[int, object] = {}  # frame_index → raw BGR numpy array
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

    # ---- 5. LLM reasoning (Person C) ------------------------------------
    reasoner = LLMReasoner(
        model_name=config.reasoning.llm_model,
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


def run_pipeline_from_video(
    video_path: str,
    question: str,
    config: AppConfig | None = None,
    pose_sample_fps: int = 5,
    background_sample_fps: int = 3,
) -> CoachingReport:
    """Runs the real pipeline against an uploaded video file: Pipeline A (pose,
    RTMPose-S) -> rule-based signal detection -> Pipeline B (background,
    YOLO-World-S + ByteTrack) -> A/B evidence fusion -> LLM reasoning -> evidence
    validation -> coaching report.

    This is the "someone uploads a video" path -- run_pipeline() above stays
    synthetic/demo-mode and untouched for whoever continues the real-time
    streaming architecture. There is deliberately no manual keypoint-review gate
    here (compare pipeline/notebooks/00_master_pipeline.ipynb section 4): a live
    API request has no human in the loop. Confidence gating -- compute_framing's
    conf_thresh in batch_pose.py, evidence_validation's MIN_EVENT_CONFIDENCE, and
    the unstable_tracking rule in detect_signal_events() -- is the automated
    substitute for that human review.

    Transcript/WPM/filler-word audio metrics are still the synthetic placeholder
    from Person B's subsystem (real ASR on the uploaded video's audio track is a
    separate, larger piece of scope). Audio *quality* is real, though: the
    uploaded video's actual audio track is analyzed for low_mic_level and
    intermittent_audio (signal-level RMS checks, no ASR) via
    audio_pipeline.batch_audio_quality, and merged into the same fused evidence
    the LLM sees. A video with no audio track at all is handled gracefully --
    extract_audio_quality_evidence() never raises, it just contributes no signals.
    """
    config = config or load_config()

    # ---- Pipeline A: pose + rule-based signals ---------------------------
    pose_evidence = extract_pose_evidence(video_path, sample_fps=pose_sample_fps)
    if not pose_evidence.get("frames"):
        raise ValueError(
            "No frames could be extracted from the video. "
            "Check that the file is a valid video with a readable video track."
        )
    pose_evidence["signal_events"] = detect_signal_events(pose_evidence)
    tracking_pct = batch_valid_tracking_pct(pose_evidence)

    # ---- Pipeline B: background detection + tracking ---------------------
    background_evidence = extract_background_evidence(video_path, pose_evidence, sample_fps=background_sample_fps)

    # ---- Audio quality (signal-level only -- low mic level / intermittent audio;
    # never raises, returns has_audio=False for videos with no audio track) --------
    audio_quality_evidence = extract_audio_quality_evidence(video_path)

    # ---- A/B fusion --------------------------------------------------------
    fused = fuse_evidence(pose_evidence, background_evidence, audio_quality_evidence)
    duration_s = float(fused.get("duration_s") or 1.0)  # guard against 0 / None

    # ---- Audio (Person B, synthetic placeholder -- see docstring) --------
    asr_model = build_asr_model(config.audio.asr_model)
    raw_audio = synthetic_audio(duration_s=duration_s, sample_rate=config.audio.sample_rate)
    segments = preprocess(raw_audio, config.audio.sample_rate)
    transcripts = [asr_model.transcribe(seg) for seg in segments]
    combined_words = [w for t in transcripts for w in t.words]
    transcript = normalize_disfluencies(
        Transcript(text=" ".join(t.text for t in transcripts), words=combined_words)
    )
    audio_metrics = compute_metrics(transcript, total_duration_s=duration_s)

    # ---- Multimodal fusion & evidence assembly (Person C) -----------------
    # Two passes: the first tells us which frame indices the reasoner wants;
    # the second decodes the actual frames at those indices.
    probe = from_fused_evidence_json(fused, question=question, transcript=transcript, audio_metrics=audio_metrics)
    all_frames = grab_frames(video_path, probe.selected_frames, fused["fps_fused"])
    evidence = from_fused_evidence_json(
        fused, question=question, transcript=transcript, audio_metrics=audio_metrics, all_frames=all_frames,
    )

    # ---- LLM reasoning (Person C) ------------------------------------------
    reasoner = LLMReasoner(
        model_name=config.reasoning.llm_model,
        max_tokens=config.reasoning.max_output_tokens,
        temperature=config.reasoning.temperature,
    )
    reasoning_output = reasoner.reason(evidence)

    # ---- Evidence validation (Person C) ------------------------------------
    validation = validate(evidence, reasoning_output)

    # ---- Coaching report (Person D) ----------------------------------------
    return build_coaching_report(
        duration_s=duration_s,
        valid_tracking_pct=tracking_pct,
        audio_metrics=audio_metrics,
        visual_events=evidence.visual_events,
        reasoning=reasoning_output,
        validation=validation,
    )
