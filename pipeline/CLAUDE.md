# InterviewLens — Final Project (MSADS Advanced Computer Vision, 31023)

## Start here — activate the environment

Before running **any** Python, pip, or notebook command in this project, activate `cv_env`
first:

```bash
source /home/arcanegus/MSADS_/advanced_cv_31023/cv_env/bin/activate
```

Every notebook must run under the `cv_env` Jupyter kernel (see `## Environment` below) —
never a system or conda Python, and never a bare `python`/`pip` from a different env. If
executing a notebook non-interactively, point directly at the env's binaries instead of
relying on shell activation, e.g.
`/home/arcanegus/MSADS_/advanced_cv_31023/cv_env/bin/jupyter nbconvert --execute ...`.

## Goal

Analyze a recorded interview video (video + audio, ~2 min) and produce two independent,
gradable computer-vision assessments that are later fused into a single timestamped
evidence package:

1. **Problem 1 — Pose Estimation** (keypoint regression): upper-body pose, framing, and
   subject-region geometry.
2. **Problem 2 — Background Environment Validation** (open-vocabulary detection +
   tracking): clutter/distraction detection with temporal persistence and a 3-tier
   taxonomy (neutral / mild / distracting).

Both feed a common timeline that an LLM reasoning stage consumes to produce coaching
feedback — now implemented in `src/interviewlens/reasoning/` (see "Full pipeline &
Streamlit app" below), separate from these notebooks. See `pipeline_final.jpeg` (high-level)
and `pipeline_detallado.png` (full system architecture) for the target design, and
`context.docx` for the design-conversation rationale behind every model choice.

Course rubric: `Project.pdf`. Two distinct cognitive problems, ≥2 champion-challenger
models per problem, detailed comparative metrics, deployment/maintenance plan.

## Scope of this delivery

Originally scoped as three notebooks only, stopping at "Evidence Fusion & Timeline" — VLM
reasoning, evidence validation, coaching report, and real audio/ASR were explicitly
out of scope. **That has since expanded.** The full pipeline — real ASR (faster-whisper),
LLM reasoning (Ollama/Nemotron-Mini), evidence validation, and the final coaching
report — is now implemented in `src/interviewlens/` (repo root, one level up from this
`pipeline/` directory) and exposed through a Streamlit app, `scripts/app.py`. See
"Full pipeline & Streamlit app" below. The notebooks in this directory remain the
course-deliverable artifacts (Problems 1 & 2 champion/challenger comparisons); the
`src/interviewlens` app is the separate, more complete productionized version built on
top of the same models.

| # | Notebook | Produces |
|---|----------|----------|
| 1 | `notebooks/01_pipeline_A_pose_estimation.ipynb` | `pose_evidence.json` |
| 2 | `notebooks/02_pipeline_B_background_analysis.ipynb` | `background_evidence.json` |
| 3 | `notebooks/03_evidence_fusion_timeline.ipynb` | `fused_evidence.json` |
| 4 | `notebooks/04_inference_only.ipynb` | Same, via `champion_inference.py` — champion-only, no training, no network downloads (bundled ONNX/`.pt` weights) |
| — | `notebooks/00_master_pipeline.ipynb` | Runs 01→02→03 in one notebook |

Notebook 2 depends on Notebook 1's output (person-region suppression). Notebook 3 depends
on both. Run in numeric order. Notebook 4 is self-contained (hand-maintained copy of the
champion-path logic from 01/02/03 — see `champion_inference.py`'s module docstring; if a
threshold or heuristic changes in one place it must be mirrored by hand in the other).

All three/four files (plus every figure/CSV each notebook produces) land in the same
**per-run** directory, `outputs/<video_stem>_<YYYYmmdd_HHMMSS>/` — see "Per-run output
directory" below.

## Full pipeline & Streamlit app (repo root, `src/interviewlens/`)

The productionized pipeline lives outside `pipeline/`, at the repo root:

```
interview_lens/                 # repo root (parent of this pipeline/ dir)
├── src/interviewlens/
│   ├── video_pipeline/         # pose estimation, keypoints, temporal windows, signal detection
│   ├── audio_pipeline/         # capture, real ASR (faster-whisper), post-processing, delivery analytics
│   ├── reasoning/               # evidence fusion, LLM reasoning (Ollama), evidence validation
│   ├── reporting/               # coaching report, timeline visualization
│   ├── orchestration/           # wires all subsystems together (pipeline.py)
│   └── api/                     # FastAPI server
├── scripts/app.py               # Streamlit UI — upload a video, get a coaching report
└── tests/                       # pytest suite (test_audio_pipeline, test_reasoning, test_reporting, test_video_pipeline)
```

**Two Python environments, neither has everything on its own — this trips people up:**

- `cv_env` (`/home/arcanegus/MSADS_/advanced_cv_31023/cv_env/`) — has `cv2`,
  `faster-whisper`, `streamlit`, `ultralytics`, etc., but does **not** have `interviewlens`
  installed (no `pip` in this env either).
- `.venv` (repo root) — has `interviewlens` installed (editable) so `import interviewlens`
  works, but is **missing `cv2`** (opencv), so it can't run anything touching
  `video_pipeline`.

To run the Streamlit app, use `cv_env` with `src/` added to `PYTHONPATH` explicitly
(no editable install needed that way):

```bash
cd <repo root>
PYTHONPATH=src /home/arcanegus/MSADS_/advanced_cv_31023/cv_env/bin/streamlit run scripts/app.py
```

To run the test suite (pure-Python subsystems only, no `cv2` needed by most of them),
`.venv` is sufficient:

```bash
cd <repo root>
.venv/bin/python -m pytest -q
```

Ollama must be running locally (`ollama serve`, model `nemotron-mini` pulled) for real
LLM reasoning; the reasoner falls back to a deterministic, evidence-grounded mock when
Ollama is unreachable so the pipeline never hard-blocks on it (see
`src/interviewlens/reasoning/llm_reasoning.py`).

## Known gotchas (`src/interviewlens` app, not the notebooks)

- **Audio VAD fragmentation**: `audio_pipeline/preprocessing.py::detect_speech_segments`
  is a placeholder energy-based VAD (`TODO(Person B): replace with webrtcvad /
  silero-vad`). It now bridges silence gaps < 300ms and drops runs < 150ms — without
  that merging step, real (noisy) audio gets chopped into dozens of tiny segments, each
  paying faster-whisper's ~1-2s fixed per-call overhead on CPU, which reads as the
  Streamlit app "hanging" at Stage 5/6. If VAD logic changes again, re-verify segment
  count and Stage 5 wall-clock time on a real video, not just unit tests.
- **LLM JSON nulls**: `reasoning/llm_reasoning.py::_coerce_str_list` drops `null`/empty
  entries from the LLM's JSON arrays instead of stringifying them — small local models
  (nemotron-mini) sometimes pad `observations`/`suggestions` arrays with `null`, and
  `str(None)` used to leak literal `"None"` cards into the coaching report UI.
- **Coaching feedback intensity**: both the live-LLM system prompt and the offline mock
  fallback (`_mock_reasoning`) scale suggestion specificity with evidence volume — a
  single brief signal gets a light note, a recurring/high-duration signal gets its
  frequency named explicitly plus a concrete practice drill. Keep both paths in sync if
  you touch one (mock is what actually renders whenever Ollama is unreachable).

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
    ├── shared_video.py      # single-source-of-truth video loader + per-run output dir
    ├── data/                # downloaded dataset subsets + demo video
    ├── outputs/
    │   ├── .current_run             # points to this run's directory, below
    │   └── <video_stem>_<timestamp>/  # one directory per pipeline run (see below)
    │       ├── pose_evidence.json
    │       ├── background_evidence.json
    │       ├── fused_evidence.json
    │       └── *.png, *.csv           # figures, eval tables for that run
    └── saved_models/        # fine-tuned challenger weights (shared across runs)
```

## Demo video

All three notebooks operate on the same video, `notebooks/data/demo_kitchen.mp4` —
17.56 s, 25 fps, 3840×2160, single person (kitchen, using a laptop). Source:
`videos/5983740-uhd_3840_2160_25fps.mp4` (Pexels, free-to-use — no license TODO, unlike
the prior clip). Adopted in place of the original talking-head interview clip
(`notebooks/data/demo_interview_archived_talking_head.mp4`, itself trimmed from
`videos/Online Webcam Job Interview Tips.mp4` to remove 4 title-card slides — kept for
reference) after a champion-only test showed the interview clip's tight close-up crop
left almost no background visible (<10% track persistence in Pipeline B), while this
kitchen clip gave 100% track persistence with zero misclassified detections (laptop +
2 cabinets, all correct on visual inspection). Using one consistent video across all
three notebooks is what lets Notebook 3's fused timeline show real, matching timestamps.

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

### Per-run output directory

Every pipeline run writes into its own `outputs/<video_stem>_<YYYYmmdd_HHMMSS>/`
directory instead of a single shared `outputs/` — the old layout meant re-running the
pipeline against a new video (or re-running the same video after a code change) silently
overwrote the previous run's evidence JSONs, figures, and eval tables, with no record
that anything had changed underneath you.

`notebooks/shared_video.py` provides two functions, mirroring the checksum-guard
pattern above:

- **`start_run_dir(video_path, output_root)`** — called once, by **Notebook 1** (or the
  master notebook), to allocate a fresh timestamped directory and record it in
  `outputs/.current_run`.
- **`current_run_dir(output_root)`** — called by **Notebooks 2 and 3** to resolve the
  *same* directory Notebook 1 just allocated. Raises loudly if Notebook 1 hasn't run yet
  (no `.current_run` pointer) rather than silently falling back to `outputs/` itself.

Practical effect: `OUTPUT_DIR` is rebound partway through Notebook 1/2/3's setup cell
(right after the video is loaded) from the static `outputs/` root to that run's
subdirectory — every `OUTPUT_DIR / "..."` write later in the notebook (evidence JSON,
EDA plots, training curves, comparison tables, sample-frame images) automatically lands
in the run directory with no further changes needed downstream. **Run the three
notebooks in the same sitting, in order (01 → 02 → 03)** — Notebook 1 starts the run,
Notebooks 2 and 3 join it; running Notebook 1 twice before running 2/3 moves
`.current_run` to a second, empty directory and 2/3 will not find Notebook 1's output.

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
  assertions (this rule is enforced formally by `src/interviewlens/reasoning/
  evidence_validation.py`, but the JSON schemas here should already satisfy it).
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
