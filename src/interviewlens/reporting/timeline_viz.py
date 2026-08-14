"""Timeline visualization helper — Person D.

Renders the CoachingReport.timeline as a simple matplotlib strip chart
(swap for a proper front-end component later; this is enough for the
demo script and for embedding a PNG in an exported report).
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from interviewlens.common.schemas import CoachingReport

COLORS = {
    "repetitive_hand_movement": "tab:orange",
    "frequent_posture_shifting": "tab:purple",
    "hand_to_face_activity": "tab:red",
    "long_pause": "tab:blue",
}


def render_timeline(report: CoachingReport, out_path: str | None = None):
    fig, ax = plt.subplots(figsize=(10, 2))

    for event in report.timeline:
        color = COLORS.get(event["label"], "gray")
        ax.axvline(event["start_s"], color=color, linewidth=2)
        ax.text(
            event["start_s"], 1.05, event["label"].replace("_", " "),
            rotation=90, fontsize=7, va="bottom", ha="center", color=color,
        )

    ax.set_xlim(0, max(report.duration_s, 1))
    ax.set_yticks([])
    ax.set_xlabel("Time (s)")
    ax.set_title("Response Timeline")

    fig.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=150)
    return fig
