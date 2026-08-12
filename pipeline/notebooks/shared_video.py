"""Single source of truth for which demo video every InterviewLens notebook analyzes,
and for which per-run output directory they all write into.

Both Pipeline A (pose) and Pipeline B (background) must observe the exact same footage
for the fused timeline in Notebook 3 to make sense. Each notebook calls
`load_verified_video_path()` instead of hardcoding `DATA_DIR / "demo_interview.mp4"`, so
a video swap that updates the file but not `configs/config.yaml` (or vice versa) fails
loudly at the top of the notebook instead of silently producing evidence from two
different videos. See CLAUDE.md > "Shared demo video" for the full rationale.

Similarly, each *run* of the pipeline against a video gets its own timestamped output
directory (`outputs/<video_stem>_<YYYYmmdd_HHMMSS>/`) instead of every notebook writing
into a single shared `outputs/`, which silently overwrote the previous run's evidence on
every re-run. Notebook 1 (or the master notebook) calls `start_run_dir()` once to
allocate that directory and record it as the current run; Notebooks 2 and 3 call
`current_run_dir()` to resolve the same directory Notebook 1 just created, the same
"single source of truth, fail loudly on mismatch" pattern as the checksum guard above.
"""
import hashlib
from datetime import datetime
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path("../configs/config.yaml")
CURRENT_RUN_POINTER_NAME = ".current_run"


def load_verified_video_path(data_dir: Path, config_path: Path = DEFAULT_CONFIG_PATH) -> Path:
    """Resolve the demo video path from config.yaml and verify its SHA256 checksum.

    Raises AssertionError (with a corrective message) if the file is missing or its
    content no longer matches the checksum recorded in config.yaml.
    """
    config = yaml.safe_load(config_path.read_text())
    video_cfg = config["demo_video"]
    video_path = data_dir / video_cfg["filename"]
    assert video_path.exists(), f"Demo video not found at {video_path}"

    actual_sha256 = hashlib.sha256(video_path.read_bytes()).hexdigest()
    expected_sha256 = video_cfg["sha256"]
    assert actual_sha256 == expected_sha256, (
        f"{video_path} does not match the checksum recorded in {config_path} "
        f"(expected {expected_sha256[:12]}..., got {actual_sha256[:12]}...). "
        "If you intentionally replaced the demo video, update demo_video.sha256 in "
        "configs/config.yaml, then re-run every notebook in order (01 -> 02 -> 03) so "
        "all evidence JSONs are regenerated against the same file."
    )
    return video_path


def start_run_dir(video_path: Path, output_root: Path) -> Path:
    """Allocate a fresh `<output_root>/<video_stem>_<timestamp>/` directory for one full
    pipeline run and record it in `<output_root>/.current_run` so Notebooks 2 and 3 (run
    afterward, per CLAUDE.md's "01 -> 02 -> 03" order) resolve the same directory
    without independently re-deriving the timestamp -- two notebooks computing their own
    `datetime.now()` would almost never agree on one.

    Call this from Notebook 1 (or the master notebook) only -- Notebooks 2 and 3 must
    call `current_run_dir()` instead, or they'd each allocate their own new (empty) run.
    """
    output_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / f"{video_path.stem}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (output_root / CURRENT_RUN_POINTER_NAME).write_text(run_dir.name)
    return run_dir


def current_run_dir(output_root: Path) -> Path:
    """Resolve the run directory Notebook 1 (or the master notebook) most recently
    allocated via `start_run_dir()`. Raises loudly if no run has been started yet or the
    recorded directory is missing, instead of silently falling back to `output_root`
    itself and mixing this run's evidence with a stale/different run's.
    """
    pointer = output_root / CURRENT_RUN_POINTER_NAME
    assert pointer.exists(), (
        f"No current run recorded at {pointer}. Run Notebook 1 (or the master "
        "notebook) first -- it allocates the per-run output directory that this "
        "notebook reads from and writes into."
    )
    run_dir = output_root / pointer.read_text().strip()
    assert run_dir.exists(), (
        f"Recorded run directory {run_dir} no longer exists. Re-run Notebook 1 (or the "
        "master notebook) to start a fresh run."
    )
    return run_dir
