"""InterviewLens — Streamlit coaching interface.

Run from the repo root:
    streamlit run scripts/app.py
"""
from __future__ import annotations

import html
import os
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="InterviewLens · AI Interview Coach",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ─── base ─────────────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', system-ui, sans-serif;
    background: #ffffff;
    color: #1e293b;
}

[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed; inset: 0; z-index: -1;
    background:
        radial-gradient(ellipse 80% 60% at 10%  15%, rgba(34,211,238,.06)  0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 90%  85%, rgba(129,140,248,.06) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 50%  50%, rgba(236,72,153,.03)  0%, transparent 50%),
        #ffffff;
}

[data-testid="stHeader"]  { background: transparent !important; }
.block-container          { padding-top: 1.8rem !important; max-width: 1400px; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* ─── sidebar ───────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] > div:first-child {
    background: rgba(255,255,255,.95);
    border-right: 1px solid rgba(15,23,42,.08);
    backdrop-filter: blur(20px);
}
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }
/* Confirmed via DevTools: the file uploader's icon is
   <span data-testid="stIconMaterial">upload</span> -- Material Symbols renders icons
   via font ligatures (the literal word "upload" is substituted for the glyph only
   when the element's font-family is actually the Material Symbols font). The blanket
   `[data-testid="stSidebar"] *` rule above forces Inter onto it too, breaking that
   substitution, so the raw ligature word renders as plain text right next to the
   "Upload" button label ("uploadUpload"). It's purely decorative, so just hide it by
   its exact testid instead of trying to restore the right icon font. */
[data-testid="stFileUploaderDropzone"] [data-testid="stIconMaterial"] {
    display: none !important;
}

/* ─── hero title ─────────────────────────────────────────────────────────────── */
@keyframes gradient-pan {
    0%   { background-position: 0%   50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0%   50%; }
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(2.2rem, 4vw, 3.4rem);
    font-weight: 700;
    letter-spacing: -.02em;
    background: linear-gradient(110deg, #22d3ee, #818cf8, #ec4899, #22d3ee);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient-pan 6s ease infinite;
    line-height: 1.1;
    margin: 0;
}
.hero-sub {
    color: #475569;
    font-size: .95rem;
    margin-top: .5rem;
    letter-spacing: .01em;
}
.hero-divider {
    height: 1px;
    background: linear-gradient(90deg, rgba(34,211,238,.4), rgba(129,140,248,.4), transparent);
    margin: 1.4rem 0 1.8rem;
    border: none;
}

/* ─── metric cards ───────────────────────────────────────────────────────────── */
@keyframes card-in {
    from { opacity:0; transform: translateY(14px); }
    to   { opacity:1; transform: translateY(0);    }
}
.il-card {
    position: relative;
    background: rgba(15,23,42,.03);
    border-radius: 16px;
    padding: 1.4rem 1rem 1.1rem;
    text-align: center;
    overflow: hidden;
    animation: card-in .4s ease both;
    transition: transform .25s, box-shadow .25s;
}
.il-card::before {
    content: "";
    position: absolute; inset: 0;
    border-radius: 16px;
    padding: 1px;
    background: linear-gradient(135deg, rgba(34,211,238,.35), rgba(129,140,248,.2), rgba(236,72,153,.15));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor; mask-composite: exclude;
    pointer-events: none;
}
.il-card::after {
    content: "";
    position: absolute; top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at center, rgba(34,211,238,.04) 0%, transparent 60%);
    pointer-events: none;
}
.il-card:hover { transform: translateY(-4px);
                 box-shadow: 0 12px 40px rgba(34,211,238,.12); }
.il-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.1rem; font-weight: 700;
    background: linear-gradient(135deg, #1e293b, #0891b2);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1.1; display: block;
}
.il-label {
    font-size: .62rem; font-weight: 600; letter-spacing: .12em;
    text-transform: uppercase; color: #475569; margin-top: .35rem;
}
.il-sub { font-size: .63rem; color: rgba(34,211,238,.7); margin-top: .15rem; }

/* ─── section header ─────────────────────────────────────────────────────────── */
.sec-hdr {
    display: flex; align-items: center; gap: .6rem;
    margin: 1.6rem 0 1rem;
}
.sec-hdr-icon {
    width: 28px; height: 28px; border-radius: 8px;
    background: linear-gradient(135deg, rgba(34,211,238,.2), rgba(129,140,248,.15));
    border: 1px solid rgba(34,211,238,.25);
    display: flex; align-items: center; justify-content: center;
    font-size: .9rem; flex-shrink: 0;
}
.sec-hdr-text {
    font-size: .65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .14em; color: #64748b;
}
.sec-hdr-line { flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(34,211,238,.15), transparent); }

