# InterviewLens — Team Roles & Task Breakdown

This document splits the InterviewLens computer-vision + speech + LLM
pipeline into four independent workstreams, mapped directly onto the
numbered blocks in the architecture diagram. Each role owns a vertical
slice of the pipeline end-to-end (model choice, implementation, tests) and
exposes a small, stable interface to the other three roles.

- **Person A — Visual / Pose Engineer** → diagram block **2**
- **Person B — Audio / Speech Engineer** → diagram block **3**
- **Person C — ML / Reasoning Engineer** → diagram blocks **4, 5, 6**
- **Person D — Platform / Product Engineer** → diagram blocks **7, 8** + integration

All four roles share **`src/interviewlens/common/schemas.py`** and
**`configs/config.yaml`**. Changes to shared files must be raised with the
whole team before merging — everything else is safe to change unilaterally
inside your own subsystem folder.

---

## Person A — Visual / Pose Engineer

**Owns:** `src/interviewlens/video_pipeline/`

**Diagram blocks:** 1.A (video input), 2.1–2.5

| Stage | File | Responsibility |
|---|---|---|
| 1.A Video input | `capture.py` | Webcam/video-file capture at 30 FPS, 1280×720 (or 720×1280), yields `(frame, timestamp)` |
| 2.1 Pose estimation | `pose_estimation.py` | Champion: **RTMPose-S**. Challenger: **SimpleBaseline**. Both implement `PoseEstimator.estimate()` |
| 2.2 Keypoint output | `keypoint_processor.py` | Normalize to 11 upper-body keypoints, `(x, y, confidence)`, add visibility flags |
| 2.3 Temporal sequence builder | `temporal_sequence.py` | Rolling window buffer: 64 frames (4s), 1s stride, shape `(64, 11, 3)` |
| 2.4 Distracting-signal detection | `signal_detection.py` | Champion: **PoseFormerV2-inspired Transformer**. Challenger: **ST-GCN**. Detects: repetitive hand movement, frequent posture shifting, hand-to-face activity |
| 2.5 Visual output | (consumed by Person C) | Emits `VisualEvent(signal_type, start_time_s, end_time_s, confidence)` |

### Deliverables
1. Real RTMPose-S (or equivalent lightweight pose model) wired into `RTMPoseEstimator.estimate()`.
2. A second pose backbone (SimpleBaseline or similar) wired into `SimpleBaselineEstimator.estimate()` for champion/challenger comparison.
3. A trained temporal classifier (PoseFormerV2-style transformer) for the 3 target signals, replacing `_mock_signals()`.
4. `valid_tracking_pct` computation (fraction of frames with all 11 joints above the visibility threshold) — currently hardcoded in `orchestration/pipeline.py`, should move into this module.
5. Unit tests in `tests/test_video_pipeline.py` covering real-model output shapes.

### Definition of done
- `PoseEstimator.estimate(frame, frame_index, timestamp_s) -> PoseFrame` returns real (not mock) 11-keypoint output.
- `SignalDetector.detect(window) -> list[VisualEvent]` returns real detections with calibrated confidence scores (not the placeholder variance heuristic).
- Champion vs. challenger can be swapped purely via `configs/config.yaml: video.pose_model`.
- All video-pipeline tests pass with `pytest -q tests/test_video_pipeline.py`.

### Suggested libraries
`mediapipe`, `mmpose` / `rtmlib`, `torch`, `opencv-python`.

---

## Person B — Audio / Speech Engineer

**Owns:** `src/interviewlens/audio_pipeline/`

**Diagram blocks:** 1.B (audio input), 3.1–3.5

| Stage | File | Responsibility |
|---|---|---|
| 1.B Audio input | `capture.py` | Mic capture at 16kHz, mono, real-time framing |
| 3.1 Preprocessing | `preprocessing.py` | Noise reduction, level normalization, VAD-based speech segmentation, framing/buffering |
| 3.2 Speech recognition | `asr.py` | Champion: **Whisper-small**. Challenger: **Wav2Vec 2.0**. Both implement `ASRModel.transcribe()`, output word-level timestamps |
| 3.3 Post-processing | `postprocessing.py` | Word-level alignment refinement, disfluency normalization, filler-word tagging, pause detection |
| 3.4 Delivery analytics | `delivery_analytics.py` | Words per minute, filler word count/rate, long-pause count, speaking time %, confidence scores |
| 3.5 Audio output | (consumed by Person C) | Emits `Transcript` + `AudioMetrics` |

