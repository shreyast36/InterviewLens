"""Quick end-to-end smoke test: runs the full InterviewLens pipeline in
demo_mode (synthetic inputs, mocked models) and prints the resulting
coaching report as JSON.

Usage:
    python scripts/run_demo.py
"""
from __future__ import annotations

import json
from dataclasses import asdict

from interviewlens.orchestration.pipeline import run_pipeline


def main() -> None:
    report = run_pipeline(question="Tell me about a time you resolved a conflict at work.")
    print(json.dumps(asdict(report), indent=2, default=str))


if __name__ == "__main__":
    main()
