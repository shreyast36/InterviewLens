# InterviewLens — Final Project (MSADS Advanced Computer Vision, 31023)

## Goal

Analyze a recorded interview video (video + audio, ~2 min) and produce two independent,
gradable computer-vision assessments that are later fused into a single timestamped
evidence package:

1. **Problem 1 — Pose Estimation** (keypoint regression): upper-body pose, framing, and
   subject-region geometry.
2. **Problem 2 — Background Environment Validation** (open-vocabulary detection +
   tracking): clutter/distraction detection with temporal persistence and a 3-tier
   taxonomy (neutral / mild / distracting).

Both feed a common timeline that a future (out-of-scope for this delivery) VLM reasoning
stage would consume to produce coaching feedback. See `pipeline_final.jpeg` (high-level)
and `pipeline_detallado.png` (full system architecture) for the target design, and
`context.docx` for the design-conversation rationale behind every model choice.

Course rubric: `Project.pdf`. Two distinct cognitive problems, ≥2 champion-challenger
models per problem, detailed comparative metrics, deployment/maintenance plan.

## Scope of this delivery

Three notebooks only — everything past "Evidence Fusion & Timeline" in the architecture
diagram (VLM reasoning, evidence validation, final coaching report, audio/ASR/quality
supplementary modules) is **not** part of this delivery.

| # | Notebook | Produces |
|---|----------|----------|
| 1 | `notebooks/01_pipeline_A_pose_estimation.ipynb` | `outputs/pose_evidence.json` |
| 2 | `notebooks/02_pipeline_B_background_analysis.ipynb` | `outputs/background_evidence.json` |
| 3 | `notebooks/03_evidence_fusion_timeline.ipynb` | `outputs/fused_evidence.json` |

Notebook 2 depends on Notebook 1's output (person-region suppression). Notebook 3 depends
on both. Run in numeric order.

## Champion–challenger models

| Problem | Champion | Challenger | Why this pairing |
|---|---|---|---|
| Pose | RTMPose-S (via `rtmlib`, ONNX) | SimpleBaseline (ResNet + deconv head, implemented from scratch) | Heatmap-based SOTA vs. classic learned baseline — isolates "modern efficient architecture" as the variable |
| Background | YOLO-World-S (open-vocab) | RT-DETR-R18 (closed-set) | Open-vocabulary flexibility vs. closed-set precision/speed — see `context.docx` for the full argument |

Tracking uses **ByteTrack** via the already-installed `supervision` package (no separate
install needed).

## Environment

- Python venv: `/home/arcanegus/MSADS_/advanced_cv_31023/cv_env/` (activate with
  `source cv_env/bin/activate`). Always use this env/kernel for anything in this project
  — never a system or conda Python.
- GPU: RTX 5080 Laptop (16 GB). Prefer ONNX-Runtime-based inference (`rtmlib`) over
  packages that require compiling CUDA extensions (`mmcv`/`mmdet`) — this GPU's Blackwell
  architecture has a known history of build/runtime incompatibilities with packages that
  ship prebuilt CUDA kernels for older architectures.
- New packages needed beyond `requirements.txt`: `pycocotools`, `torchmetrics`, `rtmlib`,
  `lvis`. Install into `cv_env`, not globally.

## Folder layout

```
final_project/
├── CLAUDE.md              # this file
├── SKILLS.md               # technique/API reference used across notebooks
├── Project.pdf             # course rubric
├── context.docx            # design-conversation source of truth for model choices
├── pipeline_final.jpeg     # high-level architecture
├── pipeline_detallado.png  # detailed system architecture
└── notebooks/
    ├── 01_pipeline_A_pose_estimation.ipynb
    ├── 02_pipeline_B_background_analysis.ipynb
    ├── 03_evidence_fusion_timeline.ipynb
    ├── shared_video.py      # single-source-of-truth + checksum-verified video loader
    ├── data/                # downloaded dataset subsets + demo video
    ├── outputs/             # evidence JSONs, figures, eval tables
    └── saved_models/        # fine-tuned challenger weights
```

## Demo video

