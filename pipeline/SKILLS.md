# InterviewLens — Technique & API Reference

Running reference of the specific models, metrics, and schemas used across the three
notebooks, so any future session (or teammate) can ramp up without re-deriving choices
already made in `context.docx`. Update this file whenever a notebook adopts a new
technique or changes a package/API choice.

---

## Pose estimation (Notebook 1)

### RTMPose-S (champion)
- Package: `rtmlib` — pure ONNX Runtime inference, no `mmcv`/`mmdet` build required.
  This is why it was chosen over loading RTMPose through the full `mmpose` stack.
- Usage: `rtmlib.Wholebody` or `rtmlib.RTMPose` with a COCO-pretrained ONNX checkpoint
  (auto-downloaded on first use). Input: BGR frame (OpenCV convention). Output: `(17, 2)`
  keypoint array + `(17,)` confidence, COCO-17 order.
- We only keep the 11 upper-body joints: nose, left/right eye, left/right ear,
  left/right shoulder, left/right elbow, left/right wrist (indices 0–2,3,4,5,6,7,8,9,10
  in COCO-17 ordering — verify against `rtmlib`'s actual index map before slicing).

### SimpleBaseline (challenger, implemented from scratch)
- Backbone: `torchvision.models.resnet{18,34,50}` with ImageNet-pretrained weights,
  `strict=False` load into a custom class if the final FC layer is stripped.
- Head: 3 transposed-conv (deconv) layers upsampling the backbone's final feature map to
  heatmap resolution, followed by a 1×1 conv to `num_keypoints` channels. This head is
  written by hand — do not import a pretrained SimpleBaseline checkpoint; the point of
  this challenger is the from-scratch heatmap decoder.
- Loss: per-keypoint MSE against a Gaussian heatmap centered on the GT keypoint
  (`sigma` typically 2 px at heatmap resolution).
- Decoding: heatmap argmax + optional sub-pixel refinement (quarter-offset from
  second-highest neighboring pixel).

### Framing & Subject Region (geometry, no model)
- Bounding box: min/max over visible keypoint (x, y).
- Headroom %: vertical gap between top of frame and top of the bbox, divided by frame
  height.
- Centering offset: bbox center vs. frame center, normalized by frame width/height.
- Roll angle: `atan2(dy, dx)` of the shoulder-to-shoulder or eye-to-eye line.
- This module's bbox output is the input to Notebook 2's person-suppression step —
  keep its output schema stable (`{x1,y1,x2,y2}` in pixel coords per frame).

### Pose metrics
- **PCK@0.2**: fraction of keypoints within `0.2 × torso_diameter` (or head segment
  length, per protocol) of GT.
- **OKS-AP**: COCO's Object Keypoint Similarity, computed via `pycocotools.cocoeval`
  (`iouType='keypoints'`).
- **MPJPE**: mean per-joint position error in pixels (or normalized units), simplest to
  compute by hand — `mean(||pred_xy - gt_xy||)` over visible joints.

### Pose evidence JSON schema (`outputs/pose_evidence.json`)
```json
{
  "video": "demo_interview.mp4",
  "fps_sampled": 5,
  "model": "RTMPose-S",
  "frames": [
    {
      "timestamp_s": 0.0,
      "keypoints": [[x, y, conf], "... x11"],
      "framing": {"bbox": [x1,y1,x2,y2], "headroom_pct": 0.0, "centering_offset": [0.0,0.0], "roll_deg": 0.0}
    }
  ]
}
```

---

## Background analysis (Notebook 2)

### YOLO-World-S (champion, open-vocabulary)
- Package: `ultralytics` (already installed, ≥8.4). Class: `ultralytics.YOLO` loaded
  with a `yolov8s-worldv2.pt` (or similar) checkpoint.
- Prompt-then-detect: call `model.set_classes([...])` with the taxonomy's category names
  once, then run standard `model.predict(frame)` — this re-parameterizes text embeddings
  into the detection head so inference doesn't need the text encoder per frame.

### RT-DETR-R18 (challenger, closed-set)
- Either `transformers.RTDetrForObjectDetection` (HF, already validated available in this
  course's DETR notebook) with `RTDetrImageProcessor`, or `ultralytics.RTDETR`.
- NMS-free, end-to-end set prediction (DETR-family). Fine-tune the classification head on
  the taxonomy subset; keep the backbone/encoder mostly frozen for the small-data budget.

### 3-tier distraction taxonomy
Defined once as a Python dict/config, reused everywhere (detection eval, persistence
mapping, evidence JSON) — do not redefine ad hoc in multiple cells:
```python
TAXONOMY = {
    "neutral": ["wall", "door", "plant", "bookshelf", ...],
    "mild": ["bed_made", "tv_off", "hanging_clothes", ...],
    "distracting": ["tv_on", "person_moving", "pet", "laundry_pile", ...],
}
```

### ByteTrack (tracking)
- Package: `supervision.ByteTrack` — already installed, no separate `bytetracker`/`yolox`
  package needed.
- Usage: `tracker = sv.ByteTrack(); tracked = tracker.update_with_detections(detections)`
  per frame, where `detections` is a `supervision.Detections` object built from the
  detector's boxes/scores/classes.
- Two-stage association (high-score IoU match, then low-score recovery) — no ReID model.

### Temporal persistence & distraction tier
- Persistence % per track = `frames_present / frames_sampled_in_track_window`.
- `> 80%` persistence → static furniture (real, stable object).
- `< 20%` persistence → transient event or false positive; if it forms a bounded
  start/end interval, treat as a transient event (e.g., person walking through frame).
- Map each surviving detection/track to its taxonomy tier for aggregation.

### Person suppression
- Load `outputs/pose_evidence.json`'s per-frame `framing.bbox`.
- Drop any Pipeline-B detection whose box overlaps the subject bbox above an IoU/overlap
  threshold (e.g. 0.3) — prevents the subject's own chair/clothing from registering as
  background clutter.

### Detection/tracking metrics
- **mAP@[.5:.95]**, **AP50**, **AP-small**: via `pycocotools.cocoeval` or `torchmetrics`'s
  `MeanAveragePrecision`.
- Tracking: full HOTA/IDF1 need MOT-style ground truth we likely won't have for the demo
  video — document this as a known limitation; report a simpler proxy (ID-switch count,
  track fragmentation) instead, and note in the notebook that HOTA/IDF1 apply if/when a
  labeled benchmark (e.g. MOT17-style) is added.

### Background evidence JSON schema (`outputs/background_evidence.json`)
```json
{
  "video": "demo_interview.mp4",
  "fps_sampled": 3,
  "model": "YOLO-World-S",
  "detections": [
    {
      "track_id": 1,
      "class": "laundry_pile",
      "tier": "distracting",
      "persistence_pct": 0.15,
      "start_s": 47.0,
      "end_s": 52.0,
      "box_area_frac": 0.08
    }
  ]
}
```

---

## Evidence fusion (Notebook 3)

- Two source streams sampled at different rates (pose 5 fps, background 2–3 fps) —
  resample onto a common grid rather than forcing one rate onto the other's raw data.
- Fused schema is the union of both evidence files keyed by `timestamp_s`, plus derived
  fields (e.g. `flags` list per timestamp). Write to `outputs/fused_evidence.json`.
- Every fused claim must carry a timestamp + the measurement that supports it (persistence
  %, track lifespan, frame area, etc.) — this is the rule the (out-of-scope) Evidence
  Validation layer will enforce later; satisfy it here by construction.
- Timeline visualization: matplotlib Gantt/broken-barh chart, x-axis = video time,
  separate rows for pose/framing flags vs. background flags.

---

## Environment gotchas

- `cv_env` is the only Python environment for this project — verify via
  `which python` / `pip list` inside the activated venv before running anything.
- Avoid `mmcv`/`mmdet`/full `mmpose` installs on this machine (RTX 5080, Blackwell) —
  prefer ONNX Runtime (`rtmlib`) or plain `torch`/`torchvision` implementations.
- `jupyter nbconvert --execute` can silently fail partway through a long notebook while
  still reporting exit code 0 — always cross-check `execution_count`/`error` fields in the
  saved `.ipynb` JSON after a full run.
