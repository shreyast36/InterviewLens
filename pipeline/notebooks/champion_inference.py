"""Champion-only inference: RTMPose-S (pose) + YOLO-World-S (background) + fusion.

Both champion models are pretrained/off-the-shelf and their weights are committed in
this directory (`weights/rtmpose/*.onnx`, `yolov8s-worldv2.pt`) -- neither requires
training or a network download, unlike the challenger models (SimpleBaseline,
RT-DETR-R18) that Notebooks 01/02 train from scratch purely for the champion-challenger
comparison tables. This module lets you produce real evidence JSONs against any video
without running that training (or the COCO/LVIS EDA that precedes it) -- see
04_inference_only.ipynb.

This is a **copy** of Notebooks 01/02/03's champion-path logic (kept in sync by hand),
not a refactor of them -- those notebooks stay exactly as originally verified/graded,
self-contained and importing nothing from here. If you change a threshold or the
gesture-detection heuristic in one place, mirror it in the other.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import supervision as sv
from rtmlib import Body as RTMLibBody
from ultralytics import YOLO

# --------------------------------------------------------------------------- #
# Pose (Notebook 01 section 5-8, champion: RTMPose-S)
# --------------------------------------------------------------------------- #

COCO17_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]
UPPER_BODY_IDX = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
UPPER_BODY_NAMES = [COCO17_NAMES[i] for i in UPPER_BODY_IDX]

# rtmlib's Body(mode="lightweight") normally resolves to these same two ONNX files via a
# network download on first use (cached to ~/.cache/rtmlib). Pointing at the copies
# committed under weights/rtmpose/ instead makes this repo fully offline -- rtmlib's
# base loader only downloads when os.path.exists(path) is False, so a valid local path
# short-circuits it.
_RTMPOSE_WEIGHTS_DIR = Path(__file__).parent / "weights" / "rtmpose"
_RTMPOSE_DET_ONNX = _RTMPOSE_WEIGHTS_DIR / "yolox_tiny_8xb8-300e_humanart-6f3252f9.onnx"
_RTMPOSE_POSE_ONNX = _RTMPOSE_WEIGHTS_DIR / "rtmpose-s_simcc-body7_pt-body7_420e-256x192-acd4a1ef_20230504.onnx"

def load_pose_model() -> RTMLibBody:
    """Loads the champion pose model -- pretrained, no training involved."""
    return RTMLibBody(
        det=str(_RTMPOSE_DET_ONNX),
        det_input_size=(416, 416),
        pose=str(_RTMPOSE_POSE_ONNX),
        pose_input_size=(192, 256),
        backend="onnxruntime",
        device="cpu",
    )


def rtmpose_predict(model: RTMLibBody, img_bgr: np.ndarray) -> np.ndarray:
    """Returns (17, 3) array [x, y, confidence] for the highest-confidence detected
    person, or an all-zero array if no person was detected."""
    kpts, scores = model(img_bgr)
    if kpts.shape[0] == 0:
        return np.zeros((17, 3), dtype=np.float32)
    best = int(scores.mean(axis=1).argmax())
    return np.concatenate([kpts[best], scores[best, :, None]], axis=1).astype(np.float32)


def compute_framing(keypoints_xyc: np.ndarray, frame_w: int, frame_h: int, conf_thresh: float = 0.3) -> dict:
    """keypoints_xyc: (17, 3) [x, y, confidence] in COCO-17 order, original frame coords."""
    upper = keypoints_xyc[UPPER_BODY_IDX]
    visible = upper[upper[:, 2] > conf_thresh]
    if len(visible) == 0:
        return {"bbox": None, "headroom_pct": None, "centering_offset": None, "roll_deg": None}

    x1, y1 = visible[:, 0].min(), visible[:, 1].min()
    x2, y2 = visible[:, 0].max(), visible[:, 1].max()
    bbox = [float(x1), float(y1), float(x2), float(y2)]

    headroom_pct = float(y1 / frame_h)

    bbox_cx, bbox_cy = (x1 + x2) / 2, (y1 + y2) / 2
    centering_offset = [
        float((bbox_cx - frame_w / 2) / (frame_w / 2)),
        float((bbox_cy - frame_h / 2) / (frame_h / 2)),
    ]

    l_eye, r_eye = keypoints_xyc[1], keypoints_xyc[2]
    l_sh, r_sh = keypoints_xyc[5], keypoints_xyc[6]
    if l_eye[2] > conf_thresh and r_eye[2] > conf_thresh:
        dx, dy = r_eye[0] - l_eye[0], r_eye[1] - l_eye[1]
    elif l_sh[2] > conf_thresh and r_sh[2] > conf_thresh:
        dx, dy = r_sh[0] - l_sh[0], r_sh[1] - l_sh[1]
    else:
        dx, dy = None, None
    roll_deg = float(np.degrees(np.arctan2(dy, dx))) if dx is not None else None

    return {"bbox": bbox, "headroom_pct": headroom_pct, "centering_offset": centering_offset, "roll_deg": roll_deg}


def extract_pose_evidence(model: RTMLibBody, video_path: Path, sample_fps: int) -> dict:
    cap = cv2.VideoCapture(str(video_path))
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    stride = max(1, round(src_fps / sample_fps))

    frames_out = []
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % stride == 0:
            pred = rtmpose_predict(model, frame)
            framing = compute_framing(pred, frame_w, frame_h)
            frames_out.append({
                "timestamp_s": round(frame_idx / src_fps, 3),
                "keypoints": [[round(float(x), 2), round(float(y), 2), round(float(c), 3)] for x, y, c in pred[UPPER_BODY_IDX]],
                "framing": framing,
            })
        frame_idx += 1
    cap.release()

    pose_evidence = {
        "video": video_path.name,
        "fps_sampled": sample_fps,
        "model": "RTMPose-S",
        "frame_size": [frame_w, frame_h],
        "upper_body_joint_names": UPPER_BODY_NAMES,
        "frames": frames_out,
    }
    pose_evidence["signal_events"] = detect_rule_based_signals(pose_evidence)
    return pose_evidence


# --------------------------------------------------------------------------- #
# Rule-based pose signal detection (00_master_pipeline.ipynb section 5)
# --------------------------------------------------------------------------- #
#
# Pure geometry over the champion keypoints -- no extra model, no training data. This
# is the FULL 17-rule set the master notebook implements (architecture block 2.4,
# "Distracting-Signal Detection"); it supersedes an earlier, narrower hand-to-face-only
# heuristic that lived here (v1/v2, confidence+proximity on the wrists alone) -- checked
# against real video, that narrower heuristic missed real touches this rule set catches
# via `hands_near_face`, and produced a flag name ("hand_near_face") that was NOT the
# one Shreyas's evidence_assembly.py _FLAG_TO_SIGNAL actually keys on for the broader
# signal taxonomy ("hands_near_face", plural, matching SignalType.HANDS_NEAR_FACE).
#
# Design (unchanged from the master notebook, ported verbatim):
#   - Scale invariance: every distance normalized by shoulder width, so thresholds hold
#     across resolutions and subject-to-camera distances.
#   - Confidence gating: a rule only evaluates when its required joints pass CONF; an
#     occluded joint yields "unknown" (skipped), never a flag.
#   - Temporal hysteresis: a condition must hold >=MIN_CONSEC consecutive samples
#     (~0.6s) before becoming an event -- single-frame jitter is not evidence.
#     `sudden_movement` is the exception (a point event by definition, MIN_CONSEC=1).
#
# Known 2D limitation (documented, not hidden): "hand near face" cannot distinguish
# depth -- a hand raised in front of the chest at face height can false-positive.

CONF = 0.3


def _autocorr_peak(x, min_lag=2, max_lag=10) -> float:
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    if x.std() < 1e-9:
        return 0.0
    ac = np.correlate(x, x, "full")[len(x) - 1:]
    ac = ac / ac[0]
    hi = min(max_lag + 1, len(ac))
    return float(ac[min_lag:hi].max()) if hi > min_lag else 0.0


def _rolling_mean(vals, w):
    out = [None] * len(vals)
    for i in range(len(vals)):
        window = [v for v in vals[max(0, i - w + 1):i + 1] if v is not None]
        out[i] = float(np.mean(window)) if len(window) >= max(2, w // 2) else None
    return out


def _rolling_std(vals, w):
    out = [None] * len(vals)
    for i in range(len(vals)):
        window = [v for v in vals[max(0, i - w + 1):i + 1] if v is not None]
        out[i] = float(np.std(window)) if len(window) >= max(2, w // 2) else None
    return out


def _events_from(name, flags, min_consec):
    events, run = [], None
    for i, on in enumerate(list(flags) + [False]):
        if on and run is None:
            run = i
        elif not on and run is not None:
            if i - run >= min_consec:
                events.append({"type": name, "start_s": run, "end_s": i - 1})  # indices, resolved to TS by caller
            run = None
    return events


def detect_rule_based_signals(pose_evidence: dict) -> list[dict]:
    """Returns a list of {"type", "start_s", "end_s"} signal events -- the 17 rules from
    00_master_pipeline.ipynb section 5, run over `pose_evidence["frames"]`. Attach the
    result as `pose_evidence["signal_events"]` (extract_pose_evidence does this
    automatically) so fuse_evidence() can fold the events into the fused timeline's
    flags, which is what Shreyas's evidence_assembly.py._FLAG_TO_SIGNAL actually reads.
    """
    frames = pose_evidence["frames"]
    n = len(frames)
    if n == 0:
        return []
    sample_fps = pose_evidence["fps_sampled"]
    min_consec = max(1, round(0.6 * sample_fps))   # ~0.6s hysteresis
    period_window = max(4, round(4 * sample_fps))  # ~4s window for periodicity rules

    names = pose_evidence["upper_body_joint_names"]
    j = {name: i for i, name in enumerate(names)}
    ts = np.array([fr["timestamp_s"] for fr in frames])
    kp = np.array([fr["keypoints"] for fr in frames], dtype=float)  # (n, 11, 3)

    def vis(i, *joint_names):
        return all(kp[i, j[jn], 2] > CONF for jn in joint_names)

    def pt(i, joint_name):
        return kp[i, j[joint_name], :2]

    feat_keys = ("sw", "head_height", "ear_sh", "eye_ratio", "pitch", "shoulder_deg", "eye_deg", "sh_mid_x", "mean_conf")
    feat = {k: [None] * n for k in feat_keys}
    for i in range(n):
        feat["mean_conf"][i] = float(kp[i, :, 2].mean())
        if not vis(i, "left_shoulder", "right_shoulder"):
            continue
        l_sh, r_sh = pt(i, "left_shoulder"), pt(i, "right_shoulder")
        sw = float(np.linalg.norm(l_sh - r_sh))
        if sw < 1e-6:
            continue
        sh_mid = (l_sh + r_sh) / 2
        feat["sw"][i] = sw
        feat["sh_mid_x"][i] = float(sh_mid[0]) / sw
        d = r_sh - l_sh
        feat["shoulder_deg"][i] = float(np.degrees(np.arctan2(d[1], d[0])))
        if vis(i, "nose"):
            feat["head_height"][i] = float(sh_mid[1] - pt(i, "nose")[1]) / sw
        gaps = [float(pt(i, s)[1] - pt(i, e)[1]) / sw
                for s, e in (("left_shoulder", "left_ear"), ("right_shoulder", "right_ear")) if vis(i, e)]
        if gaps:
            feat["ear_sh"][i] = float(np.mean(gaps))
        if vis(i, "left_eye", "right_eye"):
            l_eye, r_eye = pt(i, "left_eye"), pt(i, "right_eye")
            eye_dist = float(np.linalg.norm(l_eye - r_eye))
            feat["eye_ratio"][i] = eye_dist / sw
            de = r_eye - l_eye
            feat["eye_deg"][i] = float(np.degrees(np.arctan2(de[1], de[0])))
            if vis(i, "nose") and eye_dist > 1e-6:
                feat["pitch"][i] = float(pt(i, "nose")[1] - (l_eye[1] + r_eye[1]) / 2) / eye_dist

    def clip_median(key):
        vals = [v for v in feat[key] if v is not None]
        return float(np.median(vals)) if vals else None

    med = {k: clip_median(k) for k in ("head_height", "ear_sh", "eye_ratio", "pitch")}
    first_sw = [v for v in feat["sw"] if v is not None][:sample_fps]
    baseline_sw = float(np.median(first_sw)) if first_sw else None

    wrist_motion, nose_motion, max_jump = [None] * n, [None] * n, [None] * n
    for i in range(1, n):
        sw = feat["sw"][i]
        if sw is None:
            continue
        wm = [float(np.linalg.norm(pt(i, w) - pt(i - 1, w))) / sw
              for w in ("left_wrist", "right_wrist") if vis(i, w) and vis(i - 1, w)]
        if wm:
            wrist_motion[i] = float(np.mean(wm))
        if vis(i, "nose") and vis(i - 1, "nose"):
            nose_motion[i] = float(np.linalg.norm(pt(i, "nose") - pt(i - 1, "nose"))) / sw
        jumps = [float(np.linalg.norm(kp[i, jj, :2] - kp[i - 1, jj, :2])) / sw
                 for jj in range(kp.shape[1]) if kp[i, jj, 2] > CONF and kp[i - 1, jj, 2] > CONF]
        if jumps:
            max_jump[i] = max(jumps)

    rule_series: dict[str, list] = {}

    def series(name):
        return rule_series.setdefault(name, [False] * n)

    def face_center(i):
        pts = [pt(i, name) for name in ("nose", "left_eye", "right_eye") if vis(i, name)]
        return np.mean(pts, axis=0) if len(pts) >= 2 else None

    for i in range(n):
        sw = feat["sw"][i]
        if sw is None:
            continue

        fc = face_center(i)
        near_face = fc is not None and any(
            vis(i, w) and np.linalg.norm(pt(i, w) - fc) < 0.50 * sw for w in ("left_wrist", "right_wrist"))
        series("hands_near_face")[i] = near_face
        series("self_grooming")[i] = not near_face and any(
            vis(i, w) and vis(i, e) and np.linalg.norm(pt(i, w) - pt(i, e)) < 0.40 * sw
            for w in ("left_wrist", "right_wrist") for e in ("left_ear", "right_ear"))

        if vis(i, "left_wrist", "right_wrist"):
            mid_x = float((pt(i, "left_shoulder")[0] + pt(i, "right_shoulder")[0]) / 2)
            sh_y = float((pt(i, "left_shoulder")[1] + pt(i, "right_shoulder")[1]) / 2)
            crossed = lambda w, s: (pt(i, w)[0] - mid_x) * (pt(i, s)[0] - mid_x) < 0
            in_band = all(sh_y + 0.2 * sw < pt(i, w)[1] < sh_y + 1.6 * sw for w in ("left_wrist", "right_wrist"))
            series("arms_crossed")[i] = crossed("left_wrist", "left_shoulder") and crossed("right_wrist", "right_shoulder") and in_band

        series("hands_not_visible")[i] = kp[i, j["left_wrist"], 2] < CONF and kp[i, j["right_wrist"], 2] < CONF
        if feat["head_height"][i] is not None and med["head_height"]:
            series("head_drop")[i] = feat["head_height"][i] < 0.8 * med["head_height"]
        if feat["ear_sh"][i] is not None and med["ear_sh"]:
            series("shoulders_raised")[i] = feat["ear_sh"][i] < 0.75 * med["ear_sh"]
        if feat["eye_ratio"][i] is not None and med["eye_ratio"]:
            series("head_turned_away")[i] = feat["eye_ratio"][i] < 0.75 * med["eye_ratio"]
        if feat["pitch"][i] is not None and med["pitch"] is not None:
            series("looking_down")[i] = feat["pitch"][i] > med["pitch"] + 0.25
        if feat["eye_deg"][i] is not None and feat["shoulder_deg"][i] is not None:
            series("head_tilt")[i] = abs(feat["eye_deg"][i] - feat["shoulder_deg"][i]) > 8.0
        if feat["shoulder_deg"][i] is not None:
            series("body_lean")[i] = abs(feat["shoulder_deg"][i]) > 8.0
        if baseline_sw:
            series("leaning_in")[i] = sw > 1.2 * baseline_sw
            series("leaning_out")[i] = sw < 0.8 * baseline_sw

    wm_roll = _rolling_mean(wrist_motion, round(1.2 * sample_fps))
    combo = [None if (w is None and nm is None) else float(np.mean([v for v in (w, nm) if v is not None]))
             for w, nm in zip(wrist_motion, nose_motion)]
    combo_roll = _rolling_mean(combo, round(2.4 * sample_fps))
    conf_std = _rolling_std(feat["mean_conf"], round(2 * sample_fps))
    for i in range(n):
        if wm_roll[i] is not None:
            series("fidgeting")[i] = wm_roll[i] > 0.20
        if combo_roll[i] is not None:
            series("frozen")[i] = combo_roll[i] < 0.02
        if max_jump[i] is not None:
            series("sudden_movement")[i] = max_jump[i] > 0.9
        if conf_std[i] is not None:
            series("unstable_tracking")[i] = conf_std[i] > 0.12

    for name, key, min_amp in (("swaying", "sh_mid_x", 0.05), ("nodding", "head_height", 0.02)):
        vals = feat[key]
        for start in range(0, max(0, n - period_window + 1)):
            clean = [v for v in vals[start:start + period_window] if v is not None]
            if len(clean) < period_window - 4:
                continue
            arr = np.array(clean)
            if arr.std() > min_amp and _autocorr_peak(arr) > 0.5:
                for i in range(start, start + period_window):
                    series(name)[i] = True

    signal_events = []
    for name, flags in sorted(rule_series.items()):
        for ev in _events_from(name, flags, 1 if name == "sudden_movement" else min_consec):
            signal_events.append({
                "type": ev["type"],
                "start_s": float(ts[ev["start_s"]]),
                "end_s": float(ts[ev["end_s"]]),
            })
    signal_events.sort(key=lambda e: (e["start_s"], e["type"]))
    return signal_events


# --------------------------------------------------------------------------- #
# Background (Notebook 02 sections 3-9, champion: YOLO-World-S)
# --------------------------------------------------------------------------- #

# lvis_category_name -> (display_name_for_prompt, tier)
CATEGORY_INFO = {
    "chair": ("chair", "neutral"),
    "sofa": ("sofa", "neutral"),
    "painting": ("painting", "neutral"),
    "curtain": ("curtain", "neutral"),
    "vase": ("vase", "neutral"),
    "flowerpot": ("flower pot", "neutral"),
    "lamp": ("lamp", "neutral"),
    "mirror": ("mirror", "neutral"),
    "cabinet": ("cabinet", "neutral"),
    "drawer": ("drawer", "neutral"),
    "poster": ("poster", "neutral"),
    "pillow": ("pillow", "mild"),
    "blanket": ("blanket", "mild"),
    "bed": ("bed", "mild"),
    "towel": ("towel", "mild"),
    "bath_towel": ("bath towel", "mild"),
    "television_set": ("television", "distracting"),
    "fan": ("fan", "distracting"),
    "monitor_(computer_equipment) computer_monitor": ("computer monitor", "distracting"),
    "laptop_computer": ("laptop", "distracting"),
    "computer_keyboard": ("keyboard", "distracting"),
    "speaker_(stero_equipment)": ("speaker", "distracting"),
}
CLASS_NAMES = sorted(CATEGORY_INFO.keys())
CLASS_ID = {name: i for i, name in enumerate(CLASS_NAMES)}
DISPLAY_NAMES = [CATEGORY_INFO[n][0] for n in CLASS_NAMES]
TIER_BY_CLASS_ID = {CLASS_ID[n]: CATEGORY_INFO[n][1] for n in CLASS_NAMES}

SUPPRESSION_THRESHOLD = 0.3  # person-suppression IoU-overlap-with-subject-bbox threshold


def load_background_model(weights_path: str = "yolov8s-worldv2.pt") -> YOLO:
    """Loads the champion background model -- pretrained, open-vocabulary, no training
    involved. Applies the same warmup-before-set_classes fix as Notebook 02 (see comment
    below): calling set_classes() shrinks the detection head's class count from the
    native 80 (COCO) to our 22, but ultralytics' AutoBackend.warmup() builds its dummy
    warmup tensor assuming the *original* 80-class channel layout regardless, crashing in
    torchvision.ops.nms on this torch/torchvision build unless we warm up once BEFORE
    swapping in our custom taxonomy vocabulary.
    """
    model = YOLO(weights_path)
    _dummy = np.zeros((64, 64, 3), dtype=np.uint8)
    model.predict(_dummy, conf=0.15, verbose=False)
    model.set_classes(DISPLAY_NAMES)
    return model


def yolo_world_predict(model: YOLO, img_bgr: np.ndarray, conf: float = 0.15) -> list[dict]:
    """Returns a list of {bbox_xyxy, class_id, score} in original image coordinates."""
    result = model.predict(img_bgr, conf=conf, verbose=False)[0]
    return [
        {
            "bbox_xyxy": box.xyxy[0].cpu().numpy().tolist(),
            "class_id": int(box.cls[0]),
            "score": float(box.conf[0]),
        }
        for box in result.boxes
    ]


def sample_video_frames(video_path: Path, sample_fps: int):
    cap = cv2.VideoCapture(str(video_path))
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    stride = max(1, round(src_fps / sample_fps))
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % stride == 0:
            yield frame_idx / src_fps, frame
        frame_idx += 1
    cap.release()


def track_objects(model: YOLO, video_path: Path, sample_fps: int) -> list[dict]:
    tracker = sv.ByteTrack()
    tracked_frames = []
    for ts, frame in sample_video_frames(video_path, sample_fps):
        preds = yolo_world_predict(model, frame, conf=0.15)
        if preds:
            xyxy = np.array([p["bbox_xyxy"] for p in preds], dtype=np.float32)
            confidence = np.array([p["score"] for p in preds], dtype=np.float32)
            class_id = np.array([p["class_id"] for p in preds], dtype=int)
            dets = sv.Detections(xyxy=xyxy, confidence=confidence, class_id=class_id)
        else:
            dets = sv.Detections.empty()
        dets = tracker.update_with_detections(dets)
        frame_dets = [
            {"track_id": int(tid), "class_id": int(cid), "bbox_xyxy": box.tolist(), "score": float(conf)}
            for box, cid, tid, conf in zip(dets.xyxy, dets.class_id, dets.tracker_id, dets.confidence)
        ]
        tracked_frames.append({"timestamp_s": round(ts, 3), "detections": frame_dets})
    return tracked_frames


def summarize_tracks(tracked_frames: list[dict], video_w: int, video_h: int) -> list[dict]:
    by_track = defaultdict(list)
    for f in tracked_frames:
        for d in f["detections"]:
            by_track[d["track_id"]].append((f["timestamp_s"], d))

    summaries = []
    for track_id, entries in by_track.items():
        entries.sort(key=lambda e: e[0])
        start_s, end_s = entries[0][0], entries[-1][0]
        window_frames = [f for f in tracked_frames if start_s <= f["timestamp_s"] <= end_s]
        persistence_pct = len(entries) / max(1, len(window_frames))
        class_ids = Counter(d["class_id"] for _, d in entries)
        class_id = class_ids.most_common(1)[0][0]
        areas = [
            ((d["bbox_xyxy"][2] - d["bbox_xyxy"][0]) * (d["bbox_xyxy"][3] - d["bbox_xyxy"][1])) / (video_w * video_h)
            for _, d in entries
        ]
        summaries.append({
            "track_id": track_id,
            "class_id": class_id,
            "class_name": CLASS_NAMES[class_id],
            "display_name": DISPLAY_NAMES[class_id],
            "tier": TIER_BY_CLASS_ID[class_id],
            "persistence_pct": round(persistence_pct, 3),
            "start_s": start_s,
            "end_s": end_s,
            "box_area_frac": round(float(np.mean(areas)), 4),
            "frames_present": len(entries),
        })
    return summaries


def _iou_overlap_frac(box_a, box_b) -> float:
    """Fraction of box_a's area that overlaps box_b (subject-suppression style, not
    symmetric IoU -- we want 'is this detection mostly inside the subject region'."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = max(1e-6, (ax2 - ax1) * (ay2 - ay1))
    return inter / area_a


