"""Batch pose extraction + rule-based signal detection for uploaded videos — Person A.

Ported from pipeline/notebooks/00_master_pipeline.ipynb sections 3 and 5, minus the
manual skeleton-review widget: there is no human in the loop for a real user upload.
Confidence gating (compute_framing's conf_thresh below, evidence_validation's
MIN_EVENT_CONFIDENCE downstream) is the automated substitute for that review step.

This is a *batch* pipeline (whole video in, one JSON dict out) rather than the
frame-by-frame streaming design in pose_estimation.py / signal_detection.py — it
matches what evidence_assembly.py's from_fused_evidence_json() actually consumes,
because that adapter was built against the notebook's batch output format.
"""
from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

COCO17_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]
UPPER_BODY_IDX = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
UPPER_BODY_NAMES = [COCO17_NAMES[i] for i in UPPER_BODY_IDX]

DET_REFRESH_EVERY_N_SAMPLES = 5  # re-run the person detector every Nth sampled frame
BBOX_MARGIN = 0.25                # pad the reused bbox to tolerate movement between refreshes
CONF = 0.3                        # keypoint-visibility confidence gate, used throughout

_rtmpose_champion = None  # lazy-loaded singleton -- one load per process, not per request


def _get_pose_model():
    global _rtmpose_champion
    if _rtmpose_champion is None:
        from rtmlib import Body as RTMLibBody
        logger.info("Loading RTMPose-S (champion) …")
        _rtmpose_champion = RTMLibBody(mode="lightweight", backend="onnxruntime", device="cpu")
    return _rtmpose_champion


def _pad_bbox(bbox, margin: float, frame_w: int, frame_h: int) -> list[float]:
    x1, y1, x2, y2 = bbox
    bw, bh = x2 - x1, y2 - y1
    return [
        max(0.0, x1 - bw * margin), max(0.0, y1 - bh * margin),
        min(float(frame_w), x2 + bw * margin), min(float(frame_h), y2 + bh * margin),
    ]


def compute_framing(keypoints_xyc: np.ndarray, frame_w: int, frame_h: int, conf_thresh: float = CONF) -> dict:
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


def extract_pose_evidence(video_path: str, sample_fps: int = 5) -> dict:
    """Runs the YOLOX person detector only every DET_REFRESH_EVERY_N_SAMPLES-th sampled
    frame; in between, reuses a bbox padded from the previous frame's own keypoints and
    calls the (much cheaper) pose model directly with it. Assumes a single continuous
    subject in frame -- if multiple people are ever detected, the first bbox is used.
    """
    model = _get_pose_model()
    cap = cv2.VideoCapture(str(video_path))
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    stride = max(1, round(src_fps / sample_fps))

    frames_out = []
    frame_idx = 0
    sample_idx = 0
    cached_bbox = None
    while True:
        # cap.grab() decodes without the BGR-array conversion cap.read() does -- for the
        # skipped frames that conversion is pure waste. Only cap.retrieve() (the expensive
        # half) on frames actually sampled. Measured ~4.6x faster decode in the notebook.
        if frame_idx % stride == 0:
            ok, frame = cap.read()
        else:
            ok = cap.grab()
        if not ok:
            break
        if frame_idx % stride == 0:
            if cached_bbox is None or sample_idx % DET_REFRESH_EVERY_N_SAMPLES == 0:
                bboxes = model.det_model(frame)
                bbox = bboxes[0] if len(bboxes) else None
            else:
                bbox = cached_bbox

            if bbox is None:
                pred = np.zeros((17, 3), dtype=np.float32)
                cached_bbox = None
            else:
                kpts, scores = model.pose_model(frame, bboxes=[bbox])
                pred = np.concatenate([kpts[0], scores[0, :, None]], axis=1).astype(np.float32)
                visible = pred[:, 2] > CONF
                cached_bbox = (
                    _pad_bbox([pred[visible, 0].min(), pred[visible, 1].min(),
                               pred[visible, 0].max(), pred[visible, 1].max()], BBOX_MARGIN, frame_w, frame_h)
                    if visible.sum() > 0 else None
                )

            framing = compute_framing(pred, frame_w, frame_h)
            frames_out.append({
                "timestamp_s": round(frame_idx / src_fps, 3),
                "keypoints": [[round(float(x), 2), round(float(y), 2), round(float(c), 3)] for x, y, c in pred[UPPER_BODY_IDX]],
                "framing": framing,
            })
            sample_idx += 1
        frame_idx += 1
    cap.release()

    return {
        "video": str(video_path).rsplit("/", 1)[-1],
        "fps_sampled": sample_fps,
        "model": "RTMPose-S",
        "frame_size": [frame_w, frame_h],
        "upper_body_joint_names": UPPER_BODY_NAMES,
        "frames": frames_out,
    }


def valid_tracking_pct(pose_evidence: dict, threshold: float = CONF) -> float:
    """Percentage of sampled frames where every upper-body joint cleared the
    confidence threshold -- the automated-pipeline analog of
    keypoint_processor.valid_tracking_pct() for the batch pose_evidence dict."""
    frames = pose_evidence["frames"]
    if not frames:
        return 0.0
    fully_visible = sum(1 for fr in frames if all(c >= threshold for _, _, c in fr["keypoints"]))
    return round(100.0 * fully_visible / len(frames), 1)