All three notebooks operate on the same video, `notebooks/data/demo_interview.mp4` —
52.0 s, 29.97 fps, 490×360, single person talking to camera. Trimmed from
`videos/Online Webcam Job Interview Tips.mp4` ("Zoe's Online Interview Tips",
user-provided): the original 66.1 s clip had 4 title-card/summary-slide segments
(~13 s total) cut in throughout — not real footage — which were removed with `ffmpeg`
`select`/`aselect` filters (see git history on `configs/config.yaml` and
`notebooks/shared_video.py` for when/why). The untrimmed original is kept at
`notebooks/data/demo_interview_original_with_slides.mp4` for reference. Using one
consistent video across all three notebooks is what lets Notebook 3's fused timeline
show real, matching timestamps. **TODO**: confirm and cite the original source/license
of this clip in Notebook 1's setup section before the file is included in the final
report submission.

### Shared demo video — single source of truth + checksum guard

Every notebook loads the video via `notebooks/shared_video.py`'s
`load_verified_video_path(DATA_DIR)` instead of hardcoding
`DATA_DIR / "demo_interview.mp4"`. That helper:

1. Reads the file*name* and expected SHA256 from `configs/config.yaml`'s `demo_video:`
   block (the single source of truth for which video the whole project analyzes).
2. Computes the SHA256 of the actual file on disk and asserts it matches.
3. Raises a clear `AssertionError` (not a silent pass-through) if the file is missing or
   its content has drifted from what's recorded.

**Why**: Pipeline A and Pipeline B used to each hardcode their own
`DEMO_VIDEO_PATH = DATA_DIR / "demo_interview.mp4"` literal. Nothing stopped one notebook
from being pointed at a different/updated video while the other kept analyzing the old
one — a silent mismatch that would only surface much later, in Notebook 3's fused
timeline (or not at all). The checksum makes that failure loud and immediate, at the top
of whichever notebook has the stale reference.

**When swapping the demo video**: update `configs/config.yaml`'s `demo_video.filename`
and `demo_video.sha256` (`sha256sum notebooks/data/<file>`) once, in that single file,
then re-run every notebook in order (01 → 02 → 03) so all evidence JSONs are regenerated
against the same footage. Do not hand-edit `DEMO_VIDEO_PATH` inside a notebook.

## Background training videos (`final_project/videos/`)

~52 additional Pexels clips (free-to-use, filenames follow Pexels' numeric-ID naming
convention, e.g. `13929625-uhd_2160_3840_24fps.mp4`) live in `final_project/videos/` for
**Pipeline B** (Notebook 2) EDA/training — most are vertical/social-media format, not
webcam interview shots, and are not used as the pose-estimation demo video.

**Excluded**: 9 files named `istockphoto-*-640_adpp_is.mp4` in that same folder are
watermarked iStock *preview* downloads (640 px, `_adpp_is` suffix) — not licensed for
real use. Do not reference or use these in any notebook or the final report; they are
left in place (not deleted) since they're the user's own downloaded files, but are
excluded from the project's data manifest.

## Conventions

- All notebook markdown/comments in English.
- No obligation to mirror the prior weekly course notebooks' exact structure — follow
  general ML-notebook best practices: clear intro, logical numbered sections, a
  standardized device-selection cell, reproducible seeds, a final summary/comparison
  section with real (non-placeholder) numbers.
- Every evidence-JSON claim must carry a timestamp and a measurement — no unsupported
  assertions (this rule is enforced formally in the (out-of-scope) Evidence Validation
  layer, but the JSON schemas here should already satisfy it).
- Training scope: small subsets (2–5k images) for challenger fine-tuning, ~15–20 epochs
  with early stopping on a held-out val split — enough for genuine, non-trivial
  champion-challenger comparisons without multi-hour runs.

## Verification standard

Notebooks must be executed top-to-bottom for real (`jupyter nbconvert --execute` or
equivalent) using the `cv_env` kernel before being called done. After execution, check the
saved `.ipynb` JSON for `execution_count`/error fields directly — `nbconvert` can silently
crash partway through a notebook while still reporting a misleading "exit code 0". Inspect
actual visual outputs (skeleton overlays, detection/track frames, the fused timeline
chart) rather than trusting a metric alone — a metric can be green while the rendered
output is visibly wrong.

## Reference

Full implementation plan: `/home/arcanegus/.claude/plans/rippling-skipping-glade.md`.