def suppress_person_detections(tracked_frames: list[dict], pose_evidence: dict) -> int:
    """Mutates `tracked_frames` in place, dropping detections that mostly overlap the
    subject's own framing bbox (Notebook 01's output). Returns the count suppressed."""
    pose_frames_by_ts = {
        fr["timestamp_s"]: fr["framing"] for fr in pose_evidence["frames"] if fr["framing"]["bbox"] is not None
    }
    pose_timestamps = np.array(sorted(pose_frames_by_ts.keys()))

    def nearest_subject_bbox(ts: float):
        if len(pose_timestamps) == 0:
            return None
        idx = int(np.argmin(np.abs(pose_timestamps - ts)))
        return pose_frames_by_ts[pose_timestamps[idx]]["bbox"]

    suppressed_count = 0
    for f in tracked_frames:
        subject_bbox = nearest_subject_bbox(f["timestamp_s"])
        kept = []
        for d in f["detections"]:
            if subject_bbox is not None and _iou_overlap_frac(d["bbox_xyxy"], subject_bbox) > SUPPRESSION_THRESHOLD:
                suppressed_count += 1
                continue
            kept.append(d)
        f["detections"] = kept
    return suppressed_count


def extract_background_evidence(model: YOLO, video_path: Path, pose_evidence: dict, sample_fps: int, video_w: int, video_h: int) -> dict:
    tracked_frames = track_objects(model, video_path, sample_fps)
    suppress_person_detections(tracked_frames, pose_evidence)
    track_summaries = summarize_tracks(tracked_frames, video_w, video_h)

    return {
        "video": video_path.name,
        "fps_sampled": sample_fps,
        "model": "YOLO-World-S",
        "taxonomy": {name: CATEGORY_INFO[name][1] for name in CLASS_NAMES},
        "detections": [
            {
                "track_id": t["track_id"],
                "class": t["display_name"],
                "tier": t["tier"],
                "persistence_pct": t["persistence_pct"],
                "start_s": t["start_s"],
                "end_s": t["end_s"],
                "box_area_frac": t["box_area_frac"],
            }
            for t in track_summaries
        ],
    }


