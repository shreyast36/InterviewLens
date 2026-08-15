"""
Generate 4 LLM & Reasoning slides matching the exact visual style of
InterviewLens_Presentation.pptx — dark navy hero cards, colored tier labels,
decorative corner circle, icon badge squares, data bar backgrounds.

Usage:  python scripts/generate_llm_slides.py
Output: C:/Users/shrey/Downloads/InterviewLens_LLM_Slides.pptx
"""
from __future__ import annotations
from pathlib import Path

from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Exact palette from the deck ────────────────────────────────────────────────
BLUE      = RGBColor(0x2C, 0x7F, 0xB8)   # primary accent
DARK_NAV  = RGBColor(0x14, 0x30, 0x4F)   # hero card / headlines
NAVY_ICON = RGBColor(0x1F, 0x38, 0x64)   # small icon badge squares
MID       = RGBColor(0x1A, 0x2B, 0x3C)   # body text
CARD_LT   = RGBColor(0xDC, 0xEB, 0xF7)   # light blue data bar
CARD_MD   = RGBColor(0xEA, 0xF2, 0xFA)   # medium blue card
CARD_GREY = RGBColor(0xEE, 0xF1, 0xF4)   # neutral / challenger card
AMBER     = RGBColor(0xF0, 0xB4, 0x29)   # amber tier label
AMBER_BG  = RGBColor(0xFC, 0xF3, 0xDC)   # amber card body
RED       = RGBColor(0xF0, 0x3B, 0x20)   # red tier
RED_BG    = RGBColor(0xFC, 0xE3, 0xDD)   # red card body
MUTED     = RGBColor(0x5B, 0x7A, 0x99)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
GREEN     = RGBColor(0x21, 0x96, 0x53)
GREEN_BG  = RGBColor(0xE6, 0xF4, 0xEA)

W = 12192000   # slide width  EMU
H =  6858000   # slide height EMU


# ── Low-level helpers ──────────────────────────────────────────────────────────
def _rect(slide, l, t, w, h, fill=None, line_color=None, lw=12700):
    sh = slide.shapes.add_shape(1, l, t, w, h)
    sh.fill.solid() if fill else sh.fill.background()
    if fill: sh.fill.fore_color.rgb = fill
    if line_color: sh.line.color.rgb = line_color; sh.line.width = Emu(lw)
    else: sh.line.fill.background()
    return sh

