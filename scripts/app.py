"""InterviewLens — Streamlit coaching interface.

Run from the repo root:
    streamlit run scripts/app.py
"""
from __future__ import annotations

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
    background: #050c18;
    color: #e2e8f0;
}

[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed; inset: 0; z-index: -1;
    background:
        radial-gradient(ellipse 80% 60% at 10%  15%, rgba(34,211,238,.07)  0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 90%  85%, rgba(129,140,248,.07) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 50%  50%, rgba(236,72,153,.04)  0%, transparent 50%),
        #050c18;
}

[data-testid="stHeader"]  { background: transparent !important; }
.block-container          { padding-top: 1.8rem !important; max-width: 1400px; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* ─── sidebar ───────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] > div:first-child {
    background: rgba(5,12,24,.95);
    border-right: 1px solid rgba(34,211,238,.08);
    backdrop-filter: blur(20px);
}
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }

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
    background: rgba(255,255,255,.03);
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
    background: linear-gradient(135deg, #e2e8f0, #22d3ee);
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
    font-size: .84rem; color: #94a3b8;
    line-height: 1.65;
    overflow: hidden;
    animation: slide-in .35s ease both;
    transition: transform .2s, color .2s;
    backdrop-filter: blur(8px);
}
.ccard:hover { transform: translateX(3px); color: #cbd5e1; }
.ccard::before {
    content: ""; position: absolute; left: 0; top: 0;
    width: 3px; height: 100%; border-radius: 0 2px 2px 0;
}
.ccard-obs { background: rgba(129,140,248,.06); }
.ccard-obs::before { background: linear-gradient(180deg, #818cf8, #a78bfa); }
.ccard-imp { background: rgba(249,115,22,.06);  }
.ccard-imp::before { background: linear-gradient(180deg, #f97316, #fb923c); }
.ccard-str { background: rgba(34,211,238,.06);  }
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
    background: linear-gradient(135deg, rgba(255,255,255,.12), rgba(255,255,255,.03));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none;
}
.feat-bg0 { background: linear-gradient(135deg, rgba(34,211,238,.08), rgba(6,182,212,.04)); }
.feat-bg1 { background: linear-gradient(135deg, rgba(129,140,248,.08), rgba(99,102,241,.04)); }
.feat-bg2 { background: linear-gradient(135deg, rgba(236,72,153,.08), rgba(244,114,182,.04)); }
.feat-bg3 { background: linear-gradient(135deg, rgba(251,191,36,.08), rgba(245,158,11,.04)); }
.feat:hover { transform: translateY(-5px) scale(1.01);
              box-shadow: 0 20px 50px rgba(0,0,0,.4); }
.feat-icon  { font-size: 2rem; margin-bottom: .7rem; }
.feat-title { font-family: 'Space Grotesk', sans-serif; font-size: .92rem;
              font-weight: 600; color: #e2e8f0; margin-bottom: .4rem; }
.feat-body  { font-size: .78rem; color: #64748b; line-height: 1.6; }

/* ─── badge ──────────────────────────────────────────────────────────────────── */
.rbadge {
    display: inline-flex; align-items: center; gap: .45rem;
    padding: .28rem 1rem .28rem .65rem;
    border-radius: 999px; font-size: .73rem; font-weight: 600;
    letter-spacing: .04em;
}
.rbadge-hi  { background: rgba(34,211,238,.1);  color: #22d3ee;
              border: 1px solid rgba(34,211,238,.25); }
.rbadge-med { background: rgba(234,179,8,.1);   color: #eab308;
              border: 1px solid rgba(234,179,8,.25);  }
.rbadge-lo  { background: rgba(239,68,68,.1);   color: #ef4444;
              border: 1px solid rgba(239,68,68,.25);  }
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
    background: rgba(255,255,255,.04) !important;
    border: 1px solid rgba(255,255,255,.1) !important;
    color: #64748b !important; border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ─── sidebar label ──────────────────────────────────────────────────────────── */
.sb-label {
    font-size: .58rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .13em; color: #334155; margin-bottom: .7rem;
    padding-bottom: .5rem; border-bottom: 1px solid rgba(255,255,255,.05);
}

/* ─── ollama box ─────────────────────────────────────────────────────────────── */
.ollama-box {
    border-radius: 12px; padding: .7rem .9rem;
    background: rgba(255,255,255,.025);
    border: 1px solid rgba(255,255,255,.06);
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


# ══════════════════════════════════════════════════════════════════════════════
# PLOTLY CHARTS
# ══════════════════════════════════════════════════════════════════════════════
_PLOTLY_BASE = dict(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"))


def _gauge(value_0_1: float, title: str) -> go.Figure:
    pct = round(min(max(value_0_1, 0.0), 1.0) * 100, 1)
    clr = "#22d3ee" if pct >= 75 else "#eab308" if pct >= 50 else "#ef4444"
    glow = f"rgba({int(clr[1:3],16)},{int(clr[3:5],16)},{int(clr[5:7],16)},.15)"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number=dict(suffix="%", font=dict(size=30, color="#e2e8f0",
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
        textfont=dict(size=10, color="#e2e8f0"),
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
    if not timeline:
        return None
    sorted_tl = sorted(timeline, key=lambda e: e["time_s"])
    spans: list[tuple[str, float, float]] = []
    cur, cur_s = sorted_tl[0]["label"], float(sorted_tl[0]["time_s"])
    for ev in sorted_tl[1:]:
        t = float(ev["time_s"])
        if ev["label"] != cur:
            spans.append((cur, cur_s, t))
            cur, cur_s = ev["label"], t
    spans.append((cur, cur_s, max(cur_s + 0.5, duration_s)))

    labels  = list(dict.fromkeys(s[0] for s in spans))
    y_map   = {l: i for i, l in enumerate(labels)}
    plotted: set[str] = set()
    fig = go.Figure()

    for label, start, end in spans:
        c = _clr(label)
        # glow layer
        fig.add_trace(go.Bar(
            x=[end - start], y=[y_map[label]], base=[start],
            orientation="h",
            marker=dict(color=c, opacity=0.15),
            showlegend=False, hoverinfo="skip",
            width=0.85,
        ))
        # main bar
        fig.add_trace(go.Bar(
            x=[end - start], y=[y_map[label]], base=[start],
            orientation="h",
            marker=dict(color=c, opacity=0.88,
                        line=dict(color="rgba(0,0,0,.4)", width=1)),
            name=label.replace("_", " ").title(),
            showlegend=label not in plotted,
            width=0.55,
            hovertemplate=(
                f"<b>{label.replace('_',' ').title()}</b><br>"
                f"⏱ {start:.1f}s – {end:.1f}s  ({end-start:.1f}s)<extra></extra>"
            ),
        ))
        plotted.add(label)

    ax = dict(gridcolor="rgba(255,255,255,.04)", zeroline=False,
              color="#334155", tickfont=dict(size=10))
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(title="Time (s)", range=[0, duration_s], **ax),
        yaxis=dict(tickvals=list(y_map.values()),
                   ticktext=[l.replace("_", " ").title() for l in labels], **ax),
        height=max(190, 60 + 46 * len(labels)),
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(255,255,255,.012)",
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
    return f'<div class="ccard ccard-{kind}">{text}</div>'


def _col_title(icon: str, text: str, kind: str) -> str:
    return (f'<div class="ccard-col-title ccard-col-title-{kind}">'
            f'{icon} {text}</div>')


def _badge(score: float) -> str:
    cls   = "rbadge-hi" if score >= 0.75 else "rbadge-med" if score >= 0.5 else "rbadge-lo"
    dot   = "#22c55e"   if score >= 0.75 else "#eab308"    if score >= 0.5 else "#ef4444"
    label = ("High confidence" if score >= 0.75
             else "Moderate" if score >= 0.5 else "Low confidence")
    return (f'<span class="rbadge {cls}">'
            f'<span class="rdot" style="background:{dot}"></span>'
            f'{label} &nbsp;·&nbsp; {score:.0%}</span>')


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE RUNNERS
# ══════════════════════════════════════════════════════════════════════════════
def _run_demo(question: str) -> tuple[dict, dict]:
    from interviewlens.audio_pipeline.asr import build_asr_model
    from interviewlens.audio_pipeline.capture import synthetic_audio
    from interviewlens.audio_pipeline.delivery_analytics import compute_metrics
    from interviewlens.audio_pipeline.postprocessing import normalize_disfluencies
    from interviewlens.audio_pipeline.preprocessing import preprocess
    from interviewlens.common.config import load_config
    from interviewlens.common.schemas import Transcript
    from interviewlens.reasoning.evidence_assembly import assemble_evidence
    from interviewlens.reasoning.evidence_validation import validate
    from interviewlens.reasoning.llm_reasoning import LLMReasoner
    from interviewlens.reporting.coaching_report import build_coaching_report
    from interviewlens.video_pipeline.capture import synthetic_frames
    from interviewlens.video_pipeline.keypoint_processor import (
        normalize_frame, valid_tracking_pct,
    )
    from interviewlens.video_pipeline.pose_estimation import build_pose_estimator
    from interviewlens.video_pipeline.signal_detection import build_signal_detector
    from interviewlens.video_pipeline.temporal_sequence import RollingWindowBuilder

    cfg = load_config()

    with st.status("🚀 Running InterviewLens pipeline…", expanded=True) as status:
        st.write("📐 **Stage 1 / 5** — Video pipeline: pose estimation & signal detection")
        pe = build_pose_estimator(cfg.video.pose_model)
        sd = build_signal_detector("champion")
        wb = RollingWindowBuilder(fps=cfg.video.fps,
                                  window_seconds=cfg.video.window_seconds,
                                  stride_seconds=cfg.video.stride_seconds)
        visual_events, pose_frames, all_frames = [], [], {}
        for frame, ts in synthetic_frames(cfg.video.fps * 8, fps=cfg.video.fps):
            fi = int(ts * cfg.video.fps)
            all_frames[fi] = frame
            pf = normalize_frame(pe.estimate(frame, fi, ts))
            pose_frames.append(pf)
            w = wb.push(pf)
            if w:
                visual_events.extend(sd.detect(w))
        tracking_pct = valid_tracking_pct(pose_frames)

        st.write("🎙️ **Stage 2 / 5** — Audio pipeline: transcription & delivery metrics")
        asr = build_asr_model(cfg.audio.asr_model)
        raw_audio = synthetic_audio(duration_s=8.0, sample_rate=cfg.audio.sample_rate)
        segs = preprocess(raw_audio, cfg.audio.sample_rate)
        trans_list = [asr.transcribe(seg) for seg in segs]
        transcript = normalize_disfluencies(Transcript(
            text=" ".join(t.text for t in trans_list),
            words=[w for t in trans_list for w in t.words],
        ))
        audio_metrics = compute_metrics(transcript, total_duration_s=8.0)

        st.write("🧩 **Stage 3 / 5** — Fusing modalities into evidence package")
        evidence = assemble_evidence(
            question=question, transcript=transcript,
            audio_metrics=audio_metrics, visual_events=visual_events,
            fps=cfg.video.fps, all_frames=all_frames,
        )

        st.write("🤖 **Stage 4 / 5** — LLM reasoning via Ollama Nemotron")
        reasoner = LLMReasoner(
            model_name=cfg.reasoning.llm_model,
            max_tokens=cfg.reasoning.max_output_tokens,
            temperature=cfg.reasoning.temperature,
        )
        reasoning_output = reasoner.reason(evidence)

        st.write("📊 **Stage 5 / 5** — Building coaching report")
        validation = validate(evidence, reasoning_output)
        report = build_coaching_report(
            duration_s=8.0, valid_tracking_pct=tracking_pct,
            audio_metrics=audio_metrics, visual_events=visual_events,
            reasoning=reasoning_output, validation=validation,
        )
        status.update(label="✅ Analysis complete!", state="complete", expanded=False)

    return asdict(report), {
        "observations": reasoning_output.observations,
        "explanations": reasoning_output.explanations,
        "suggestions":  reasoning_output.suggestions,
        "transcript":   transcript.text,
    }


def _run_video(question: str, video_bytes: bytes, suffix: str) -> tuple[dict, dict]:
    """Run the real pipeline on an uploaded video with per-stage status updates."""
    import gc
    from interviewlens.audio_pipeline.asr import build_asr_model
    from interviewlens.audio_pipeline.capture import synthetic_audio
    from interviewlens.audio_pipeline.delivery_analytics import compute_metrics
    from interviewlens.audio_pipeline.postprocessing import normalize_disfluencies
    from interviewlens.audio_pipeline.preprocessing import preprocess
    from interviewlens.audio_pipeline.batch_audio_quality import extract_audio_quality_evidence
    from interviewlens.common.config import load_config
    from interviewlens.common.schemas import Transcript
    from interviewlens.reasoning.evidence_assembly import from_fused_evidence_json
    from interviewlens.reasoning.evidence_validation import validate
    from interviewlens.reasoning.llm_reasoning import LLMReasoner
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

            st.write("📝 **Stage 5 / 6** — Evidence assembly & LLM reasoning…")
            asr = build_asr_model(cfg.audio.asr_model)
            raw_audio  = synthetic_audio(duration_s=duration_s, sample_rate=cfg.audio.sample_rate)
            trans_list = [asr.transcribe(seg) for seg in preprocess(raw_audio, cfg.audio.sample_rate)]
            transcript = normalize_disfluencies(Transcript(
                text=" ".join(t.text for t in trans_list),
                words=[w for t in trans_list for w in t.words],
            ))
            audio_metrics = compute_metrics(transcript, total_duration_s=duration_s)
            probe      = from_fused_evidence_json(fused, question=question,
                                                   transcript=transcript, audio_metrics=audio_metrics)
            all_frames = grab_frames(tmp_path, probe.selected_frames, fused["fps_fused"])
            evidence   = from_fused_evidence_json(fused, question=question,
                                                   transcript=transcript, audio_metrics=audio_metrics,
                                                   all_frames=all_frames)
            reasoner = LLMReasoner(
                model_name=cfg.reasoning.llm_model,
                max_tokens=cfg.reasoning.max_output_tokens,
                temperature=cfg.reasoning.temperature,
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

        return asdict(report), {
            "observations": reasoning_output.observations,
            "explanations": reasoning_output.explanations,
            "suggestions":  reasoning_output.suggestions,
            "transcript":   transcript.text,
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
    from fpdf import FPDF  # noqa: PLC0415

    observations = extra.get("observations") or data.get("strengths") or []
    suggestions  = extra.get("suggestions")  or data.get("improvements") or []
    strengths    = data.get("strengths") or []
    transcript   = extra.get("transcript", "")
    reliability  = float(data["reliability_score"])
    timeline     = data.get("timeline", [])
    question     = extra.get("question", "")

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

    class Report(FPDF):
        def header(self):
            pass  # custom header drawn per-page below

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

    # ── Question ─────────────────────────────────────────────────────────────
    if question:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(0, 5, "INTERVIEW QUESTION", ln=True)
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(*C_TEXT)
        pdf.multi_cell(W - 24, 6, f'"{question}"', align="L")
        pdf.ln(3)

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
                pdf.set_fill_color(254, 243, 199) if cnt > 3 else pdf.set_fill_color(241, 245, 249)
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
            # bullet strip
            pdf.set_fill_color(*accent)
            pdf.rect(12, pdf.get_y(), 2, 0, style="F")  # thin left bar
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*C_TEXT)
            pdf.set_x(16)
            # wrap long items
            safe = item.replace("\u2014", "-").replace("\u2019", "'").replace("\u2018", "'")
            pdf.multi_cell(W - 28, 5.5, f"{bullet}  {safe}", align="L")
            pdf.ln(1)
        pdf.ln(2)

    _coaching_section("Observations",     observations, C_INDIGO)
    _coaching_section("Areas to Improve", suggestions,  C_ORANGE)
    _coaching_section("Strengths",        strengths,    C_CYAN)

    # ── Transcript ────────────────────────────────────────────────────────────
    if transcript:
        if pdf.get_y() > pdf.h - 60:
            pdf.add_page()
        _section_header("Transcript (Synthetic Placeholder)", C_MUTED)
        pdf.set_font("Helvetica", "I", 8.5)
        pdf.set_text_color(*C_MUTED)
        pdf.set_x(12)
        pdf.multi_cell(W - 24, 5, transcript)
        pdf.ln(2)

    # ── Footer accent line ─────────────────────────────────────────────────────
    pdf.set_draw_color(*C_INDIGO)
    pdf.set_line_width(0.4)
    pdf.line(12, pdf.get_y() + 2, W - 12, pdf.get_y() + 2)

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def _dashboard(data: dict, extra: dict) -> None:
    duration_s  = float(data["duration_s"])
    reliability = float(data["reliability_score"])
    tracking    = float(data["valid_tracking_pct"]) / 100.0
    timeline    = data.get("timeline", [])

    observations = extra.get("observations") or data.get("strengths") or []
    suggestions  = extra.get("suggestions")  or data.get("improvements") or []
    strengths    = data.get("strengths") or []
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
        st.plotly_chart(fig_t, width="stretch")
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
    left_f, mid_f, right_f = st.columns([2, 2, 1])
    with left_f:
        st.markdown(_badge(reliability), unsafe_allow_html=True)
    with mid_f:
        pdf_bytes = _build_pdf(data, extra)
        st.download_button(
            label="⬇️  Download PDF Report",
            data=pdf_bytes,
            file_name="interviewlens_report.pdf",
            mime="application/pdf",
            use_container_width=False,
        )
    with right_f:
        if st.button("🔄  New Analysis", width="content"):
            for k in ("report", "extra"):
                st.session_state.pop(k, None)
            st.rerun()

    if transcript:
        with st.expander("📝 Transcript"):
            st.markdown(
                f'<p style="color:#64748b;font-size:.87rem;line-height:1.8;'
                f'font-family:Inter,sans-serif">{transcript}</p>',
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

    question = st.text_area(
        "Interview question",
        value="Tell me about a time you resolved a conflict at work.",
        height=110,
        help="The question the candidate is answering.",
    )

    mode = st.radio(
        "Input mode",
        ["🧪 Demo (synthetic)", "🎬 Upload video"],
        index=0,
    )

    uploaded_file = None
    if mode == "🎬 Upload video":
        uploaded_file = st.file_uploader(
            "Video file", type=["mp4", "mov", "avi", "webm", "mkv"],
            help="Max 500 MB. Real pipeline requires onnxruntime.",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶  Run Analysis", type="primary", width="stretch")
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
    if not question.strip():
        st.warning("Please enter an interview question.")
        st.stop()
    try:
        if mode == "🧪 Demo (synthetic)":
            rd, extra = _run_demo(question.strip())
        else:
            if uploaded_file is None:
                st.warning("Please upload a video file.")
                st.stop()
            rd, extra = _run_video(
                question.strip(),
                uploaded_file.read(),
                Path(uploaded_file.name).suffix.lower(),
            )
        st.session_state["report"] = rd
        st.session_state["extra"]  = {**extra, "question": question.strip()}
    except Exception as exc:
        st.error(f"**Pipeline error:** {exc}")
        st.stop()

# ── Dashboard ─────────────────────────────────────────────────────────────────
if "report" in st.session_state:
    st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
    _dashboard(st.session_state["report"], st.session_state.get("extra", {}))