/* ─── coaching cards ─────────────────────────────────────────────────────────── */
@keyframes slide-in {
    from { opacity:0; transform: translateX(-8px); }
    to   { opacity:1; transform: translateX(0); }
}
.ccard {
    position: relative;
    border-radius: 12px;
    padding: .95rem 1.15rem .95rem 1.4rem;
    margin-bottom: .55rem;
    font-size: .84rem; color: #475569;
    line-height: 1.65;
    overflow: hidden;
    animation: slide-in .35s ease both;
    transition: transform .2s, color .2s;
    backdrop-filter: blur(8px);
}
.ccard:hover { transform: translateX(3px); color: #1e293b; }
.ccard::before {
    content: ""; position: absolute; left: 0; top: 0;
    width: 3px; height: 100%; border-radius: 0 2px 2px 0;
}
.ccard-obs { background: rgba(129,140,248,.08); }
.ccard-obs::before { background: linear-gradient(180deg, #818cf8, #a78bfa); }
.ccard-imp { background: rgba(249,115,22,.08);  }
.ccard-imp::before { background: linear-gradient(180deg, #f97316, #fb923c); }
.ccard-str { background: rgba(34,211,238,.08);  }
.ccard-str::before { background: linear-gradient(180deg, #22d3ee, #67e8f9); }

.ccard-col-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: .8rem; font-weight: 600; letter-spacing: .04em;
    margin-bottom: .7rem; display: flex; align-items: center; gap: .5rem;
}
.ccard-col-title-obs { color: #818cf8; }
.ccard-col-title-imp { color: #f97316; }
.ccard-col-title-str { color: #22d3ee; }

/* ─── feature cards ──────────────────────────────────────────────────────────── */
.feat {
    position: relative; border-radius: 18px;
    padding: 1.6rem 1.3rem;
    overflow: hidden;
    transition: transform .3s, box-shadow .3s;
    cursor: default;
}
.feat::before {
    content: ""; position: absolute; inset: 0; border-radius: 18px; padding: 1px;
    background: linear-gradient(135deg, rgba(15,23,42,.10), rgba(15,23,42,.02));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none;
}
.feat-bg0 { background: linear-gradient(135deg, rgba(34,211,238,.08), rgba(6,182,212,.04)); }
.feat-bg1 { background: linear-gradient(135deg, rgba(129,140,248,.08), rgba(99,102,241,.04)); }
.feat-bg2 { background: linear-gradient(135deg, rgba(236,72,153,.08), rgba(244,114,182,.04)); }
.feat-bg3 { background: linear-gradient(135deg, rgba(251,191,36,.08), rgba(245,158,11,.04)); }
.feat:hover { transform: translateY(-5px) scale(1.01);
              box-shadow: 0 20px 50px rgba(15,23,42,.12); }
.feat-icon  { font-size: 2rem; margin-bottom: .7rem; }
.feat-title { font-family: 'Space Grotesk', sans-serif; font-size: .92rem;
              font-weight: 600; color: #1e293b; margin-bottom: .4rem; }
.feat-body  { font-size: .78rem; color: #64748b; line-height: 1.6; }

/* ─── reliability label (plain text, no chip/pill) ──────────────────────────── */
.rlabel {
    display: inline-flex; align-items: center; gap: .45rem;
    font-size: .78rem; font-weight: 600; letter-spacing: .02em;
}
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:.3} }
.rdot { width:7px; height:7px; border-radius:50%;
        display:inline-block; animation: pulse-dot 2s infinite; }

/* ─── primary button ─────────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #22d3ee, #818cf8) !important;
    border: none !important; color: #050c18 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important; font-size: .88rem !important;
    letter-spacing: .04em !important; border-radius: 12px !important;
    height: 2.7rem !important;
    box-shadow: 0 4px 20px rgba(34,211,238,.25) !important;
    transition: opacity .2s, transform .15s, box-shadow .2s !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: .9 !important; transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(34,211,238,.35) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(15,23,42,.03) !important;
    border: 1px solid rgba(15,23,42,.1) !important;
    color: #475569 !important; border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ─── sidebar label ──────────────────────────────────────────────────────────── */
.sb-label {
    font-size: .58rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .13em; color: #334155; margin-bottom: .7rem;
    padding-bottom: .5rem; border-bottom: 1px solid rgba(15,23,42,.08);
}

/* ─── file uploader ──────────────────────────────────────────────────────────── */
/* Only touch text wrapping here -- an earlier attempt also forced flex-wrap/height
   on the dropzone itself and that broke the "Browse files" button's own internal
   layout (it rendered doubled/overlapping text). Streamlit's default flex row for
   [icon | instructions | button] is left alone; just let the instructions text
   (and the "200MB per file..." limit line under it) wrap and shrink instead of
   overflowing under the button in the narrow sidebar column. */
[data-testid="stFileUploaderDropzoneInstructions"] {
    min-width: 0;
    flex: 1 1 auto;
}
[data-testid="stFileUploaderDropzoneInstructions"] div,
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    overflow-wrap: break-word;
    white-space: normal !important;
}

/* ─── ollama box ─────────────────────────────────────────────────────────────── */
.ollama-box {
    border-radius: 12px; padding: .7rem .9rem;
    background: rgba(15,23,42,.025);
    border: 1px solid rgba(15,23,42,.08);
    margin-top: .2rem;
}
.ollama-key { font-size: .56rem; text-transform: uppercase;
              letter-spacing: .1em; color: #334155; margin-bottom: .4rem; }
.ollama-row { display:flex; align-items:center; gap:.45rem; margin-bottom:.3rem; }
.ollama-status { font-size: .73rem; font-weight: 600; }
.ollama-detail { font-size: .63rem; color: #334155; line-height: 1.4; }

/* ─── divider ────────────────────────────────────────────────────────────────── */
.glow-divider {
    height: 1px; border: none; margin: 1.6rem 0;
    background: linear-gradient(90deg,
        transparent,
        rgba(34,211,238,.3) 20%,
        rgba(129,140,248,.3) 50%,
        rgba(236,72,153,.2) 80%,
        transparent);
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
_SIG_CLR: dict[str, str] = {
    "repetitive_hand_movement":  "#ef4444",
    "frequent_posture_shifting": "#f97316",
    "hand_to_face_activity":     "#eab308",
    "headroom_too_loose":        "#8b5cf6",
    "off_center":                "#06b6d4",
    "tilted":                    "#ec4899",
    "background_distracting":    "#64748b",
    "background_mild":           "#94a3b8",
    "hands_near_face":           "#f43f5e",
    "self_grooming":             "#fb7185",
    "arms_crossed":              "#a855f7",
    "hands_not_visible":         "#7c3aed",
    "head_drop":                 "#0ea5e9",
    "shoulders_raised":          "#38bdf8",
    "head_turned_away":          "#34d399",
    "looking_down":              "#6ee7b7",
    "head_tilt":                 "#fbbf24",
    "body_lean":                 "#f59e0b",
    "leaning_in":                "#10b981",
    "leaning_out":               "#059669",
    "fidgeting":                 "#ff6b6b",
    "frozen":                    "#a8a29e",
    "sudden_movement":           "#dc2626",
    "swaying":                   "#c084fc",
    "nodding":                   "#86efac",
    "unstable_tracking":         "#6b7280",
    "transient_object":          "#78716c",
    "cluttered_background":      "#57534e",
    "dominant_object":           "#44403c",
    "low_light":                 "#475569",
    "overexposed":               "#fef3c7",
    "backlit_face":              "#fde68a",
    "low_mic_level":             "#fdba74",
    "intermittent_audio":        "#fca5a5",
    "long_pause":                "#22d3ee",
}

_FEATURES = [
    ("📐", "feat-bg0", "Pose Analysis",
     "RTMPose-S skeleton tracking, 17-keypoint body language detection, "
     "framing quality and background distraction."),
    ("🔊", "feat-bg1", "Speech Metrics",
     "Speaking rate, filler-word count, long pauses and delivery confidence "
     "grounded in the actual audio track."),
    ("🤖", "feat-bg2", "LLM Coaching",
     "Ollama-powered Nemotron Mini generates evidence-grounded observations "
     "and concrete, actionable suggestions."),
    ("📊", "feat-bg3", "Rich Dashboard",
     "Gantt signal timeline, reliability gauges, signal breakdown donut "
     "and coaching cards with transcript drill-down."),
]


def _clr(label: str) -> str:
    return _SIG_CLR.get(label, "#94a3b8")


# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=20)
def _ollama_status() -> tuple[bool, str]:
    try:
        import ollama  # noqa: PLC0415
        result = ollama.Client().list()
        models = (
            [m.get("model", "?") for m in result.get("models", [])]
            if isinstance(result, dict)
            else [getattr(m, "model", str(m)) for m in getattr(result, "models", [])]
        )
        return True, " · ".join(models[:3]) or "server up — no models pulled"
    except ImportError:
        return False, "pip install ollama"
    except Exception:
        return False, "ollama serve  (server offline)"


def _clean_items(items: list) -> list[str]:
    """Drop None/blank entries before rendering as coaching cards. Belt-and-suspenders
    on top of llm_reasoning._coerce_str_list's own null-filtering -- this is the last
    line of defense against a stray None (or empty string) ever reaching the UI as a
    literal '<div class="ccard">None</div>' card."""
    return [str(x).strip() for x in (items or []) if x is not None and str(x).strip()]


# Which category of evidence a timeline label belongs to, so the extracted frame can
# be annotated with the thing that actually triggered the flag (skeleton for a pose
# rule, bounding box for a background object/lighting rule) instead of a bare,
# unannotated frame that leaves the viewer guessing what was flagged.
_POSE_LABELS = {
    "repetitive_hand_movement", "frequent_posture_shifting", "hand_to_face_activity",
    "headroom_too_loose", "off_center", "tilted",
    "hands_near_face", "self_grooming", "arms_crossed", "hands_not_visible",
    "head_drop", "shoulders_raised", "head_turned_away", "looking_down", "head_tilt",
    "body_lean", "leaning_in", "leaning_out", "fidgeting", "frozen", "sudden_movement",
    "swaying", "nodding", "unstable_tracking",
}
_BACKGROUND_LABELS = {
    "background_distracting", "background_mild", "transient_object",
    "cluttered_background", "dominant_object", "low_light", "overexposed",
    "backlit_face",
}

# COCO17 upper-body bones (index pairs into batch_pose.UPPER_BODY_NAMES order).
_POSE_BONES = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"),
    ("nose", "left_eye"), ("nose", "right_eye"),
    ("left_eye", "left_ear"), ("right_eye", "right_ear"),
    ("left_shoulder", "left_ear"), ("right_shoulder", "right_ear"),
]


def _nearest_by_ts(entries: list[dict], target_s: float) -> dict | None:
    if not entries:
        return None
    return min(entries, key=lambda e: abs(float(e["timestamp_s"]) - target_s))


def _draw_pose_skeleton(frame, pose_evidence: dict, start_s: float, conf_thresh: float = 0.3):
    import cv2  # noqa: PLC0415
    from interviewlens.video_pipeline.batch_pose import UPPER_BODY_NAMES  # noqa: PLC0415

    fr = _nearest_by_ts(pose_evidence.get("frames", []), start_s)
    if fr is None:
        return frame
    by_name = dict(zip(UPPER_BODY_NAMES, fr["keypoints"]))
    for a, b in _POSE_BONES:
        pa, pb = by_name.get(a), by_name.get(b)
        if pa and pb and pa[2] > conf_thresh and pb[2] > conf_thresh:
            cv2.line(frame, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])),
                      (34, 211, 238), 2, cv2.LINE_AA)
    for x, y, c in by_name.values():
        if c > conf_thresh:
            cv2.circle(frame, (int(x), int(y)), 4, (34, 211, 238), -1, cv2.LINE_AA)
            cv2.circle(frame, (int(x), int(y)), 4, (5, 12, 24), 1, cv2.LINE_AA)
    return frame


def _draw_background_boxes(frame, background_evidence: dict, start_s: float):
    import cv2  # noqa: PLC0415
    from interviewlens.video_pipeline.batch_background import (  # noqa: PLC0415
        DISPLAY_NAMES, TIER_BY_CLASS_ID,
    )

    fr = _nearest_by_ts(background_evidence.get("frames", []), start_s)
    if fr is None:
        return frame
    tier_color = {"distracting": (239, 68, 68), "mild": (234, 179, 8)}
    for det in fr.get("detections", []):
        x1, y1, x2, y2 = (int(v) for v in det["bbox_xyxy"])
        tier = TIER_BY_CLASS_ID.get(det["class_id"], "neutral")
        color = tier_color.get(tier, (129, 140, 248))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
        name = DISPLAY_NAMES[det["class_id"]] if det["class_id"] < len(DISPLAY_NAMES) else "object"
        (tw, th), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 6)), (x1 + tw + 6, y1), color, -1)
        cv2.putText(frame, name, (x1 + 3, max(12, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (5, 12, 24), 1, cv2.LINE_AA)
    return frame


def _grab_event_frames(
    video_path: str, timeline: list[dict],
    pose_evidence: dict | None = None, background_evidence: dict | None = None,
) -> list[bytes | None]:
    """Grab one JPEG-encoded frame per timeline entry, at that event's start_s, while
    the uploaded video's temp file still exists (it's deleted right after _run_video
    returns). Used both for the Gantt "click a bar -> see the frame" popup and for the
    PDF's per-category flag images. Returns a list aligned 1:1 with `timeline`; an
    unreadable/out-of-range timestamp yields None at that position rather than raising,
    so one bad event doesn't blow up the whole report.

    Each frame is annotated with what actually triggered its flag -- the pose
    skeleton for a pose/framing rule, or the detected object's bounding box for a
    background/lighting rule -- rather than handed back as a bare, unannotated frame.
    """
    import cv2  # noqa: PLC0415

    frames: list[bytes | None] = [None] * len(timeline)
    cap = cv2.VideoCapture(str(video_path))
    try:
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 0
        if video_fps <= 0:
            return frames
        for i, ev in enumerate(timeline):
            start_s = float(ev["start_s"])
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_s * video_fps))
            ok, frame = cap.read()
            if not ok:
                continue
            label = ev.get("label", "")
            if label in _POSE_LABELS and pose_evidence:
                frame = _draw_pose_skeleton(frame, pose_evidence, start_s)
            elif label in _BACKGROUND_LABELS and background_evidence:
                frame = _draw_background_boxes(frame, background_evidence, start_s)
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ok:
                frames[i] = buf.tobytes()
    finally:
        cap.release()
    return frames


def _grab_background_snapshot(video_path: str, background_evidence: dict | None) -> bytes | None:
    """One representative background-detection frame for the PDF, independent of
    whether any background *flag* actually fired -- the "Flagged Moments" gallery in
    _build_pdf only ever shows a category once it's been flagged, so a clean clip with
    zero distracting/cluttered/lighting events produced a report with a pose skeleton
    example but no background-detection image at all, even though background
    detection did run. Picks the sampled frame with the most tracked objects (the
    most informative one to show); falls back to the first sampled frame if none has
    any detections.
    """
    import cv2  # noqa: PLC0415

    if not background_evidence:
        return None
    frames = background_evidence.get("frames", [])
    if not frames:
        return None
    best = max(frames, key=lambda f: len(f.get("detections", [])))
    start_s = float(best["timestamp_s"])

    cap = cv2.VideoCapture(str(video_path))
    try:
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 0
        if video_fps <= 0:
            return None
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_s * video_fps))
        ok, frame = cap.read()
        if not ok:
            return None
        frame = _draw_background_boxes(frame, background_evidence, start_s)
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return buf.tobytes() if ok else None
    finally:
        cap.release()


# ══════════════════════════════════════════════════════════════════════════════
# PLOTLY CHARTS
# ══════════════════════════════════════════════════════════════════════════════
_PLOTLY_BASE = dict(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#475569"))


def _gauge(value_0_1: float, title: str) -> go.Figure:
    pct = round(min(max(value_0_1, 0.0), 1.0) * 100, 1)
    clr = "#22d3ee" if pct >= 75 else "#eab308" if pct >= 50 else "#ef4444"
    glow = f"rgba({int(clr[1:3],16)},{int(clr[3:5],16)},{int(clr[5:7],16)},.15)"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number=dict(suffix="%", font=dict(size=30, color="#1e293b",
                    family="Space Grotesk, sans-serif")),
        title=dict(text=title, font=dict(size=11, color="#475569")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#0f172a",
                      tickfont=dict(color="#334155", size=9), nticks=6),
            bar=dict(color=clr, thickness=0.2),
            bgcolor=glow,
            bordercolor="rgba(0,0,0,0)",
            steps=[
                dict(range=[0,  50], color="rgba(239,68,68,.05)"),
                dict(range=[50, 75], color="rgba(234,179,8,.05)"),
                dict(range=[75,100], color="rgba(34,211,238,.05)"),
            ],
            threshold=dict(line=dict(color="rgba(129,140,248,.8)", width=2),
                           thickness=0.85, value=75),
        ),
    ))
    fig.update_layout(height=230, margin=dict(l=20, r=20, t=46, b=10),
                      **_PLOTLY_BASE)
    return fig


