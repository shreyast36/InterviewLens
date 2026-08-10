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

logger = logging.getLogger(__name__)

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

SUPPRESSION_THRESHOLD = 0.3

_yolo_world = None  # lazy-loaded singleton -- one load per process, not per request


def _get_background_model():
    global _yolo_world
    if _yolo_world is None:
        from ultralytics import YOLO
        logger.info("Loading YOLO-World-S (champion) …")
        model = YOLO("yolov8s-worldv2.pt")
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


def extract_background_evidence(video_path: str, pose_evidence: dict, sample_fps: int = 3) -> dict:
    """Detects + tracks background objects with YOLO-World-S + ByteTrack, then
    suppresses any detection whose box mostly overlaps the subject's own framing
    bbox (from pose_evidence) -- prevents the subject's own chair/clothing from
    registering as clutter."""
    import supervision as sv

    frame_w, frame_h = pose_evidence.get("frame_size", [0, 0])
    tracker = sv.ByteTrack()
    tracked_frames = []
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

    pose_frames_by_ts = {fr["timestamp_s"]: fr["framing"] for fr in pose_evidence["frames"] if fr["framing"]["bbox"] is not None}
    pose_timestamps = np.array(sorted(pose_frames_by_ts.keys()))

    def nearest_subject_bbox(ts: float):
        if len(pose_timestamps) == 0:
            return None
        idx = int(np.argmin(np.abs(pose_timestamps - ts)))
        return pose_frames_by_ts[pose_timestamps[idx]]["bbox"]

    for f in tracked_frames:
        subject_bbox = nearest_subject_bbox(f["timestamp_s"])
        kept = []
        for d in f["detections"]:
            if subject_bbox is not None and _iou_overlap_frac(d["bbox_xyxy"], subject_bbox) > SUPPRESSION_THRESHOLD:
                continue
            kept.append(d)
        f["detections"] = kept

    track_summaries = _summarize_tracks(tracked_frames, frame_w, frame_h)

    return {
        "video": str(video_path).rsplit("/", 1)[-1],
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