### Deliverables
1. Real noise reduction (e.g. spectral gating / RNNoise) replacing the placeholder in `reduce_noise()`.
2. Real VAD (e.g. `webrtcvad` or `silero-vad`) replacing the energy-threshold placeholder in `detect_speech_segments()`.
3. Whisper-small wired into `WhisperSmallASR.transcribe()` (word timestamps required — use `faster-whisper` or `whisper-timestamped`).
4. Wav2Vec 2.0 wired into `Wav2Vec2ASR.transcribe()` as the challenger.
5. A real disfluency-normalization step in `normalize_disfluencies()` (rule-based is fine to start; ML-based is a stretch goal).
6. Unit tests in `tests/test_audio_pipeline.py` covering real-model transcription accuracy on a small labeled sample set.

### Definition of done
- `ASRModel.transcribe(segment) -> Transcript` returns real transcriptions with word-level timestamps accurate to ±200ms.
- `compute_metrics()` produces sane WPM/filler/pause numbers on a real recorded sample (sanity-checked by hand).
- Champion vs. challenger ASR can be swapped purely via `configs/config.yaml: audio.asr_model`.
- All audio-pipeline tests pass with `pytest -q tests/test_audio_pipeline.py`.

### Suggested libraries
`faster-whisper`, `transformers` (Wav2Vec2), `webrtcvad`, `silero-vad`, `sounddevice`, `torchaudio`.

---

## Person C — ML / Reasoning Engineer

**Owns:** `src/interviewlens/reasoning/`

**Diagram blocks:** 4, 5, 6

| Stage | File | Responsibility |
|---|---|---|
| 4. Multimodal fusion & evidence assembly | `evidence_assembly.py` | Align visual events + audio metrics by timestamp, select 6–12 representative frames, build the `EvidencePackage` |
| 5. Vision-language model reasoning | `vlm_reasoning.py` | **Qwen2.5-VL-3B-Instruct** (or similar), strict evidence-grounded JSON output: observations / explanations / suggestions |
| 6. Evidence validation layer | `evidence_validation.py` | Allowed-category check, event existence & confidence check, timestamp validity check, sufficient-supporting-evidence check, reliability scoring |

### Deliverables
1. Real frame-selection logic in `select_representative_frames()` that pulls actual JPEG/PNG crops (not just indices) to hand to the VLM.
2. Qwen2.5-VL-3B-Instruct (or a comparably sized open VLM) wired into `VLMReasoner.reason()`, replacing `_mock_reasoning()`. Must consume the prompt from `build_prompt()` plus the selected frame images, and return **strict JSON** matching `ReasoningOutput`.
3. Prompt-engineering / few-shot examples to keep the VLM from inventing unsupported claims (this is what block 6 double-checks).
4. Tightened validation rules in `validate()`:
   - Expand `ALLOWED_KEYWORDS` to match your final taxonomy of signals/metrics.
   - Add a proper supporting-evidence-count check (`MIN_SUPPORT`) instead of the current simple heuristic.
   - Tune `MIN_EVENT_CONFIDENCE` against real signal-detector output from Person A.
5. Unit tests in `tests/test_reasoning.py` covering both "valid" and "hallucinated" reasoning outputs (the validator must reject the latter).