def _donut(timeline: list[dict]) -> go.Figure | None:
    if not timeline:
        return None
    counts: dict[str, int] = {}
    for ev in timeline:
        counts[ev["label"]] = counts.get(ev["label"], 0) + 1
    labels = list(counts)
    fig = go.Figure(go.Pie(
        labels=[l.replace("_", " ").title() for l in labels],
        values=[counts[l] for l in labels],
        hole=0.65,
        marker=dict(colors=[_clr(l) for l in labels],
                    line=dict(color="rgba(5,12,24,.6)", width=2)),
        textfont=dict(size=10, color="#1e293b"),
        hovertemplate="<b>%{label}</b><br>%{value} events · %{percent}<extra></extra>",
    ))
    fig.update_layout(
        height=230, margin=dict(l=5, r=5, t=10, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9), x=1.02),
        annotations=[dict(text="signals", x=0.5, y=0.5,
                          font=dict(size=10, color="#334155",
                          family="Inter, sans-serif"), showarrow=False)],
        **_PLOTLY_BASE,
    )
    return fig


def _timeline(timeline: list[dict], duration_s: float) -> go.Figure | None:
    """One bar per real event span (start_s..end_s), not a reconstructed guess --
    the old version treated `timeline` as a flat sequence of same-time points and
    inferred each bar's end from wherever the *next* point (of any label) fell,
    which silently mangled anything that overlapped in time. `customdata` carries
    each bar's original index into `timeline` so a click on it can be resolved
    back to the exact event (see the on_select handler in _dashboard)."""
    if not timeline:
        return None
    entries = sorted(enumerate(timeline), key=lambda p: p[1]["start_s"])

    labels  = list(dict.fromkeys(e["label"] for _, e in entries))
    y_map   = {l: i for i, l in enumerate(labels)}
    plotted: set[str] = set()
    fig = go.Figure()

    for orig_idx, ev in entries:
        label = ev["label"]
        start = float(ev["start_s"])
        end   = max(float(ev["end_s"]), start + 0.15)  # keep near-instant events visible
        c = _clr(label)
        # glow layer
        fig.add_trace(go.Bar(
            x=[end - start], y=[y_map[label]], base=[start],
            orientation="h",
            marker=dict(color=c, opacity=0.15),
            customdata=[[orig_idx]],
            showlegend=False, hoverinfo="skip",
            width=0.85,
        ))
        # main bar (clickable)
        fig.add_trace(go.Bar(
            x=[end - start], y=[y_map[label]], base=[start],
            orientation="h",
            marker=dict(color=c, opacity=0.88,
                        line=dict(color="rgba(0,0,0,.4)", width=1)),
            name=label.replace("_", " ").title(),
            showlegend=label not in plotted,
            width=0.55,
            customdata=[[orig_idx]],
            hovertemplate=(
                f"<b>{label.replace('_',' ').title()}</b><br>"
                f"⏱ {start:.1f}s – {end:.1f}s  ({end-start:.1f}s)<br>"
                f"<i>Click to view the frame</i><extra></extra>"
            ),
        ))
        plotted.add(label)

    ax = dict(gridcolor="rgba(15,23,42,.06)", zeroline=False,
              color="#334155", tickfont=dict(size=10))
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(title="Time (s)", range=[0, duration_s], **ax),
        yaxis=dict(tickvals=list(y_map.values()),
                   ticktext=[l.replace("_", " ").title() for l in labels], **ax),
        height=max(190, 60 + 46 * len(labels)),
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(15,23,42,.015)",
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#64748b", size=9),
                    orientation="h", yanchor="bottom", y=1.01,
                    xanchor="right", x=1),
        **_PLOTLY_BASE,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# HTML SNIPPETS