def _rolling_mean(vals: list[float | None], w: int) -> list[float | None]:
    out: list[float | None] = [None] * len(vals)
    for i in range(len(vals)):
        window = [v for v in vals[max(0, i - w + 1):i + 1] if v is not None]
        out[i] = float(np.mean(window)) if len(window) >= max(2, w // 2) else None
    return out


def _rolling_std(vals: list[float | None], w: int) -> list[float | None]:
    out: list[float | None] = [None] * len(vals)
    for i in range(len(vals)):
        window = [v for v in vals[max(0, i - w + 1):i + 1] if v is not None]
        out[i] = float(np.std(window)) if len(window) >= max(2, w // 2) else None
    return out


def _autocorr_peak(x: np.ndarray, min_lag: int = 2, max_lag: int = 10) -> float:
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    if x.std() < 1e-9:
        return 0.0
    ac = np.correlate(x, x, "full")[len(x) - 1:]
    ac = ac / ac[0]
    hi = min(max_lag + 1, len(ac))
    return float(ac[min_lag:hi].max()) if hi > min_lag else 0.0


def detect_signal_events(pose_evidence: dict) -> list[dict]:
    """17 geometric rules over the pose_evidence keypoints -- architecture block 2.4
    ("Distracting-Signal Detection"), no extra model. Every distance is normalized by
    shoulder width (scale-invariant across resolution/subject distance), every rule is
    confidence-gated, and every event needs ~0.6s of consecutive support (MIN_CONSEC)
    before it's reported, so single-frame jitter never becomes evidence. See
    00_master_pipeline.ipynb section 5 for the full rule table and rationale; this is a
    direct, tested port of that cell.
    """
    sample_fps = pose_evidence.get("fps_sampled", 5)
    min_consec = max(1, round(0.6 * sample_fps))
    period_window = max(8, round(4 * sample_fps))

    J = {name: i for i, name in enumerate(UPPER_BODY_NAMES)}
    frames = pose_evidence["frames"]
    n = len(frames)
    if n == 0:
        return []
    ts = np.array([fr["timestamp_s"] for fr in frames])
    kp = np.array([fr["keypoints"] for fr in frames], dtype=float)  # (n, 11, 3)

    def vis(i, *names):
        return all(kp[i, J[name], 2] > CONF for name in names)

    def pt(i, name):
        return kp[i, J[name], :2]

    feat_keys = ("sw", "head_height", "ear_sh", "eye_ratio", "pitch", "shoulder_deg", "eye_deg", "sh_mid_x", "mean_conf")
    feat: dict[str, list[float | None]] = {k: [None] * n for k in feat_keys}
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

    wrist_motion: list[float | None] = [None] * n
    nose_motion: list[float | None] = [None] * n
    max_jump: list[float | None] = [None] * n
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
        jumps = [float(np.linalg.norm(kp[i, j, :2] - kp[i - 1, j, :2])) / sw
                 for j in range(kp.shape[1]) if kp[i, j, 2] > CONF and kp[i - 1, j, 2] > CONF]
        if jumps:
            max_jump[i] = max(jumps)

    rule_series: dict[str, list[bool]] = {}

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
            crossed = lambda w, s: (pt(i, w)[0] - mid_x) * (pt(i, s)[0] - mid_x) < 0  # noqa: E731
            in_band = all(sh_y + 0.2 * sw < pt(i, w)[1] < sh_y + 1.6 * sw for w in ("left_wrist", "right_wrist"))
            series("arms_crossed")[i] = crossed("left_wrist", "left_shoulder") and crossed("right_wrist", "right_shoulder") and in_band

        series("hands_not_visible")[i] = kp[i, J["left_wrist"], 2] < CONF and kp[i, J["right_wrist"], 2] < CONF
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

    wm_roll = _rolling_mean(wrist_motion, 6)
    combo = [None if (w is None and nn is None) else float(np.mean([v for v in (w, nn) if v is not None]))
             for w, nn in zip(wrist_motion, nose_motion)]
    combo_roll = _rolling_mean(combo, 12)
    conf_std = _rolling_std(feat["mean_conf"], 10)
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
        for start in range(0, n - period_window + 1):
            clean = [v for v in vals[start:start + period_window] if v is not None]
            if len(clean) < period_window - 4:
                continue
            arr = np.array(clean)
            if arr.std() > min_amp and _autocorr_peak(arr) > 0.5:
                for i in range(start, start + period_window):
                    series(name)[i] = True

    def events_from(name, flags, this_min_consec):
        events, run = [], None
        for i, on in enumerate(list(flags) + [False]):
            if on and run is None:
                run = i
            elif not on and run is not None:
                if i - run >= this_min_consec:
                    events.append({"type": name, "start_s": float(ts[run]), "end_s": float(ts[i - 1])})
                run = None
        return events

    signal_events = []
    for name, flags in sorted(rule_series.items()):
        signal_events.extend(events_from(name, flags, 1 if name == "sudden_movement" else min_consec))
    signal_events.sort(key=lambda e: (e["start_s"], e["type"]))
    return signal_events


def grab_frames(video_path: str, frame_indices: list[int], fps: float) -> dict[int, np.ndarray]:
    """Decode the raw BGR frame at frame_index/fps seconds for each requested index.
    Used to hand real frame crops to evidence_assembly.from_fused_evidence_json()'s
    all_frames param -- frame_indices here are the fps_fused-indexed values that
    function returns from select_representative_frames(), not native video frame
    numbers."""
    cap = cv2.VideoCapture(str(video_path))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    out: dict[int, np.ndarray] = {}
    for idx in frame_indices:
        ts = idx / fps
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(ts * video_fps))
        ok, frame = cap.read()
        if ok:
            out[idx] = frame
    cap.release()
    return out
