"""A/B evidence fusion — Person A/B boundary.

Combines Pipeline A's pose + rule-based signal evidence with Pipeline B's background
evidence onto one common timeline. Ported from
pipeline/notebooks/00_master_pipeline.ipynb section 7.

Named ab_fusion, not evidence_assembly, to avoid confusion with the *other* fusion
stage in the architecture: reasoning/evidence_assembly.py's "4. Multimodal Fusion &
Evidence Assembly" combines audio + this module's output + the VLM's frame-image
needs -- a later, different step owned by Person C. This module produces exactly the
fused_evidence.json shape that reasoning/evidence_assembly.py's
from_fused_evidence_json() already consumes.
"""
from __future__ import annotations

import numpy as np

HEADROOM_MIN, HEADROOM_MAX = 0.05, 0.25
CENTERING_MAX_OFFSET = 0.15
ROLL_MAX_DEG = 10.0
DOMINANT_OBJECT_AREA_FRAC = 0.18  # a track occupying >=18% of the frame area is "dominant"


def _framing_flags(framing: dict | None) -> list[str]:
    if framing is None or framing.get("bbox") is None:
        return ["no_subject_detected"]
    flags = []
    headroom = framing["headroom_pct"]
    if headroom is not None:
        if headroom < HEADROOM_MIN:
            flags.append("headroom_too_tight")
        elif headroom > HEADROOM_MAX:
            flags.append("headroom_too_loose")
    offset = framing["centering_offset"]
    if offset is not None and max(abs(offset[0]), abs(offset[1])) > CENTERING_MAX_OFFSET:
        flags.append("off_center")
    roll = framing["roll_deg"]
    if roll is not None and abs(roll) > ROLL_MAX_DEG:
        flags.append("tilted")
    return flags


def fuse_evidence(pose_evidence: dict, background_evidence: dict, audio_evidence: dict | None = None) -> dict:
    """Builds a common timeline at the coarser of the two streams' sample rates,
    resamples both onto it, merges in pose_evidence["signal_events"] (rule-based pose
    signals), background_evidence["signal_events"] (lighting + cluttered_background),
    transient/dominant background objects (from track windows/area), and optionally
    audio_evidence["signal_events"] (low_mic_level, intermittent_audio -- see
    audio_pipeline/batch_audio_quality.py; pass None or a video with no audio track
    and this simply contributes nothing, no special-casing needed here), and computes
    a signal_summary aggregate (per-type counts/durations, % of timeline flagged,
    longest clean streak) for the VLM prompt to cite.
    """
    pose_fps = pose_evidence["fps_sampled"]
    bg_fps = background_evidence["fps_sampled"]
    video_duration_s = pose_evidence["frames"][-1]["timestamp_s"] if pose_evidence["frames"] else 0.0

    fusion_fps = min(pose_fps, bg_fps)
    fusion_grid = np.round(np.arange(0.0, video_duration_s + 1e-6, 1.0 / fusion_fps), 3)

    pose_by_ts = {fr["timestamp_s"]: fr for fr in pose_evidence["frames"]}
    pose_ts_arr = np.array(sorted(pose_by_ts.keys()))
    pose_tolerance_s = 0.5 / pose_fps

    def nearest_pose_frame(ts: float):
        if len(pose_ts_arr) == 0:
            return None
        idx = int(np.argmin(np.abs(pose_ts_arr - ts)))
        nearest_ts = pose_ts_arr[idx]
        if abs(nearest_ts - ts) > pose_tolerance_s + (1.0 / fusion_fps):
            return None
        return pose_by_ts[nearest_ts]

    pose_timeline = []
    for ts in fusion_grid:
        fr = nearest_pose_frame(float(ts))
        flags = _framing_flags(fr["framing"]) if fr is not None else ["no_pose_sample"]
        pose_timeline.append({"timestamp_s": float(ts), "framing": fr["framing"] if fr is not None else None, "flags": flags})

    def active_tracks_at(ts: float) -> list[dict]:
        half_step = 0.5 / fusion_fps
        return [d for d in background_evidence["detections"] if d["start_s"] - half_step <= ts <= d["end_s"] + half_step]

    background_timeline = []
    for ts in fusion_grid:
        active = active_tracks_at(float(ts))
        flags = [f"background_{d['tier']}:{d['class']}" for d in active if d["tier"] != "neutral"]
        background_timeline.append({
            "timestamp_s": float(ts),
            "active_tracks": [{"track_id": d["track_id"], "class": d["class"], "tier": d["tier"]} for d in active],
            "flags": flags,
        })

    all_signal_events = list(pose_evidence.get("signal_events", []))
    # background_evidence's own signal_events: lighting (low_light, overexposed,
    # backlit_face) and cluttered_background -- see batch_background.py.
    all_signal_events += background_evidence.get("signal_events", [])
    if audio_evidence:
        all_signal_events += audio_evidence.get("signal_events", [])
    for d in background_evidence["detections"]:
        if d["start_s"] > 1.0 and d["end_s"] < video_duration_s - 1.0 and d["end_s"] - d["start_s"] >= 0.5:
            all_signal_events.append({"type": f"transient_object:{d['class']}", "start_s": d["start_s"], "end_s": d["end_s"]})
        if d["box_area_frac"] >= DOMINANT_OBJECT_AREA_FRAC:
            all_signal_events.append({"type": f"dominant_object:{d['class']}", "start_s": d["start_s"], "end_s": d["end_s"]})

    def signal_flags_at(ts: float) -> list[str]:
        half_step = 0.5 / fusion_fps
        return sorted({e["type"] for e in all_signal_events if e["start_s"] - half_step <= ts <= e["end_s"] + half_step})

    fused_timeline = []
    for pose_pt, bg_pt in zip(pose_timeline, background_timeline):
        ts = pose_pt["timestamp_s"]
        fused_timeline.append({
            "timestamp_s": ts,
            "pose": {"framing": pose_pt["framing"]},
            "background": {"active_tracks": bg_pt["active_tracks"]},
            "flags": pose_pt["flags"] + bg_pt["flags"] + signal_flags_at(ts),
        })

    per_type: dict[str, dict] = {}
    for e in all_signal_events:
        s = per_type.setdefault(e["type"], {"events": 0, "total_s": 0.0})
        s["events"] += 1
        s["total_s"] = round(s["total_s"] + (e["end_s"] - e["start_s"]), 2)

    step = 1.0 / fusion_fps
    longest_clean, current_clean = 0, 0
    for pt in fused_timeline:
        current_clean = 0 if pt["flags"] else current_clean + 1
        longest_clean = max(longest_clean, current_clean)

    signal_summary = {
        "per_type": per_type,
        "pct_timestamps_flagged": round(100 * sum(1 for pt in fused_timeline if pt["flags"]) / len(fused_timeline), 1) if fused_timeline else 0.0,
        "longest_clean_streak_s": round(longest_clean * step, 2),
    }

    return {
        "video": pose_evidence["video"],
        "fps_fused": fusion_fps,
        "duration_s": float(video_duration_s),
        "source_streams": {
            "pose": {"model": pose_evidence["model"], "fps_sampled": pose_fps},
            "background": {"model": background_evidence["model"], "fps_sampled": bg_fps},
            "audio_quality": {"has_audio": bool(audio_evidence and audio_evidence.get("has_audio"))},
        },
        "signal_summary": signal_summary,
        "timeline": fused_timeline,
    }