def _oval(slide, l, t, w, h, fill, line=None):
    sh = slide.shapes.add_shape(9, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line: sh.line.color.rgb = line; sh.line.width = Emu(12700)
    else: sh.line.fill.background()
    return sh

def _tb(slide, l, t, w, h):
    sh = slide.shapes.add_textbox(l, t, w, h)
    sh.line.fill.background()
    return sh

def _tf(tb):
    tf = tb.text_frame; tf.word_wrap = True; return tf

def _p(tf, text, size, bold=False, color=MID, align=PP_ALIGN.LEFT, space=0):
    p = tf.paragraphs[0]; p.alignment = align
    if space: p.space_before = Pt(space)
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
    return p

def _row(tf, text, size, bold=False, color=MID, align=PP_ALIGN.LEFT):
    tf._txBody.add_p()
    para = tf.paragraphs[-1]; para.alignment = align
    if text:
        r = para.add_run(); r.text = text
        r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
    return para

def _row2(tf, label, lsize, lbold, lcolor, body, bsize, bbold, bcolor):
    tf._txBody.add_p()
    para = tf.paragraphs[-1]
    r1 = para.add_run(); r1.text = label
    r1.font.size = Pt(lsize); r1.font.bold = lbold; r1.font.color.rgb = lcolor
    r2 = para.add_run(); r2.text = body
    r2.font.size = Pt(bsize); r2.font.bold = bbold; r2.font.color.rgb = bcolor
    return para


# ── Standard chrome (oval badge + section label + page number) ─────────────────
def _chrome(slide, section, page):
    _oval(slide, 514495, 419029, 615315, 615315, BLUE)
    tb = _tb(slide, 1252728, 588523, 9601200, 256032)
    _p(_tf(tb), section, 18, bold=True, color=BLUE)
    pn = _tb(slide, 11140135, 6528816, 548640, 256032)
    _p(_tf(pn), str(page), 9, color=MUTED, align=PP_ALIGN.RIGHT)

def _deco_circle(slide):
    """Large decorative blue quarter-circle in bottom-right (matches slide 16)."""
    _oval(slide, 10252478, 5202936, 3840480, 3840480, BLUE)

def _insight_bar(slide, text):
    """Dark navy full-width insight strip at bottom (matches slides 7, 11, 14)."""
    _rect(slide, 502920, 5180000, W - 1005840, 1050000, fill=DARK_NAV)
    tb = _tb(slide, 700000, 5240000, W - 1400000, 950000)
    tf = _tf(tb)
    _p(tf, text, 11, color=WHITE)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 18 — Pipeline overview (matches slide 7 style: dark + neutral + light)
# ══════════════════════════════════════════════════════════════════════════════
def slide_overview(prs, page):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    _chrome(slide, "LLM & REASONING", page)
    _deco_circle(slide)

    # Main headline
    tb_h = _tb(slide, 1080412, 820000, 10037619, 520000)
    _p(_tf(tb_h), "Evidence-Grounded LLM Reasoning", 28, bold=True, color=DARK_NAV)

    # Subtitle bar (matches the #DDEAF6 highlight bar in slide 9)
    _rect(slide, 502920, 1420000, W - 1005840, 380000, fill=CARD_LT)
    tb_sub = _tb(slide, 700000, 1460000, W - 1400000, 340000)
    _p(_tf(tb_sub),
       "After pose, background and audio signals are extracted, an LLM reasons "
       "over structured timestamped evidence to produce a validated coaching report.",
       11, color=MID)

    # Three-card layout — exactly matching slide 7 geometry
    cards = [
        (502920,   1930000, 3576218, 2606040, DARK_NAV,  "INPUT\nEVIDENCE",
         WHITE, [
             "Pose & framing signals",
             "Background objects",
             "Audio delivery metrics",
             "Full answer transcript",
         ]),
        (4307738,  1930000, 3576218, 2606040, CARD_GREY, "LLM\nREASONER",
         DARK_NAV, [
             "Nemotron Mini 4B via Ollama",
             "Strict JSON output format",
             "Closed signal vocabulary",
             "Coverage enforcement rules",
         ]),
        (8112557,  1930000, 3576218, 2606040, CARD_MD,   "COACHING\nREPORT",
         DARK_NAV, [
             "Observations per signal",
             "Explanations for each issue",
             "Concrete improvement tips",
             "Reliability score (0–100%)",
         ]),
    ]
    for l, t, w, h, fill, title, tclr, bullets in cards:
        _rect(slide, l, t, w, h, fill=fill)
        tb_t = _tb(slide, l + 150000, t + 130000, w - 300000, 560000)
        _p(_tf(tb_t), title, 16, bold=True, color=tclr)
        tb_b = _tb(slide, l + 150000, t + 750000, w - 300000, h - 850000)
        tf_b = _tf(tb_b)
        _p(tf_b, bullets[0], 11, color=tclr)
        for b in bullets[1:]:
            _row(tf_b, b, 11, color=tclr)

    # Arrow connectors between cards
    for ax in [4040000, 7846000]:
        arr = _tb(slide, ax + 50000, 1930000 + 1303020 - 150000, 267738 - 100000, 300000)
        _p(_tf(arr), "▶", 18, bold=True, color=BLUE, align=PP_ALIGN.CENTER)

    _insight_bar(slide,
        "Every LLM observation must start with a <signal_type>: prefix drawn from the "
        "evidence for this specific clip — the model cannot generalise beyond what the "
        "pipeline detected.")


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 19 — Signal inputs (matches slide 10 style: 3-tier colored columns)
# ══════════════════════════════════════════════════════════════════════════════
def slide_inputs(prs, page):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    _chrome(slide, "LLM & REASONING", page)
    _deco_circle(slide)

    tb_h = _tb(slide, 1080412, 820000, 10037619, 520000)
    _p(_tf(tb_h), "What the LLM Reasons Over", 28, bold=True, color=DARK_NAV)

    # Intro text
    tb_i = _tb(slide, 700000, 1360000, W - 1400000, 360000)
    _p(_tf(tb_i),
       "All four input streams are assembled into a single EvidencePackage "
       "and serialised to structured text — no images, no free-form description.",
       11, color=MID)

    # Four colored columns (matching slide 10 geometry — label bar + body card)
    COL_W = 2750000
    GAP   = 105000
    START = 466344
    LABEL_H = 430000
    BODY_H  = 3200000
    LABEL_Y = 1870000
    BODY_Y  = LABEL_Y + LABEL_H

    cols = [
        (BLUE,     CARD_MD,   "BODY LANGUAGE",  [
            "Hands near face / self-grooming",
            "Arms crossed / not visible",
            "Head tilt, body lean, swaying",
            "Nodding, fidgeting, frozen",
            "Sudden movements",
        ]),
        (AMBER,    AMBER_BG,  "FRAMING & SCENE", [
            "Headroom too loose / tight",
            "Off-centre camera framing",
            "Roll / tilt angle",
            "Distracting background objects",
            "Dominant objects in frame",
        ]),
        (RED,      RED_BG,    "AUDIO DELIVERY", [
            "Speaking rate (WPM)",
            "Filler word count",
            "Long pauses & timestamps",
            "Low microphone level",
            "Intermittent audio dropout",
        ]),
        (GREEN,    GREEN_BG,  "CONTEXT", [
            "Interview question text",
            "Full answer transcript",
            "Signal count summary",
            "Longest clean streak",
            "Per-signal durations",
        ]),
    ]
    for i, (lbl_fill, body_fill, title, bullets) in enumerate(cols):
        x = START + i * (COL_W + GAP)
        _rect(slide, x, LABEL_Y, COL_W, LABEL_H, fill=lbl_fill)
        tb_lbl = _tb(slide, x + 100000, LABEL_Y + 90000, COL_W - 200000, LABEL_H - 180000)
        _p(_tf(tb_lbl), title, 13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        _rect(slide, x, BODY_Y, COL_W, BODY_H, fill=body_fill)
        tb_bod = _tb(slide, x + 120000, BODY_Y + 120000, COL_W - 240000, BODY_H - 200000)
        tf_b = _tf(tb_bod)
        _p(tf_b, f"• {bullets[0]}", 10, color=DARK_NAV)
        for b in bullets[1:]:
            _row(tf_b, f"• {b}", 10, color=DARK_NAV)

    _insight_bar(slide,
        "Required Coverage: the prompt lists only the signal types present in this clip "
        "and mandates one observation per type — the LLM cannot stop after 1–2 signals "
        "even when 7+ are flagged.")


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 20 — Nemotron Mini (matches slide 7 + insight strip style)
# ══════════════════════════════════════════════════════════════════════════════
def slide_model(prs, page):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    _chrome(slide, "LLM & REASONING", page)
    _deco_circle(slide)

    tb_h = _tb(slide, 1080412, 820000, 10037619, 520000)
    _p(_tf(tb_h), "Nemotron Mini 4B — Local LLM via Ollama", 28, bold=True, color=DARK_NAV)

    # Champion dark card (left — matches slide 7 dark card)
    _rect(slide, 502920, 1480000, 3800000, 3500000, fill=DARK_NAV)
    tb_c = _tb(slide, 650000, 1580000, 3500000, 3300000)
    tf_c = _tf(tb_c)
    _p(tf_c, "nemotron-mini", 20, bold=True, color=WHITE)
    _row(tf_c, "Champion Model", 11, bold=False, color=CARD_MD)
    _row(tf_c, "", 6)
    facts = [
        ("4B parameters  ·  ~2.7 GB", WHITE),
        ("Runs locally — no cloud, no API key", WHITE),
        ("Instruction-tuned for structured output", WHITE),
        ("format='json' enforces valid JSON every time", WHITE),
        ("Offline fallback to deterministic mock", WHITE),
        ("Zero data leaves the device", WHITE),
    ]
    for txt, clr in facts:
        _row(tf_c, "", 4)
        _row(tf_c, f"✓  {txt}", 10, bold=False, color=clr)

    # Label bar above champion card
    _rect(slide, 502920, 1370000, 3800000, 110000, fill=BLUE)
    lbl = _tb(slide, 502920, 1280000, 3800000, 280000)
    _p(_tf(lbl), "Champion", 16, bold=True, color=DARK_NAV)

    # Three prompt-rule cards (right — icon badge style from slide 9)
    rules = [
        (NAVY_ICON, "Closed Vocabulary",
         "Every observation must start with a <signal_type>: token "
         "from the SignalType enum. Invented signal names are rejected downstream."),
        (NAVY_ICON, "Coverage Enforcement",
         "The prompt lists every signal type flagged in this clip. "
         "The LLM must produce one observation per type — no early stopping."),
        (NAVY_ICON, "Concrete Fix Mandate",
         "Lighting and audio signals require a specific remedy, not a vague comment. "
         "e.g. 'move toward a front-facing light source' for low_light."),
    ]
    rule_h = 1100000
    for i, (badge_fill, title, body) in enumerate(rules):
        y = 1400000 + i * (rule_h + 80000)
        _rect(slide, 4450000, y, 7300000, rule_h, fill=CARD_MD)
        # icon badge
        _rect(slide, 4450000, y, 380000, rule_h, fill=badge_fill)
        badge_n = _tb(slide, 4460000, y + rule_h // 2 - 200000, 360000, 400000)
        _p(_tf(badge_n), str(i + 1), 22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        # text
        tb_r = _tb(slide, 4900000, y + 120000, 6750000, rule_h - 240000)
        tf_r = _tf(tb_r)
        _p(tf_r, title, 13, bold=True, color=DARK_NAV)
        _row(tf_r, body, 10, color=MID)

    _insight_bar(slide,
        "A static example in the prompt caused small models to copy the example verbatim "
        "instead of reasoning about the actual clip. REQUIRED FORMAT replaces examples "
        "with a dynamic list of real signal names — forcing the model to read the evidence.")


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 21 — Validation + Report (matches slide 8/12 results layout)
# ══════════════════════════════════════════════════════════════════════════════
def slide_output(prs, page):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    _chrome(slide, "LLM & REASONING", page)
    _deco_circle(slide)

    tb_h = _tb(slide, 1080412, 820000, 10037619, 520000)
    _p(_tf(tb_h), "Validation Layer & Coaching Report", 28, bold=True, color=DARK_NAV)

    # Left: validation checks (4 rows, alternating light/dark)
    checks = [
        (BLUE,      "Category Check",
         "Every claim must contain a keyword from the allowed signal vocabulary."),
        (DARK_NAV,  "Timestamp Check",
         "Timestamps in claims must fall within 0 – clip duration seconds."),
        (BLUE,      "Confidence Gate",
         "Low-confidence detections (< 0.5) reduce the reliability score."),
        (DARK_NAV,  "Coverage Check",
         "Claims without matching evidence data points are flagged as unsupported."),
    ]
    chk_w = 5500000
    chk_h = 920000
    ct = 1480000
    for i, (accent, title, body) in enumerate(checks):
        y = ct + i * (chk_h + 80000)
        bg = CARD_MD if accent == BLUE else CARD_LT
        _rect(slide, 502920, y, chk_w, chk_h, fill=bg)
        _rect(slide, 502920, y, 380000, chk_h, fill=accent)
        num = _tb(slide, 502920, y + chk_h // 2 - 200000, 380000, 400000)
        _p(_tf(num), str(i + 1), 22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        tb_tx = _tb(slide, 990000, y + 100000, chk_w - 600000, chk_h - 200000)
        tf_tx = _tf(tb_tx)
        _p(tf_tx, title, 12, bold=True, color=DARK_NAV)
        _row(tf_tx, body, 10, color=MID)

    # Reliability score formula label
    rel_y = ct + 4 * (chk_h + 80000) + 20000
    _rect(slide, 502920, rel_y, chk_w, 360000, fill=BLUE)
    tb_rel = _tb(slide, 620000, rel_y + 60000, chk_w - 240000, 240000)
    _p(_tf(tb_rel),
       "Reliability = max(0,  1.0 − 0.15 × failed_checks)   →   0–100%",
       11, bold=True, color=WHITE)

    # Right: output sections (3 rows matching the tier style)
    out_x = 502920 + chk_w + 220000
    out_w = W - out_x - 502920
    outputs = [
        (BLUE,   WHITE,    "OBSERVATIONS",
         "What happened and when, tied to each flagged signal with timestamp."),
        (AMBER,  DARK_NAV, "IMPROVEMENTS",
         "One concrete, actionable suggestion per signal type in the evidence."),
        (GREEN,  WHITE,    "STRENGTHS",
         "Positive observations from reasoning output when reliability ≥ 0.75."),
    ]
    out_h_each = (4 * (chk_h + 80000) - 80000) // 3 - 60000
    for i, (lbl_fill, lbl_clr, title, body) in enumerate(outputs):
        y = ct + i * (out_h_each + 80000)
        _rect(slide, out_x, y, out_w, 380000, fill=lbl_fill)
        tb_lbl = _tb(slide, out_x + 120000, y + 80000, out_w - 240000, 280000)
        _p(_tf(tb_lbl), title, 14, bold=True, color=lbl_clr)
        _rect(slide, out_x, y + 380000, out_w, out_h_each - 380000, fill=CARD_GREY)
        tb_bod = _tb(slide, out_x + 120000, y + 480000, out_w - 240000, out_h_each - 600000)
        _p(_tf(tb_bod), body, 10, color=MID)

    # PDF export tag
    _rect(slide, out_x, ct + 3 * (out_h_each + 80000) - 60000, out_w, 420000, fill=DARK_NAV)
    tb_pdf = _tb(slide, out_x + 120000, ct + 3 * (out_h_each + 80000) - 60000 + 80000, out_w - 240000, 260000)
    _p(_tf(tb_pdf), "⬇   Full report exported as a branded PDF from the Streamlit dashboard",
       11, bold=True, color=WHITE)

    _insight_bar(slide,
        "Reliability ≥ 0.75 → High confidence  ·  0.50–0.75 → Moderate  ·  < 0.50 → Low.  "
        "Content is always shown above 0.30 so coaching is never silently suppressed by a "
        "single low-confidence detection.")


# ══════════════════════════════════════════════════════════════════════════════
def main():
    src  = Path(r"C:\Users\shrey\Downloads\InterviewLens_Presentation.pptx")
    dest = Path(r"C:\Users\shrey\Downloads\InterviewLens_LLM_Slides.pptx")

    prs = Presentation(str(src))
    n   = len(prs.slides)

    # Keep only the original 17 slides (drop any previous attempts)
    while len(prs.slides) > 17:
        rId = prs.slides._sldIdLst[-1].get("r:id")
        del prs.slides._sldIdLst[-1]
        prs.part.drop_rel(rId)

    slide_overview(prs, 18); print("  18 — Pipeline Overview")
    slide_inputs  (prs, 19); print("  19 — Signal Inputs")
    slide_model   (prs, 20); print("  20 — Nemotron Mini")
    slide_output  (prs, 21); print("  21 — Validation & Report")

    prs.save(str(dest))
    print(f"\nSaved → {dest}  ({dest.stat().st_size / 1e6:.1f} MB, 21 slides)")


if __name__ == "__main__":
    main()
