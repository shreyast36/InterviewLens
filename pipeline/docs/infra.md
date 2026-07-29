# Infrastructure notes (Person D)

This is a living design doc for block 8 of the architecture diagram
("Data, Models & Infrastructure"). Fill in real decisions as they're made.

## Datasets
- Pose training/eval: COCO Keypoints (or a project-specific mock-interview
  recording set for fine-tuning the signal-detection model).
- ASR: whichever dataset each ASR backend was pretrained on, plus a small
  hand-labeled sample of real interview recordings for calibration.

## Model checkpoints
- TODO: pick a storage location (e.g. a `models/` directory excluded from
  git via `.gitignore`, or an object store / Git LFS / Hugging Face Hub
  repo) once real checkpoints exist for the pose, signal-detection, ASR,
  and VLM models.

## Real-time inference engine
- Pose inference: per-frame (see `video_pipeline/pose_estimation.py`).
- Temporal model inference: windowed (see `video_pipeline/temporal_sequence.py`).
- ASR streaming inference: chunked via VAD segments (see `audio_pipeline/preprocessing.py`).
- Low-latency synchronization between visual and audio streams: TODO —
  currently both pipelines run independently and are aligned only by
  timestamp in `reasoning/evidence_assembly.py`. A real-time system will
  need a shared clock / buffer manager.

## Storage
- User sessions: should be encrypted at rest; not yet implemented — design
  only.
- Reports & evidence: currently returned directly from the API; persistent
  storage TODO.
- Logs & metrics: TODO — wire into whatever observability stack the
  eventual deployment target uses (e.g. CloudWatch, Prometheus).

## Deployment
- Local / cloud inference: `docker/Dockerfile` builds a container serving
  the FastAPI app (`interviewlens.api.server:app`).
- Web application: not included in this repo; the API contract
  (`POST /analyze`) is designed to be consumed by a separate front end.
