"""Batch background-object detection + tracking for uploaded videos — Person A.

Ported from pipeline/notebooks/00_master_pipeline.ipynb section 6: YOLO-World-S
(open-vocabulary, champion) + ByteTrack, with person suppression using Pipeline A's
framing bboxes so the subject's own body/chair/clothing never registers as clutter.
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict

import cv2
import numpy as np

from interviewlens.video_pipeline.batch_pose import CONF, UPPER_BODY_NAMES, events_from_boolean_series

logger = logging.getLogger(__name__)

CLUTTER_MIN_OBJECTS = 4     # simultaneous tracked objects (any tier) to call the frame cluttered
LOW_LIGHT_MAX_LUMA = 60.0   # mean frame luma (0-255) below this -> too dark
OVEREXPOSED_MIN_LUMA = 210.0  # mean frame luma above this -> blown out
BACKLIT_FRAME_LUMA_MIN = 140.0   # frame bright enough that a dark face is suspicious
BACKLIT_CONTRAST_MIN = 35.0      # frame_luma - face_patch_luma gap that suggests backlighting

# background_category_key -> (display_name_for_prompt, tier). YOLO-World is open-
# vocabulary -- these keys are just text prompts fed to set_classes(), not an index
# into a fixed model head, so the taxonomy can be extended freely without retraining.
# The original 22 (through "speaker") are unchanged from the course notebooks; keep
# them stable since other evidence (committed pipeline/notebooks/outputs/*.json) was
# generated against that exact vocabulary.
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

    # --- expanded neutral: more common static furniture/decor ---
    "bookcase": ("bookshelf", "neutral"),
    "houseplant": ("plant", "neutral"),
    "clock": ("clock", "neutral"),
    "rug": ("rug", "neutral"),
    "desk": ("desk", "neutral"),
    "shelf": ("shelf", "neutral"),
    "window": ("window", "neutral"),
    "door": ("door", "neutral"),
    "whiteboard": ("whiteboard", "neutral"),
    "candle": ("candle", "neutral"),
    "trophy": ("trophy", "neutral"),
    "guitar": ("guitar", "neutral"),

    # --- expanded mild: soft clutter, informal-setting signals ---
    "clothes_hamper": ("laundry basket", "mild"),
    "shoe": ("shoe", "mild"),
    "backpack": ("backpack", "mild"),
    "box_(container)": ("cardboard box", "mild"),
    "trash_can": ("trash can", "mild"),
    "plate": ("plate", "mild"),
    "cup": ("cup", "mild"),
    "bottle": ("bottle", "mild"),

    # --- expanded distracting: more active electronics/screens ---
    "tablet_computer": ("tablet", "distracting"),
    "cellular_telephone": ("phone", "distracting"),
    "headphones": ("headphones", "distracting"),
    "printer": ("printer", "distracting"),
    "router_(computer_equipment)": ("router", "distracting"),

    # --- people/pets appearing in the background: explicitly distracting -- a
    # person or animal entering frame draws attention (and raises a privacy/
    # professionalism concern) in a way static furniture never does. The
    # existing person-suppression step (IoU against the subject's own framing
    # bbox) already keeps the interviewee's own body from self-matching here --
    # only a genuinely separate person/pet survives to be flagged.
    "person": ("person", "distracting"),
    "dog": ("dog", "distracting"),
    "cat": ("cat", "distracting"),

    # --- kitchen/home appliances: explicitly distracting -- signals an
    # unprofessional/non-dedicated interview setting.
    "washer_(washing_machine)": ("washing machine", "distracting"),
    "refrigerator": ("refrigerator", "distracting"),
    "blender": ("blender", "distracting"),
}
CLASS_NAMES = sorted(CATEGORY_INFO.keys())
CLASS_ID = {name: i for i, name in enumerate(CLASS_NAMES)}
DISPLAY_NAMES = [CATEGORY_INFO[n][0] for n in CLASS_NAMES]
TIER_BY_CLASS_ID = {CLASS_ID[n]: CATEGORY_INFO[n][1] for n in CLASS_NAMES}

SUPPRESSION_THRESHOLD = 0.3

_yolo_world = None  # lazy-loaded singleton -- one load per process, not per request

# Search order for the YOLO-World-S weights file.
_YOLO_CANDIDATES = [
    "yolov8s-worldv2.pt",                                       # cwd (e.g. repo root)
    "pipeline/notebooks/yolov8s-worldv2.pt",                    # repo sub-folder
    str(__import__("pathlib").Path(__file__).parent.parent.parent.parent
        / "pipeline" / "notebooks" / "yolov8s-worldv2.pt"),     # absolute from src/
]


def _get_background_model():
    global _yolo_world
    if _yolo_world is None:
        import pathlib
        from ultralytics import YOLO
        logger.info("Loading YOLO-World-S (champion) …")
        # Resolve the weights file from the search list
        weights = "yolov8s-worldv2.pt"   # fallback: ultralytics will download it
        for candidate in _YOLO_CANDIDATES:
            if pathlib.Path(candidate).exists():
                weights = candidate
                break
        logger.info("Using YOLO-World weights: %s", weights)
        model = YOLO(weights)
        # Warm up BEFORE set_classes(): ultralytics' AutoBackend.warmup() assumes the
        # native 80-class (COCO) head regardless of vocabulary, which crashes deep in
        # torchvision.ops.nms on this build if set_classes() already shrank the head to
        # our 22 classes. See notebook 02 §5 for the full explanation.
        _dummy = np.zeros((64, 64, 3), dtype=np.uint8)
        model.predict(_dummy, conf=0.15, verbose=False)
        model.set_classes(DISPLAY_NAMES)
        _yolo_world = model
    return _yolo_world


def _yolo_world_predict(img_bgr: np.ndarray, conf: float = 0.15) -> list[dict]:
    model = _get_background_model()
    result = model.predict(img_bgr, conf=conf, verbose=False)[0]
    out = []
    for box in result.boxes:
        out.append({
            "bbox_xyxy": box.xyxy[0].cpu().numpy().tolist(),
            "class_id": int(box.cls[0]),
            "score": float(box.conf[0]),
        })
    return out


def _sample_video_frames(video_path: str, sample_fps: int):
    cap = cv2.VideoCapture(str(video_path))
    try:
        src_fps = cap.get(cv2.CAP_PROP_FPS)
        stride = max(1, round(src_fps / sample_fps))
        frame_idx = 0
        while True:
            # See batch_pose.extract_pose_evidence for why grab()-without-retrieve() on
            # skipped frames is worth doing -- same trick, same ~4.6x faster decode.
            if frame_idx % stride == 0:
                ok, frame = cap.read()
            else:
                ok = cap.grab()
            if not ok:
                break
            if frame_idx % stride == 0:
                yield frame_idx / src_fps, frame
            frame_idx += 1
    finally:
        cap.release()


def _summarize_tracks(tracked_frames: list[dict], frame_w: int, frame_h: int) -> list[dict]:
    by_track: dict[int, list] = defaultdict(list)
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
        areas = [((d["bbox_xyxy"][2] - d["bbox_xyxy"][0]) * (d["bbox_xyxy"][3] - d["bbox_xyxy"][1])) / (frame_w * frame_h)
                 for _, d in entries]
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
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = max(1e-6, (ax2 - ax1) * (ay2 - ay1))
    return inter / area_a


_FACE_IDX = {name: i for i, name in enumerate(UPPER_BODY_NAMES)}


def _frame_luma(frame_bgr: np.ndarray) -> float:
    return float(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).mean())


def _face_patch_luma(frame_bgr: np.ndarray, keypoints: list, frame_w: int, frame_h: int) -> tuple[float | None, float]:
    """Returns (mean luma of a small patch around the face, face-keypoint confidence).
    Patch luma is None when the face wasn't localized at all this frame (nose at the
    all-zero "no person" sentinel) -- deliberately uses the raw keypoint position
    regardless of confidence to locate the patch, since a backlit face is exactly the
    case where confidence is low but the model still has a rough fix on where the face
    is (that's the whole point of the rule)."""
    nose = keypoints[_FACE_IDX["nose"]]
    l_eye = keypoints[_FACE_IDX["left_eye"]]
    r_eye = keypoints[_FACE_IDX["right_eye"]]
    l_sh = keypoints[_FACE_IDX["left_shoulder"]]
    r_sh = keypoints[_FACE_IDX["right_shoulder"]]
    face_conf = float(np.mean([nose[2], l_eye[2], r_eye[2]]))

    nx, ny = nose[0], nose[1]
    if nx == 0.0 and ny == 0.0:
        return None, face_conf

    if l_sh[2] > CONF and r_sh[2] > CONF:
        radius = abs(r_sh[0] - l_sh[0]) * 0.35
    else:
        radius = 0.06 * frame_w
    radius = max(6.0, radius)

    x1, y1 = max(0, int(nx - radius)), max(0, int(ny - radius))
    x2, y2 = min(frame_w, int(nx + radius)), min(frame_h, int(ny + radius))
    if x2 <= x1 or y2 <= y1:
        return None, face_conf
    return _frame_luma(frame_bgr[y1:y2, x1:x2]), face_conf


def extract_background_evidence(video_path: str, pose_evidence: dict, sample_fps: int = 3) -> dict:
    """Detects + tracks background objects with YOLO-World-S + ByteTrack, then
    suppresses any detection whose box mostly overlaps the subject's own framing
    bbox (from pose_evidence) -- prevents the subject's own chair/clothing from
    registering as clutter. Also computes lighting signals (low_light, overexposed,
    backlit_face) and cluttered_background off the same decoded frames, at zero extra
    decode cost, appended as pose_evidence-style "signal_events".
    """
    import supervision as sv

    frame_w, frame_h = pose_evidence.get("frame_size", [0, 0])
    pose_by_ts = {fr["timestamp_s"]: fr for fr in pose_evidence["frames"]}
    pose_timestamps = np.array(sorted(pose_by_ts.keys()))

    def nearest_pose_frame(ts: float):
        if len(pose_timestamps) == 0:
            return None
        idx = int(np.argmin(np.abs(pose_timestamps - ts)))
        return pose_by_ts[pose_timestamps[idx]]

    tracker = sv.ByteTrack()
    tracked_frames = []
    ts_list: list[float] = []
    frame_luma_series: list[float] = []
    backlit_series: list[bool] = []
    for ts, frame in _sample_video_frames(video_path, sample_fps):
        if not frame_w:
            frame_h, frame_w = frame.shape[:2]
        preds = _yolo_world_predict(frame, conf=0.15)
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

        # --- lighting signals, reusing this same decoded frame ---
        ts_list.append(round(ts, 3))
        frame_luma = _frame_luma(frame)
        frame_luma_series.append(frame_luma)
        pose_frame = nearest_pose_frame(round(ts, 3))
        if pose_frame is not None:
            face_patch_luma, face_conf = _face_patch_luma(frame, pose_frame["keypoints"], frame_w, frame_h)
            backlit = face_conf < CONF and (
                frame_luma > BACKLIT_FRAME_LUMA_MIN
                or (face_patch_luma is not None and frame_luma - face_patch_luma > BACKLIT_CONTRAST_MIN)
            )
        else:
            backlit = False
        backlit_series.append(backlit)

    pose_frames_by_ts = {fr["timestamp_s"]: fr["framing"] for fr in pose_evidence["frames"] if fr["framing"]["bbox"] is not None}
    subject_bbox_ts = np.array(sorted(pose_frames_by_ts.keys()))

    def nearest_subject_bbox(ts: float):
        if len(subject_bbox_ts) == 0:
            return None
        idx = int(np.argmin(np.abs(subject_bbox_ts - ts)))
        return pose_frames_by_ts[subject_bbox_ts[idx]]["bbox"]

    clutter_series: list[bool] = []
    for f in tracked_frames:
        subject_bbox = nearest_subject_bbox(f["timestamp_s"])
        kept = []
        for d in f["detections"]:
            if subject_bbox is not None and _iou_overlap_frac(d["bbox_xyxy"], subject_bbox) > SUPPRESSION_THRESHOLD:
                continue
            kept.append(d)
        f["detections"] = kept
        clutter_series.append(len(kept) >= CLUTTER_MIN_OBJECTS)

    track_summaries = _summarize_tracks(tracked_frames, frame_w, frame_h)

    # --- collapse the three per-frame boolean series into events ---
    ts_arr = np.array(ts_list)
    min_consec = max(1, round(0.6 * sample_fps))
    luma_arr = np.array(frame_luma_series)
    signal_events: list[dict] = []
    signal_events += events_from_boolean_series("low_light", (luma_arr < LOW_LIGHT_MAX_LUMA).tolist(), ts_arr, min_consec)
    signal_events += events_from_boolean_series("overexposed", (luma_arr > OVEREXPOSED_MIN_LUMA).tolist(), ts_arr, min_consec)
    signal_events += events_from_boolean_series("backlit_face", backlit_series, ts_arr, min_consec)
    signal_events += events_from_boolean_series("cluttered_background", clutter_series, ts_arr, min_consec)
    signal_events.sort(key=lambda e: (e["start_s"], e["type"]))

    return {
        "video": str(video_path).rsplit("/", 1)[-1],
        "fps_sampled": sample_fps,
        "model": "YOLO-World-S",
        "taxonomy": {name: CATEGORY_INFO[name][1] for name in CLASS_NAMES},
        "signal_events": signal_events,
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
