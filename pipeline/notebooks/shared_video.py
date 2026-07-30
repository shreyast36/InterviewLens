"""Single source of truth for which demo video every InterviewLens notebook analyzes.

Both Pipeline A (pose) and Pipeline B (background) must observe the exact same footage
for the fused timeline in Notebook 3 to make sense. Each notebook calls
`load_verified_video_path()` instead of hardcoding `DATA_DIR / "demo_interview.mp4"`, so
a video swap that updates the file but not `configs/config.yaml` (or vice versa) fails
loudly at the top of the notebook instead of silently producing evidence from two
different videos. See CLAUDE.md > "Shared demo video" for the full rationale.
"""
import hashlib
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path("../configs/config.yaml")


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
