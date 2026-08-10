# Using a Different Demo Video

Notebooks 01, 02, and 03 all analyze the **same source video**, so results stay
consistent across the fused timeline. This doc explains what's required if you
want to swap in your own clip instead of the current demo video.

## 1. What the pipeline does with the video

- **Notebook 01** (pose estimation) runs pose keypoint extraction + framing
  metrics on the video and exports `outputs/pose_evidence.json`.
- **Notebook 02** (background analysis) uses that person bounding box to
  suppress the subject and analyzes the remaining background, exporting
  `outputs/background_evidence.json`.
- **Notebook 03** (evidence fusion) combines both into a single timeline.

Because all three notebooks depend on one shared file, the video is not
hardcoded per-notebook — it's resolved once via `notebooks/shared_video.py`,
which checksum-verifies it against `configs/config.yaml`.

## 2. Video requirements

| Requirement | Why |
|---|---|
| Single person, talking to camera, webcam-style framing | The challenger pose model (SimpleBaseline) uses the whole frame as its crop, assuming the subject already fills and centers it — there's no separate person detector upstream |
| Not a tight face close-up — torso and some background visible | A too-tight crop caused <10% background-tracking persistence in earlier testing |
| Background with fixed, recognizable objects (furniture, laptop, etc.) | Notebook 02 needs something stable to track |
| Static camera, decent lighting | Reduces noise in keypoint and object detection |
| `.mp4` format, short clips are fine (15-30s) | No need for a long clip to exercise the pipeline |
| Free-to-use license (Pexels/Pixabay etc.) | Required if the project is submitted for coursework |

## 3. Steps to swap the video

**Step 1 — Add the file**

```
pipeline/notebooks/data/your_video.mp4
```

**Step 2 — Compute its checksum**

```bash
sha256sum pipeline/notebooks/data/your_video.mp4
```

**Step 3 — Update `pipeline/configs/config.yaml`**

```yaml
demo_video:
  filename: your_video.mp4
  sha256: <hash from step 2>
  source: >
    Brief note on where the video came from and why it was chosen.
  duration_s: <duration in seconds>
```

This step is mandatory. `shared_video.py` verifies the file against this hash
before any notebook is allowed to run. If the file and hash don't match, the
notebooks fail loudly on purpose instead of running against out-of-sync data —
that's intentional, not a bug.

**Step 4 — Run the notebooks in order**

```
01_pipeline_A_pose_estimation.ipynb      -> outputs/pose_evidence.json
02_pipeline_B_background_analysis.ipynb  -> outputs/background_evidence.json
03_evidence_fusion_timeline.ipynb        -> outputs/fused_evidence.json
```

They must run in this order — 02 and 03 depend on outputs from earlier notebooks.

**Step 5 — Sanity-check the result**

Notebook 01 ends with a cell that draws the pose skeleton over sample frames —
confirm the keypoints look correctly placed. If Notebook 02's background
tracking persistence is poor, the framing is likely too tight; try a wider shot.

## 4. TL;DR

No code changes are needed to switch videos — only the `.mp4` file and the
three fields in `config.yaml` (`filename`, `sha256`, `duration_s`). Everything
else (models, notebook logic) stays the same.