### Definition of done
- `VLMReasoner.reason(evidence) -> ReasoningOutput` returns real model output, grounded only in the given `EvidencePackage`.
- `validate(evidence, reasoning) -> ValidationResult` reliably fails on synthetic hallucination test cases (e.g. claims about signals/timestamps that don't exist in the evidence).
- Reliability score correlates with manual reviewer agreement on a small hand-labeled test set (stretch goal: report Cohen's kappa).
- All reasoning tests pass with `pytest -q tests/test_reasoning.py`.

### Suggested libraries
`transformers`, `vllm` or `qwen-vl-utils`, `torch`, `pillow`.

---

## Person D — Platform / Product Engineer

**Owns:** `src/interviewlens/reporting/`, `src/interviewlens/orchestration/`, `src/interviewlens/api/`, `configs/`, `docker/`, CI/CD

**Diagram blocks:** 7, 8, plus overall integration

| Stage | File | Responsibility |
|---|---|---|
| 7. Coaching report | `reporting/coaching_report.py` | Delivery snapshot, top-3 strengths, top-3 improvements, timeline data, practice recommendation |
| Timeline visualization | `reporting/timeline_viz.py` | Renders the report timeline (matplotlib strip chart → swap for a real front-end component later) |
| Orchestration | `orchestration/pipeline.py` | Wires blocks 1–7 together end-to-end; the de-facto integration test for the whole team |
| API | `api/server.py` | FastAPI endpoint (`POST /analyze`) so the front end (or a demo script) can call the pipeline |
| Infra | `configs/config.yaml`, `docker/Dockerfile`, CI | Central config, containerization, environment reproducibility |

### Deliverables
1. A real "practice recommendation" generator in `coaching_report.py` (currently only delivery snapshot + strengths/improvements/timeline are populated).
2. A proper front-end or notebook demo consuming `POST /analyze` (out of scope for the initial repo, but stub the contract here).
3. Model checkpoint / artifact storage strategy (see block 8 in the diagram: model checkpoints, user-session storage, logs & metrics) — document in `docs/infra.md`.
4. CI pipeline (GitHub Actions) that runs `pytest -q` on every PR — **this is the top-priority infra deliverable**, since it's what keeps A/B/C's independent work from silently breaking each other.
5. Basic auth / secure storage plan for user sessions (per diagram: "Encrypted" user sessions) — can be a design doc for v1, not necessarily implemented.
6. Unit tests in `tests/test_reporting.py`.

### Definition of done
- `python scripts/run_demo.py` runs cleanly end-to-end and prints a populated `CoachingReport` as JSON.
- `uvicorn interviewlens.api.server:app` serves `POST /analyze` and returns a valid report for a sample question.
- CI runs the full test suite (`tests/test_video_pipeline.py`, `test_audio_pipeline.py`, `test_reasoning.py`, `test_reporting.py`) on every push/PR and blocks merges on failure.
- `docker build . && docker run -p 8000:8000 <image>` serves the API with no host-machine Python setup required.

### Suggested libraries
`fastapi`, `uvicorn`, `matplotlib`, `pydantic`, GitHub Actions.

---

## Shared contracts (do not change without team sign-off)

All cross-role data exchange happens through dataclasses in
`src/interviewlens/common/schemas.py`:

```
PoseFrame → PoseWindow → VisualEvent           (Person A → Person C)
Transcript → AudioMetrics                       (Person B → Person C)
EvidencePackage                                 (Person C internal)
ReasoningOutput → ValidationResult               (Person C internal)
CoachingReport                                  (Person C → Person D)
```

If a role needs a new field, add it as an **optional field with a default**
so the other three roles' code doesn't break, then message the team before
relying on it downstream.

## Suggested 4-week timeline

| Week | Person A | Person B | Person C | Person D |
|---|---|---|---|---|
| 1 | Wire real pose estimator (champion) | Wire real ASR (champion) + real VAD | Draft VLM prompt + wire evidence assembly | Stand up CI, confirm `run_demo.py` runs mock pipeline end-to-end |
| 2 | Train/wire signal-detection model (champion) | Wire delivery analytics against real transcripts | Wire real VLM inference | Wire coaching report against real (non-mock) upstream data |
| 3 | Add challenger pose model + comparison | Add challenger ASR + comparison | Build & tune evidence-validation rules | Timeline viz + API polish |
| 4 | Tests, calibration, `valid_tracking_pct` | Tests, calibration on real recordings | Hallucination test suite, reliability scoring | Dockerize, docs, final integration pass |

## Integration checkpoints

- **End of Week 1:** each person's subsystem passes its own unit tests in isolation using mocks for anyone else's stage.
- **End of Week 2:** first full-stack "real models" run of `scripts/run_demo.py` (still may use synthetic audio/video, but every model in the chain is real).
- **End of Week 3:** first run against an actual recorded webcam+mic sample end-to-end.
- **End of Week 4:** demo-ready: CI green, Docker image builds, README/ROLES docs updated to match final implementation choices.