# --------------------------------------------------------------------------- #
# Fusion (Notebook 03)
# --------------------------------------------------------------------------- #

HEADROOM_MIN, HEADROOM_MAX = 0.05, 0.25
CENTERING_MAX_OFFSET = 0.15
ROLL_MAX_DEG = 10.0


def _framing_flags(framing: dict) -> list[str]:
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


def pose_flags(fr: dict) -> list[str]:
    return _framing_flags(fr["framing"])


def fuse_evidence(pose_evidence: dict, background_evidence: dict) -> dict:
    """Same fusion logic as Notebook 03, plus 00_master_pipeline.ipynb section 7's two
    additions -- both required for Shreyas's evidence_assembly.py to have anything to
    map beyond framing/background flags:

    - `pose_evidence["signal_events"]` (the 17 rule-based signals from
      detect_rule_based_signals(), attached by extract_pose_evidence()) folded into the
      per-timestamp `flags`, the same way framing/background flags already are.
    - `transient_object:<class>` flags for background tracks whose whole lifetime sits
      strictly inside the clip (entered and left frame mid-video).
    - A `signal_summary` block (per-type event counts/durations, % of timeline flagged,
      longest clean streak) that evidence_assembly.py passes straight through to the
      VLM prompt when present.
    """
    assert pose_evidence["video"] == background_evidence["video"], (
        f"Evidence extracted from different videos: pose={pose_evidence['video']!r}, "
        f"background={background_evidence['video']!r}"
    )

    pose_fps = pose_evidence["fps_sampled"]
    bg_fps = background_evidence["fps_sampled"]
    fusion_fps = min(pose_fps, bg_fps)
    video_duration_s = pose_evidence["frames"][-1]["timestamp_s"]
    fusion_grid = np.round(np.arange(0.0, video_duration_s + 1e-6, 1.0 / fusion_fps), 3)

    pose_by_ts = {fr["timestamp_s"]: fr for fr in pose_evidence["frames"]}
    pose_timestamps = np.array(sorted(pose_by_ts.keys()))
    pose_tolerance_s = 0.5 / pose_fps

    def nearest_pose_frame(ts: float):
        idx = int(np.argmin(np.abs(pose_timestamps - ts)))
        nearest_ts = pose_timestamps[idx]
        if abs(nearest_ts - ts) > pose_tolerance_s + (1.0 / fusion_fps):
            return None
        return pose_by_ts[nearest_ts]

    def active_tracks_at(ts: float) -> list[dict]:
        half_step = 0.5 / fusion_fps
        return [
            d for d in background_evidence["detections"]
            if d["start_s"] - half_step <= ts <= d["end_s"] + half_step
        ]

    all_signal_events = list(pose_evidence.get("signal_events", []))
    for d in background_evidence["detections"]:
        if d["start_s"] > 1.0 and d["end_s"] < video_duration_s - 1.0 and d["end_s"] - d["start_s"] >= 0.5:
            all_signal_events.append({"type": f"transient_object:{d['class']}", "start_s": d["start_s"], "end_s": d["end_s"]})

    def signal_flags_at(ts: float) -> list[str]:
        half_step = 0.5 / fusion_fps
        return sorted({e["type"] for e in all_signal_events if e["start_s"] - half_step <= ts <= e["end_s"] + half_step})

    fused_timeline = []
    for ts in fusion_grid:
        ts = float(ts)
        fr = nearest_pose_frame(ts)
        pose_flags_here = pose_flags(fr) if fr is not None else ["no_pose_sample"]
        active = active_tracks_at(ts)
        bg_flags_here = [f"background_{d['tier']}:{d['class']}" for d in active if d["tier"] != "neutral"]
        fused_timeline.append({
            "timestamp_s": ts,
            "pose": {"framing": fr["framing"] if fr is not None else None},
            "background": {"active_tracks": [{"track_id": d["track_id"], "class": d["class"], "tier": d["tier"]} for d in active]},
            "flags": pose_flags_here + bg_flags_here + signal_flags_at(ts),
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
        "pct_timestamps_flagged": round(100 * sum(1 for pt in fused_timeline if pt["flags"]) / len(fused_timeline), 1),
        "longest_clean_streak_s": round(longest_clean * step, 2),
    }

    return {
        "video": pose_evidence["video"],
        "fps_fused": fusion_fps,
        "duration_s": float(video_duration_s),
        "source_streams": {
            "pose": {"model": pose_evidence["model"], "fps_sampled": pose_fps},
            "background": {"model": background_evidence["model"], "fps_sampled": bg_fps},
        },
        "signal_summary": signal_summary,
        "timeline": fused_timeline,
    }


# --------------------------------------------------------------------------- #
# Visualization helpers (sanity-check overlays, same as Notebooks 01/02)
# --------------------------------------------------------------------------- #

COCO17_SKELETON = [
    (0, 1), (0, 2), (1, 3), (2, 4),  # face
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # arms
    (5, 11), (6, 12), (11, 12),  # torso
    (11, 13), (13, 15), (12, 14), (14, 16),  # legs
]
TIER_COLORS = {"neutral": (44, 127, 184), "mild": (240, 180, 41), "distracting": (240, 59, 32)}


def draw_skeleton(img: np.ndarray, kpts: np.ndarray, edges=COCO17_SKELETON, color=(0, 255, 0)) -> np.ndarray:
    """kpts: (17, 3) [x, y, visible] -- visible as a 0/1-like truthy flag, not a raw confidence."""
    out = img.copy()
    for (a, b) in edges:
        if kpts[a, 2] > 0 and kpts[b, 2] > 0:
            pa, pb = tuple(kpts[a, :2].astype(int)), tuple(kpts[b, :2].astype(int))
            cv2.line(out, pa, pb, color, 2)
    for j in range(kpts.shape[0]):
        if kpts[j, 2] > 0:
            cv2.circle(out, tuple(kpts[j, :2].astype(int)), 3, (0, 0, 255), -1)
    return out


def draw_tracks(img: np.ndarray, detections: list[dict]) -> np.ndarray:
    out = img.copy()
    for d in detections:
        x1, y1, x2, y2 = map(int, d["bbox_xyxy"])
        tier = TIER_BY_CLASS_ID[d["class_id"]]
        color = TIER_COLORS[tier]
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(out, f"#{d['track_id']} {DISPLAY_NAMES[d['class_id']]}", (x1, max(0, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    return out