# ══════════════════════════════════════════════════════════════════════════════
def _metric(val: str, label: str, sub: str = "") -> str:
    s = f'<div class="il-sub">{sub}</div>' if sub else ""
    return (f'<div class="il-card">'
            f'<span class="il-val">{val}</span>'
            f'<div class="il-label">{label}</div>{s}</div>')


def _sec(icon: str, title: str) -> str:
    return (f'<div class="sec-hdr">'
            f'<div class="sec-hdr-icon">{icon}</div>'
            f'<span class="sec-hdr-text">{title}</span>'
            f'<div class="sec-hdr-line"></div></div>')


def _ccard(text: str, kind: str) -> str:
    return f'<div class="ccard ccard-{kind}">{html.escape(str(text))}</div>'


def _col_title(icon: str, text: str, kind: str) -> str:
    return (f'<div class="ccard-col-title ccard-col-title-{kind}">'
            f'{icon} {text}</div>')


def _badge(score: float) -> str:
    clr   = "#0891b2" if score >= 0.75 else "#b45309" if score >= 0.5 else "#dc2626"
    dot   = "#22c55e" if score >= 0.75 else "#eab308" if score >= 0.5 else "#ef4444"
    label = ("High confidence" if score >= 0.75
             else "Moderate" if score >= 0.5 else "Low confidence")
    return (f'<span class="rlabel" style="color:{clr}">'
            f'<span class="rdot" style="background:{dot}"></span>'
            f'{label} &nbsp;·&nbsp; {score:.0%}</span>')


# ══════════════════════════════════════════════════════════════════════════════
# CACHED MODEL LOADERS
# ══════════════════════════════════════════════════════════════════════════════
# Heavy model objects are cached per Streamlit session so repeated analyses in
# the same session don't reload weights from disk (RTMPose / YOLO-World are
# already module-level cached inside their own subsystems; ASR and the LLM
# client were not, so every "Run Analysis" click reloaded Whisper).
@st.cache_resource(show_spinner=False)
def _get_asr_model(model_name: str):
    from interviewlens.audio_pipeline.asr import build_asr_model  # noqa: PLC0415
    return build_asr_model(model_name)


@st.cache_resource(show_spinner=False)
def _get_reasoner(model_name: str, max_tokens: int, temperature: float):
    from interviewlens.reasoning.llm_reasoning import LLMReasoner  # noqa: PLC0415
    return LLMReasoner(model_name=model_name, max_tokens=max_tokens, temperature=temperature)


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE RUNNER
# ══════════════════════════════════════════════════════════════════════════════
def _run_video(question: str, video_bytes: bytes, suffix: str) -> tuple[dict, dict]:
    """Run the real pipeline on an uploaded video with per-stage status updates.

    Every stage operates on the uploaded video's real data — pose from its
    actual frames, background from its actual frames, transcript and speaking
    metrics from its actual audio track (decoded via ffmpeg, transcribed via
    faster-whisper). No synthetic placeholders anywhere in this path.
    """
    import gc
    from interviewlens.audio_pipeline.batch_audio_quality import (
        extract_audio_quality_evidence, extract_audio_samples,
    )
    from interviewlens.audio_pipeline.delivery_analytics import compute_metrics
    from interviewlens.audio_pipeline.postprocessing import normalize_disfluencies
    from interviewlens.audio_pipeline.preprocessing import preprocess
    from interviewlens.common.config import load_config
    from interviewlens.common.schemas import Transcript
    from interviewlens.reasoning.evidence_assembly import from_fused_evidence_json
    from interviewlens.reasoning.evidence_validation import validate
    from interviewlens.reporting.coaching_report import build_coaching_report
    from interviewlens.video_pipeline.ab_fusion import fuse_evidence
    from interviewlens.video_pipeline.batch_background import extract_background_evidence
    from interviewlens.video_pipeline.batch_pose import (
        detect_signal_events, extract_pose_evidence,
        grab_frames, valid_tracking_pct as batch_valid_tracking_pct,
    )

    cfg = load_config()
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        with st.status("🚀 Analysing uploaded video…", expanded=True) as status:

            st.write("📐 **Stage 1 / 6** — Pose estimation (RTMPose-S)…")
            pose_evidence = extract_pose_evidence(tmp_path, sample_fps=5)
            if not pose_evidence.get("frames"):
                raise ValueError(
                    "No frames decoded — check the file is a valid MP4/MOV/AVI/WebM."
                )
            pose_evidence["signal_events"] = detect_signal_events(pose_evidence)
            tracking_pct = batch_valid_tracking_pct(pose_evidence)
            st.write(f"   ✔ {len(pose_evidence['frames'])} pose frames, "
                     f"{len(pose_evidence['signal_events'])} signal events")

            st.write("🖼️ **Stage 2 / 6** — Background detection (YOLO-World-S + ByteTrack)…")
            background_evidence = extract_background_evidence(tmp_path, pose_evidence, sample_fps=3)
            st.write(f"   ✔ {len(background_evidence.get('detections', []))} background tracks")

            st.write("🔊 **Stage 3 / 6** — Audio quality analysis…")
            audio_quality_evidence = extract_audio_quality_evidence(tmp_path)
            st.write(f"   ✔ audio: {'present' if audio_quality_evidence.get('has_audio') else 'none'}, "
                     f"{len(audio_quality_evidence.get('signal_events', []))} quality events")

            st.write("🧩 **Stage 4 / 6** — A/B evidence fusion…")
            fused      = fuse_evidence(pose_evidence, background_evidence, audio_quality_evidence)
            duration_s = float(fused.get("duration_s") or 1.0)
            st.write(f"   ✔ {len(fused.get('timeline', []))} fused timestamps, {duration_s:.1f}s")

            st.write("📝 **Stage 5 / 6** — Transcribing real audio (faster-whisper) & LLM reasoning…")
            asr = _get_asr_model(cfg.audio.asr_model)
            raw_audio  = extract_audio_samples(tmp_path, sample_rate=cfg.audio.sample_rate)
            segs       = preprocess(raw_audio, cfg.audio.sample_rate) if raw_audio is not None and len(raw_audio) else []
            trans_list = [asr.transcribe(seg) for seg in segs]
            transcript = normalize_disfluencies(Transcript(
                text=" ".join(t.text for t in trans_list if t.text),
                words=[w for t in trans_list for w in t.words],
            ))
            if not segs:
                st.write("   ⚠ no usable audio track found — transcript will be empty")
            audio_metrics = compute_metrics(transcript, total_duration_s=duration_s)
            probe      = from_fused_evidence_json(fused, question=question,
                                                   transcript=transcript, audio_metrics=audio_metrics)
            all_frames = grab_frames(tmp_path, probe.selected_frames, fused["fps_fused"])
            evidence   = from_fused_evidence_json(fused, question=question,
                                                   transcript=transcript, audio_metrics=audio_metrics,
                                                   all_frames=all_frames)
            reasoner = _get_reasoner(
                cfg.reasoning.llm_model, cfg.reasoning.max_output_tokens, cfg.reasoning.temperature,
            )
            reasoning_output = reasoner.reason(evidence)

            st.write("📊 **Stage 6 / 6** — Building coaching report…")
            validation = validate(evidence, reasoning_output)
            report     = build_coaching_report(
                duration_s=duration_s, valid_tracking_pct=tracking_pct,
                audio_metrics=audio_metrics, visual_events=evidence.visual_events,
                reasoning=reasoning_output, validation=validation,
            )
            status.update(label="✅ Analysis complete!", state="complete", expanded=False)

        # Grab one frame per flagged moment now, while tmp_path still exists (it's
        # deleted in `finally` below) -- powers both the Gantt click-to-preview popup
        # and the PDF's per-category flag images.
        event_frames = _grab_event_frames(
            tmp_path, report.timeline,
            pose_evidence=pose_evidence, background_evidence=background_evidence,
        )
        background_snapshot = _grab_background_snapshot(tmp_path, background_evidence)

        return asdict(report), {
            "observations": reasoning_output.observations,
            "explanations": reasoning_output.explanations,
            "suggestions":  reasoning_output.suggestions,
            "transcript":   transcript.text,
            "event_frames": event_frames,
            "background_snapshot": background_snapshot,
            "failed_checks": validation.failed_checks,
        }

    finally:
        gc.collect()
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except PermissionError:
                pass  # Windows holds the handle briefly — OS cleans %TEMP% automatically


# ══════════════════════════════════════════════════════════════════════════════
# PDF REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def _build_pdf(data: dict, extra: dict) -> bytes:
    """Generate a professional PDF coaching report and return the raw bytes."""
    from datetime import datetime
    import io
    import unicodedata
    from fpdf import FPDF  # noqa: PLC0415

    observations = _clean_items(extra.get("observations") or data.get("strengths"))
    suggestions  = _clean_items(extra.get("suggestions")  or data.get("improvements"))
    strengths    = _clean_items(data.get("strengths"))
    transcript   = extra.get("transcript", "")
    reliability  = float(data["reliability_score"])
    timeline     = data.get("timeline", [])
    event_frames = extra.get("event_frames") or []

    # ── Colours (RGB) ────────────────────────────────────────────────────────
    C_BG_DARK   = (5,   12,  24)
    C_CYAN      = (34,  211, 238)
    C_INDIGO    = (129, 140, 248)
    C_ORANGE    = (249, 115, 22)
    C_TEXT      = (30,  41,  59)
    C_MUTED     = (100, 116, 139)
    C_WHITE     = (255, 255, 255)
    C_LIGHT_BG  = (241, 245, 249)
    C_GREEN     = (34,  197, 94)
    C_AMBER     = (234, 179, 8)
    C_RED       = (239, 68,  68)

    def rel_color(score: float):
        if score >= 0.75: return C_GREEN
        if score >= 0.50: return C_AMBER
        return C_RED

    def _pdf_safe_text(text: object) -> str:
        """Normalize text for Helvetica/core PDF fonts that do not support full Unicode."""
        safe = str(text)
        replacements = {
            "\u2013": "-",
            "\u2014": "-",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2026": "...",
            "\u00b7": "-",
            "\u2022": "-",
            "\u00d7": "x",
            "\u00a0": " ",
        }
        for old, new in replacements.items():
            safe = safe.replace(old, new)
        return unicodedata.normalize("NFKD", safe).encode("latin-1", "ignore").decode("latin-1")

    class Report(FPDF):
        def header(self):
            pass  # custom header drawn per-page below

        def normalize_text(self, text):
            return super().normalize_text(_pdf_safe_text(text))

        def footer(self):
            self.set_y(-14)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*C_MUTED)
            self.cell(0, 6, f"InterviewLens Coaching Report  ·  Page {self.page_no()}",
                      align="C")

    pdf = Report(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    W = pdf.w

    # ── Hero banner ──────────────────────────────────────────────────────────
    pdf.set_fill_color(*C_BG_DARK)
    pdf.rect(0, 0, W, 36, style="F")

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*C_CYAN)
    pdf.set_xy(12, 8)
    pdf.cell(0, 10, "InterviewLens", ln=False)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_INDIGO)
    pdf.set_xy(12, 22)
    pdf.cell(0, 6, "AI-Powered Interview Coaching Report", ln=False)

    date_str = datetime.now().strftime("%d %b %Y  %H:%M")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C_MUTED)
    pdf.set_xy(W - 52, 8)
    pdf.cell(40, 6, date_str, align="R")
    pdf.ln(28)

    # ── Accent line ───────────────────────────────────────────────────────────
    pdf.set_draw_color(*C_CYAN)
    pdf.set_line_width(0.6)
    pdf.line(12, pdf.get_y(), W - 12, pdf.get_y())
    pdf.ln(4)

    # ── Metrics row ───────────────────────────────────────────────────────────
    def _section_header(title: str, color=C_INDIGO):
        pdf.set_fill_color(*C_LIGHT_BG)
        pdf.rect(12, pdf.get_y(), W - 24, 7, style="F")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*color)
        pdf.set_x(14)
        pdf.cell(0, 7, title.upper(), ln=True)
        pdf.ln(1)

    _section_header("Performance Metrics", C_INDIGO)

    metrics = [
        ("Speaking Rate",  f"{data['speaking_rate_wpm']:.0f} wpm",  "target 120–160"),
        ("Filler Words",   str(data["filler_word_count"]),           "aim for < 5"),
        ("Long Pauses",    str(data["long_pause_count"]),            "> 1.5 s each"),
        ("Signals Flagged",str(data["detected_signals"]),            "body language"),
        ("Duration",       f"{float(data['duration_s']):.0f}s",     "response length"),
    ]
    col_w = (W - 24) / len(metrics)
    start_x = 12
    row_y = pdf.get_y()

    for i, (label, value, sub) in enumerate(metrics):
        x = start_x + i * col_w
        # card background
        pdf.set_fill_color(245, 247, 250)
        pdf.rect(x + 1, row_y, col_w - 2, 20, style="F")
        # value
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*C_BG_DARK)
        pdf.set_xy(x, row_y + 2)
        pdf.cell(col_w - 2, 8, value, align="C")
        # label
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*C_MUTED)
        pdf.set_xy(x, row_y + 10)
        pdf.cell(col_w - 2, 5, label.upper(), align="C")
        # sub
        pdf.set_font("Helvetica", "I", 6.5)
        pdf.set_text_color(*C_INDIGO)
        pdf.set_xy(x, row_y + 15)
        pdf.cell(col_w - 2, 4, sub, align="C")

    pdf.set_y(row_y + 24)
    pdf.ln(2)

    # ── Reliability + tracking ────────────────────────────────────────────────
    _section_header("Quality Scores", C_CYAN)
    row_y2 = pdf.get_y()
    half = (W - 24) / 2

    for i, (label, score) in enumerate([
        ("AI Reliability Score", reliability),
        ("Pose Tracking Quality", float(data["valid_tracking_pct"]) / 100.0),
    ]):
        x = 12 + i * half
        pct = round(score * 100, 1)
        bar_color = rel_color(score)
        # label
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_TEXT)
        pdf.set_xy(x + 1, row_y2)
        pdf.cell(half - 4, 6, label)
        # track
        bar_y = row_y2 + 7
        pdf.set_fill_color(220, 226, 232)
        pdf.rect(x + 1, bar_y, half - 8, 4, style="F")
        pdf.set_fill_color(*bar_color)
        pdf.rect(x + 1, bar_y, (half - 8) * score, 4, style="F")
        # pct
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*bar_color)
        pdf.set_xy(x + half - 16, row_y2)
        pdf.cell(14, 6, f"{pct:.0f}%", align="R")

    pdf.set_y(row_y2 + 16)
    pdf.ln(2)

    # ── Signal timeline (text list) ───────────────────────────────────────────
    if timeline:
        _section_header("Signal Events Timeline", C_ORANGE)
        counts: dict[str, int] = {}
        for ev in timeline:
            counts[ev["label"]] = counts.get(ev["label"], 0) + 1
        col_per_row = 3
        items = [(lbl.replace("_", " ").title(), cnt) for lbl, cnt in
                 sorted(counts.items(), key=lambda x: -x[1])]
        cell_w = (W - 24) / col_per_row
        for row_start in range(0, len(items), col_per_row):
            row_items = items[row_start:row_start + col_per_row]
            row_y3 = pdf.get_y()
            for j, (lbl, cnt) in enumerate(row_items):
                x = 12 + j * cell_w
                if cnt > 3:
                    pdf.set_fill_color(254, 243, 199)
                else:
                    pdf.set_fill_color(241, 245, 249)
                pdf.rect(x + 1, row_y3, cell_w - 2, 7, style="F")
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*C_TEXT)
                pdf.set_xy(x + 2, row_y3)
                pdf.cell(cell_w - 10, 7, lbl)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*C_ORANGE)
                pdf.set_xy(x + cell_w - 12, row_y3)
                pdf.cell(10, 7, f"×{cnt}", align="R")
            pdf.set_y(row_y3 + 9)
        pdf.ln(3)

    # ── Coaching sections (helper) ────────────────────────────────────────────
    def _coaching_section(title: str, items: list[str], accent: tuple,
                           bullet: str = "•"):
        if not items:
            return
        _section_header(title, accent)
        for item in items:
            if pdf.get_y() > pdf.h - 30:
                pdf.add_page()
            y_start = pdf.get_y()
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*C_TEXT)
            pdf.set_x(16)
            # wrap long items
            pdf.multi_cell(W - 28, 5.5, f"{bullet}  {item}", align="L")
            y_end = pdf.get_y()
            # accent bar to the left, sized to the wrapped text block's height
            pdf.set_draw_color(*accent)
            pdf.set_line_width(0.8)
            pdf.line(13, y_start + 0.5, 13, y_end - 0.5)
            pdf.ln(1)
        pdf.ln(2)

    _coaching_section("Observations",     observations, C_INDIGO)
    _coaching_section("Areas to Improve", suggestions,  C_ORANGE)
    _coaching_section("Strengths",        strengths,    C_CYAN)

    # ── Transcript ────────────────────────────────────────────────────────────
    if transcript:
        if pdf.get_y() > pdf.h - 60:
            pdf.add_page()
        _section_header("Transcript", C_MUTED)
        pdf.set_font("Helvetica", "I", 8.5)
        pdf.set_text_color(*C_MUTED)
        pdf.set_x(12)
        pdf.multi_cell(W - 24, 5, transcript)
        pdf.ln(2)

    # ── Flagged moments (one image per distinct category that produced a flag) ──
    # First occurrence per label, in time order -- not one image per individual event,
    # per spec ("una imagen por cada una de las categorías que generó el flag").
    first_per_label: dict[str, int] = {}
    for idx in sorted(range(len(timeline)), key=lambda i: timeline[i]["start_s"]):
        label = timeline[idx]["label"]
        if label not in first_per_label:
            first_per_label[label] = idx
    gallery_entries = [
        (label, idx) for label, idx in first_per_label.items()
        if idx < len(event_frames) and event_frames[idx]
    ]
    gallery_items = [
        (label.replace("_", " ").title(), event_frames[idx], f"at {timeline[idx]['start_s']:.1f}s")
        for label, idx in gallery_entries
    ]
    # Background detection ran on every clip regardless of whether anything about it
    # got flagged -- a clean/uncluttered background means the "Flagged Moments" loop
    # above never includes a background image at all (nothing in _BACKGROUND_LABELS
    # fired), leaving the gallery with pose examples only. Always show a representative
    # background-detection snapshot too, unless a flagged background/lighting image is
    # already in the gallery (then it'd be redundant). Checked against `gallery_entries`
    # (already filtered by a successful frame grab), not the raw label set -- a
    # background label can exist in `first_per_label` even when its frame extraction
    # failed and it never actually made it into the gallery, which was silently
    # suppressing the snapshot fallback and leaving the PDF with zero background images.
    has_background_flag_image = any(label in _BACKGROUND_LABELS for label, _ in gallery_entries)
    background_snapshot = extra.get("background_snapshot")
    if not has_background_flag_image and background_snapshot:
        gallery_items.append(("Background Detection", background_snapshot, "environment snapshot"))

    if gallery_items:
        pdf.add_page()
        _section_header("Flagged Moments", C_MUTED)
        COLS, GAP = 3, 4
        img_w = (W - 24 - GAP * (COLS - 1)) / COLS
        img_h = img_w * 9 / 16
        row_h = img_h + 10
        row_y4 = pdf.get_y()
        for i, (label_text, img_bytes, caption) in enumerate(gallery_items):
            col = i % COLS
            if col == 0 and i > 0:
                row_y4 = row_y4 + row_h
            if row_y4 + row_h > pdf.h - 18:
                pdf.add_page()
                row_y4 = pdf.get_y()
            x = 12 + col * (img_w + GAP)
            y = row_y4
            try:
                pdf.image(io.BytesIO(img_bytes), x=x, y=y, w=img_w, h=img_h)
            except Exception:
                pdf.set_draw_color(*C_MUTED)
                pdf.rect(x, y, img_w, img_h)
            pdf.set_xy(x, y + img_h + 1)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*C_TEXT)
            pdf.multi_cell(img_w, 3.5, label_text, align="L")
            pdf.set_xy(x, pdf.get_y())
            pdf.set_font("Helvetica", "", 6.5)
            pdf.set_text_color(*C_MUTED)
            pdf.multi_cell(img_w, 3, caption, align="L")
        pdf.set_y(row_y4 + row_h)

    # ── Footer accent line ─────────────────────────────────────────────────────
    pdf.set_draw_color(*C_INDIGO)
    pdf.set_line_width(0.4)
    pdf.line(12, pdf.get_y() + 2, W - 12, pdf.get_y() + 2)

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# GANTT CLICK -> FRAME POPUP
# ══════════════════════════════════════════════════════════════════════════════
@st.dialog("Flagged moment")
def _show_event_popup(idx: int, timeline: list[dict], event_frames: list) -> None:
    ev = timeline[idx]
    label = ev["label"].replace("_", " ").title()
    st.markdown(f"**{label}**  ·  {ev['start_s']:.1f}s – {ev['end_s']:.1f}s")
    img = event_frames[idx] if idx < len(event_frames) else None
    if img:
        st.image(img, width="stretch")
    else:
        st.info("No frame was captured for this moment.")


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def _dashboard(data: dict, extra: dict) -> None:
    duration_s  = float(data["duration_s"])
    reliability = float(data["reliability_score"])
    tracking    = float(data["valid_tracking_pct"]) / 100.0
    timeline    = data.get("timeline", [])

    observations = _clean_items(extra.get("observations") or data.get("strengths"))
    suggestions  = _clean_items(extra.get("suggestions")  or data.get("improvements"))
    strengths    = _clean_items(data.get("strengths"))
    transcript   = extra.get("transcript", "")

    # ── Metrics ───────────────────────────────────────────────────────────────
    st.markdown(_sec("📊", "Performance Snapshot"), unsafe_allow_html=True)
    cols = st.columns(5)
    for col, (v, lbl, sub) in zip(cols, [
        (f"{data['speaking_rate_wpm']:.0f}", "WPM",          "target 120–160"),
        (str(data["filler_word_count"]),      "Filler words", "aim for < 5"),
        (str(data["long_pause_count"]),        "Long pauses",  "> 1.5 s each"),
        (str(data["detected_signals"]),        "Body signals", "flagged events"),
        (f"{duration_s:.0f}s",                "Duration",     "response length"),
    ]):
        col.markdown(_metric(v, lbl, sub), unsafe_allow_html=True)

    # ── Gauges + donut ────────────────────────────────────────────────────────
    st.markdown(_sec("🎯", "Quality Gauges"), unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(_gauge(reliability, "AI Reliability Score"),
                        width="stretch")
    with g2:
        st.plotly_chart(_gauge(tracking, "Pose Tracking Quality"),
                        width="stretch")
    with g3:
        fig_d = _donut(timeline)
        if fig_d:
            st.plotly_chart(fig_d, width="stretch")
        else:
            st.markdown(
                '<p style="color:#334155;font-size:.85rem;padding-top:2rem;'
                'text-align:center">No signals detected</p>',
                unsafe_allow_html=True,
            )

    # ── Timeline ──────────────────────────────────────────────────────────────
    st.markdown(_sec("⏱", "Signal Timeline"), unsafe_allow_html=True)
    fig_t = _timeline(timeline, duration_s)
    if fig_t:
        st.markdown(
            '<p style="color:#94a3b8;font-size:.73rem;margin:-.4rem 0 .5rem">'
            'Click a bar to preview the frame captured at that moment.</p>',
            unsafe_allow_html=True,
        )
        event = st.plotly_chart(
            fig_t, width="stretch", on_select="rerun", selection_mode="points",
            key="gantt_chart",
        )
        points = ((event or {}).get("selection") or {}).get("points") or []
        if points:
            idx = points[0].get("customdata", [None])[0]
            if idx is not None and idx != st.session_state.get("_gantt_last_click"):
                st.session_state["_gantt_last_click"] = idx
                _show_event_popup(idx, timeline, extra.get("event_frames") or [])
    else:
        st.markdown(
            '<p style="color:#334155;font-size:.85rem">No signals to display.</p>',
            unsafe_allow_html=True,
        )

    # ── Coaching cards ────────────────────────────────────────────────────────
    st.markdown(_sec("💬", "Coaching Report"), unsafe_allow_html=True)
    ca, cb, cc = st.columns(3)

    with ca:
        st.markdown(_col_title("🔍", "Observations", "obs"), unsafe_allow_html=True)
        for item in (observations or ["Nothing notable detected."]):
            st.markdown(_ccard(item, "obs"), unsafe_allow_html=True)

    with cb:
        st.markdown(_col_title("⚡", "Areas to Improve", "imp"), unsafe_allow_html=True)
        for item in (suggestions or ["No critical issues detected."]):
            st.markdown(_ccard(item, "imp"), unsafe_allow_html=True)

    with cc:
        st.markdown(_col_title("✨", "Strengths", "str"), unsafe_allow_html=True)
        for item in (strengths or ["Keep practising consistently."]):
            st.markdown(_ccard(item, "str"), unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
    pdf_bytes = st.session_state.get("pdf_bytes")
    if pdf_bytes is None:
        pdf_bytes = _build_pdf(data, extra)
        st.session_state["pdf_bytes"] = pdf_bytes
    footer = st.container()
    footer.markdown(_badge(reliability), unsafe_allow_html=True)
    failed_checks = extra.get("failed_checks") or []
    if failed_checks:
        with footer.expander(f"Why is reliability low? ({len(failed_checks)} check(s) failed)"):
            for check in failed_checks:
                st.markdown(f"- `{check}`")
    fcol1, fcol2 = footer.columns(2)
    fcol1.download_button(
        label="⬇️  Download PDF Report",
        data=pdf_bytes,
        file_name="interviewlens_report.pdf",
        mime="application/pdf",
        width="content",
    )
    if fcol2.button("🔄  New Analysis", width="content"):
        for k in ("report", "extra", "pdf_bytes"):
            st.session_state.pop(k, None)
        st.rerun()

    if transcript:
        with st.expander("📝 Transcript"):
            st.markdown(
                f'<p style="color:#64748b;font-size:.87rem;line-height:1.8;'
                f'font-family:Inter,sans-serif">{html.escape(transcript)}</p>',
                unsafe_allow_html=True,
            )
    with st.expander("🗂 Raw report JSON"):
        st.json(data)


# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<h1 class="hero-title">InterviewLens</h1>
<p class="hero-sub">
  Evidence-grounded AI interview coaching &nbsp;·&nbsp;
  pose analysis &nbsp;·&nbsp; speech metrics &nbsp;·&nbsp; LLM feedback
</p>
<hr class="hero-divider">
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-label">Configuration</div>', unsafe_allow_html=True)

    _MAX_UPLOAD_MB = 500
    uploaded_file = st.file_uploader(
        "Video file", type=["mp4", "mov", "avi", "webm", "mkv"],
        help=f"Max {_MAX_UPLOAD_MB} MB. Analyzed with the real pipeline "
             "(RTMPose-S, YOLO-World-S, faster-whisper) — no synthetic data.",
    )
    if uploaded_file is not None and uploaded_file.size > _MAX_UPLOAD_MB * 1024 * 1024:
        st.error(f"File is {uploaded_file.size / (1024 * 1024):.0f} MB — "
                 f"max is {_MAX_UPLOAD_MB} MB.")
        uploaded_file = None

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶  Run Analysis", type="primary", width="stretch",
                        disabled=uploaded_file is None)
    st.divider()

    # Ollama status
    ollama_ok, ollama_msg = _ollama_status()
    dot_clr  = "#22c55e" if ollama_ok else "#ef4444"
    stat_txt = "Connected" if ollama_ok else "Offline"
    stat_clr = "#22c55e" if ollama_ok else "#ef4444"
    st.markdown(f"""
<div class="ollama-box">
  <div class="ollama-key">Ollama LLM</div>
  <div class="ollama-row">
    <span class="rdot" style="background:{dot_clr}"></span>
    <span class="ollama-status" style="color:{stat_clr}">{stat_txt}</span>
  </div>
  <div class="ollama-detail">{ollama_msg}</div>
</div>
""", unsafe_allow_html=True)

# ── Pre-run intro ─────────────────────────────────────────────────────────────
if "report" not in st.session_state:
    st.markdown("""
<p style="color:#475569;font-size:.93rem;max-width:700px;line-height:1.85;
          margin-bottom:2rem;font-family:'Inter',sans-serif">
  InterviewLens watches a mock-interview response and produces an
  evidence-grounded coaching report — what you said, how you said it,
  what your body language was doing, and concrete suggestions backed by
  explicit, checkable evidence rather than free-form AI opinion.
</p>
""", unsafe_allow_html=True)

    cols = st.columns(4)
    for col, (icon, bg, title, body) in zip(cols, _FEATURES):
        col.markdown(
            f'<div class="feat {bg}">'
            f'<div class="feat-icon">{icon}</div>'
            f'<div class="feat-title">{title}</div>'
            f'<div class="feat-body">{body}</div></div>',
            unsafe_allow_html=True,
        )

# ── Run ───────────────────────────────────────────────────────────────────────
if run_btn:
    if uploaded_file is None:
        st.warning("Please upload a video file.")
        st.stop()
    try:
        rd, extra = _run_video(
            "",
            uploaded_file.read(),
            Path(uploaded_file.name).suffix.lower(),
        )
        st.session_state["report"] = rd
        st.session_state["extra"]  = extra
        st.session_state.pop("pdf_bytes", None)
    except Exception as exc:
        # Drop any previous run's report/extra/pdf -- otherwise a failed run on a new
        # video leaves the *last successful* run's dashboard (and its transcript) on
        # screen with no visible link to the video that actually failed, which reads
        # exactly like the report is "stuck" on old, hardcoded data.
        for k in ("report", "extra", "pdf_bytes"):
            st.session_state.pop(k, None)
        st.error(f"**Pipeline error:** {exc}")
        st.stop()

# ── Dashboard ─────────────────────────────────────────────────────────────────
if "report" in st.session_state:
    st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
    _dashboard(st.session_state["report"], st.session_state.get("extra", {}))
