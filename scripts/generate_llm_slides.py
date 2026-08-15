"""
Generate 4 LLM & Reasoning slides appended to InterviewLens_Presentation.pptx.
Matches the existing deck style: white background, #2C7FB8 blue accents,
#14304F dark-navy headings, #DCEBF7 / #EAF2FA light-blue cards.

Usage:  python scripts/generate_llm_slides.py
Output: C:/Users/shrey/Downloads/InterviewLens_LLM_Slides.pptx
"""
from __future__ import annotations
from pathlib import Path

from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Palette ────────────────────────────────────────────────────────────────────
BLUE      = RGBColor(0x2C, 0x7F, 0xB8)
NAVY      = RGBColor(0x14, 0x30, 0x4F)
MID       = RGBColor(0x1A, 0x2B, 0x3C)
CARD_LT   = RGBColor(0xDC, 0xEB, 0xF7)   # #DCEBF7  light blue card
CARD_MD   = RGBColor(0xEA, 0xF2, 0xFA)   # #EAF2FA  medium blue card
CARD_GRN  = RGBColor(0xEA, 0xF2, 0xD6)   # soft green card
CARD_GREY = RGBColor(0xEE, 0xF1, 0xF4)   # neutral grey card
MUTED     = RGBColor(0x5B, 0x7A, 0x99)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)

# Slide canvas (13.333" × 7.5", standard widescreen)
W = 12192000   # EMU
H =  6858000   # EMU


# ── Primitive helpers ──────────────────────────────────────────────────────────
def _rect(slide, l, t, w, h, fill=None, line=None, lw=12700):
    sh = slide.shapes.add_shape(1, l, t, w, h)
    sh.fill.solid() if fill else sh.fill.background()
    if fill: sh.fill.fore_color.rgb = fill
    if line: sh.line.color.rgb = line; sh.line.width = Emu(lw)
    else: sh.line.fill.background()
    return sh

def _oval(slide, l, t, w, h, fill, line):
    sh = slide.shapes.add_shape(9, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = line; sh.line.width = Emu(12700)
    return sh

def _tb(slide, l, t, w, h):
    sh = slide.shapes.add_textbox(l, t, w, h)
    sh.line.fill.background()
    return sh

def _p0(tf, txt, size, bold=False, color=MID, align=PP_ALIGN.LEFT):
    """Set text in first paragraph of a text frame."""
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = txt; r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color
    return p

def _row(tf, txt, size, bold=False, color=MID, align=PP_ALIGN.LEFT):
    """Append a new paragraph to a text frame."""
    p = tf._txBody.add_p()
    para = tf.paragraphs[-1]
    para.alignment = align
    if txt:
        r = para.add_run()
        r.text = txt; r.font.size = Pt(size); r.font.bold = bold
        r.font.color.rgb = color
    return para


def _chrome(slide, section: str, page: int):
    """Standard slide chrome: blue oval badge + section title + page number."""
    _oval(slide, 514495, 419029, 615315, 615315, BLUE, BLUE)
    tb = _tb(slide, 1252728, 588523, 9601200, 256032)
    _p0(tb.text_frame, section, 18, bold=True, color=BLUE)
    pn = _tb(slide, 11140135, 6528816, 548640, 256032)
    _p0(pn.text_frame, str(page), 9, bold=False, color=MUTED, align=PP_ALIGN.RIGHT)


def _heading(slide, txt, size=25, y=855054):
    tb = _tb(slide, 1080412, y, 10037619, 476874)
    _p0(tb.text_frame, txt, size, bold=True, color=NAVY)
    return tb


def _subhead(slide, txt, y):
    tb = _tb(slide, 995567, y, 10370934, 300000)
    _p0(tb.text_frame, txt, 12, bold=False, color=MID)
    return tb


def _bottom_bar(slide, txt):
    """Dark navy banner across the bottom (like the insight bars in the deck)."""
    _rect(slide, 502920, 5260000, W - 1005840, 700000, fill=NAVY)
    tb = _tb(slide, 660000, 5300000, W - 1320000, 640000)
    _p0(tb.text_frame, txt, 11, bold=False, color=WHITE)
    tb.text_frame.word_wrap = True


# ══════════════════════════════════════════════════════════════════════════════
# Slide 1 — What the LLM Reasoning stage does
# ══════════════════════════════════════════════════════════════════════════════
def slide_overview(prs, page):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    _chrome(slide, "LLM & REASONING", page)
    _heading(slide, "Evidence-Grounded LLM Reasoning")

    # Sub-heading
    _subhead(slide,
             "After pose, background, and audio signals are extracted, an LLM reasons "
             "over the structured evidence to produce coaching insights — every claim "
             "must be traceable back to a timestamped event in the data.",
             1430000)

    # 5 pipeline cards
    stages = [
        ("Pose &\nFraming",    "17 keypoint rules\nframing quality",    CARD_MD),
        ("Background\n& Audio","Object detection\nmic-level checks",    CARD_MD),
        ("Evidence\nPackage",  "Fused timeline\nper-signal summary",    CARD_LT),
        ("Nemotron\nMini 4B",  "Structured JSON\nobservations & tips",  BLUE),
        ("Coaching\nReport",   "Validated insights\nPDF + dashboard",   CARD_GRN),
    ]
    cw, ch, ct = 1960000, 1780000, 2100000
    gap = 150000
    total = len(stages) * cw + (len(stages) - 1) * gap
    sx = (W - total) // 2

    for i, (title, body, fill) in enumerate(stages):
        x = sx + i * (cw + gap)
        _rect(slide, x, ct, cw, ch, fill=fill)
        title_clr = WHITE if fill == BLUE else NAVY
        body_clr  = WHITE if fill == BLUE else MID
        tb1 = _tb(slide, x + 80000, ct + 120000, cw - 160000, 580000)
        _p0(tb1.text_frame, title, 13, bold=True, color=title_clr, align=PP_ALIGN.CENTER)
        tb2 = _tb(slide, x + 80000, ct + 740000, cw - 160000, 900000)
        _p0(tb2.text_frame, body, 9, bold=False, color=body_clr, align=PP_ALIGN.CENTER)
        if i < len(stages) - 1:
            arr = _tb(slide, x + cw + 10000, ct + ch // 2 - 100000, gap - 20000, 200000)
            _p0(arr.text_frame, "→", 16, bold=True, color=BLUE, align=PP_ALIGN.CENTER)

    _bottom_bar(slide,
        "The LLM is never shown raw video frames — it reads only timestamped, structured "
        "evidence.  This eliminates appearance hallucinations and makes every coaching "
        "suggestion checkable against the original signal data.")


# ══════════════════════════════════════════════════════════════════════════════
# Slide 2 — What goes into the LLM (signal inputs)
# ══════════════════════════════════════════════════════════════════════════════
def slide_inputs(prs, page):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    _chrome(slide, "LLM & REASONING", page)
    _heading(slide, "What the LLM Reasons Over")

    groups = [
        ("Body Language Signals", CARD_LT, [
            "Hands near face / self-grooming",
            "Arms crossed / hands not visible",
            "Head tilt, body lean, swaying, nodding",
            "Sudden movements, fidgeting, frozen posture",
        ]),
        ("Camera Framing", CARD_MD, [
            "Headroom too loose / too tight",
            "Off-center framing",
            "Camera roll / tilt angle",
            "Dominant background objects",
        ]),
        ("Audio Delivery", CARD_GRN, [
            "Speaking rate (words per minute)",
            "Filler word count",
            "Long pause count & timestamps",
            "Mic level quality / intermittent audio",
        ]),
        ("Context", CARD_LT, [
            "Interview question asked",
            "Full answer transcript",
            "Signal summary (counts, durations)",
            "Longest clean streak (no flags)",
        ]),
    ]

    cw = (W - 1005840 - 3 * 130000) // 4
    ch = 3400000
    ct = 1580000
    sx = 502920

    for i, (title, fill, bullets) in enumerate(groups):
        x = sx + i * (cw + 130000)
        _rect(slide, x, ct, cw, ch, fill=fill)
        tb = _tb(slide, x + 90000, ct + 100000, cw - 180000, ch - 180000)
        _p0(tb.text_frame, title, 12, bold=True, color=NAVY)
        for b in bullets:
            _row(tb.text_frame, "", 5)        # spacer
            _row(tb.text_frame, f"• {b}", 9, bold=False, color=MID)

    _bottom_bar(slide,
        "Each signal type has a required prefix in the LLM output — "
        "the prompt lists only signals present in this specific clip, "
        "and coverage is enforced: one observation per flagged signal type.")


# ══════════════════════════════════════════════════════════════════════════════
# Slide 3 — Nemotron Mini: model choice & prompt design
# ══════════════════════════════════════════════════════════════════════════════
def slide_model(prs, page):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    _chrome(slide, "LLM & REASONING", page)
    _heading(slide, "Nemotron Mini 4B — Local LLM via Ollama")

    # Left: model facts card
    lw, lh, lt = 5200000, 3600000, 1600000
    _rect(slide, 502920, lt, lw, lh, fill=CARD_LT)
    tb_l = _tb(slide, 640000, lt + 120000, lw - 280000, lh - 240000)
    _p0(tb_l.text_frame, "NVIDIA Nemotron Mini 4B Instruct", 14, bold=True, color=NAVY)
    facts = [
        ("Size",         "4 billion parameters  ·  ~2.7 GB download"),
        ("Runtime",      "Ollama — runs locally on CPU, no cloud required"),
        ("Output",       "Strict JSON: observations / explanations / suggestions"),
        ("Format lock",  "format='json' enforces structured output every time"),
        ("Fallback",     "Deterministic mock output when server is offline"),
        ("Privacy",      "All inference stays on-device — no data sent externally"),
    ]
    for label, detail in facts:
        _row(tb_l.text_frame, "", 5)
        p = tb_l.text_frame._txBody.add_p()
        para = tb_l.text_frame.paragraphs[-1]
        r1 = para.add_run(); r1.text = f"{label}:  "; r1.font.size = Pt(10); r1.font.bold = True; r1.font.color.rgb = NAVY
        r2 = para.add_run(); r2.text = detail; r2.font.size = Pt(10); r2.font.color.rgb = MID

    # Right: prompt design boxes
    rw = W - lw - 502920 - 502920 - 200000
    rx = 502920 + lw + 200000

    prompts = [
        ("Closed Vocabulary",
         "Only SignalType enum tokens are allowed. "
         "The LLM cannot invent signal names not in the evidence.",
         CARD_MD),
        ("Coverage Enforcement",
         "Every signal type present in the clip must get one observation. "
         "The model cannot stop after 1–2 signals.",
         CARD_MD),
        ("Concrete Fix Rules",
         "Low-light → move toward a front light source. "
         "Low mic level → move closer or increase gain. "
         "Vague suggestions are not accepted.",
         CARD_MD),
    ]
    ph = (lh - 2 * 80000) // len(prompts)
    for i, (title, body, fill) in enumerate(prompts):
        y = lt + i * (ph + 80000)
        _rect(slide, rx, y, rw, ph, fill=fill)
        tb = _tb(slide, rx + 100000, y + 80000, rw - 200000, ph - 160000)
        _p0(tb.text_frame, title, 11, bold=True, color=NAVY)
        _row(tb.text_frame, body, 9, bold=False, color=MID)
        tb.text_frame.word_wrap = True

    _bottom_bar(slide,
        "Running locally via Ollama means zero latency from network round-trips, "
        "zero API cost, and zero privacy exposure — interview responses never leave the machine.")


# ══════════════════════════════════════════════════════════════════════════════
# Slide 4 — Validation layer + Coaching Report output
# ══════════════════════════════════════════════════════════════════════════════
def slide_output(prs, page):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    _chrome(slide, "LLM & REASONING", page)
    _heading(slide, "Validation Layer & Coaching Report")

    # Left: 4 validation checks
    checks = [
        ("Category check",       "Every claim references a known signal keyword — no invented behavior."),
        ("Timestamp check",       "Referenced timestamps must fall within the actual clip duration."),
        ("Confidence gate",       "Low-confidence detections reduce the reliability score automatically."),
        ("Coverage check",        "Claims need matching data points; unsupported observations are flagged."),
    ]
    chk_w = 5500000
    chk_h = 940000
    ct = 1600000

    for i, (title, body) in enumerate(checks):
        y = ct + i * (chk_h + 120000)
        fill = CARD_LT if i % 2 == 0 else CARD_MD
        _rect(slide, 502920, y, chk_w, chk_h, fill=fill)
        # numbered badge
        _rect(slide, 502920, y, 420000, chk_h, fill=BLUE)
        num = _tb(slide, 502920, y + 200000, 420000, 540000)
        _p0(num.text_frame, str(i + 1), 20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        # content
        tb = _tb(slide, 1020000, y + 100000, chk_w - 620000, chk_h - 200000)
        _p0(tb.text_frame, title, 12, bold=True, color=NAVY)
        _row(tb.text_frame, body, 10, bold=False, color=MID)
        tb.text_frame.word_wrap = True

    # Right: output card
    out_x = 502920 + chk_w + 250000
    out_w = W - out_x - 402920
    out_h = 4 * (chk_h + 120000) - 120000
    _rect(slide, out_x, ct, out_w, out_h, fill=CARD_GREY)

    tb_o = _tb(slide, out_x + 120000, ct + 120000, out_w - 240000, out_h - 240000)
    _p0(tb_o.text_frame, "Coaching Report Output", 13, bold=True, color=NAVY)
    outputs = [
        ("Observations",   "What happened and when, tied to each signal"),
        ("Explanations",   "Why it matters in an interview context"),
        ("Suggestions",    "One concrete, actionable improvement per signal"),
        ("Reliability",    "0 – 100% score based on validation checks"),
        ("Timeline",       "Interactive signal Gantt chart in the dashboard"),
        ("PDF Export",     "Branded downloadable report with all sections"),
    ]
    for label, detail in outputs:
        _row(tb_o.text_frame, "", 4)
        p = tb_o.text_frame._txBody.add_p()
        para = tb_o.text_frame.paragraphs[-1]
        r1 = para.add_run(); r1.text = f"{label}  "; r1.font.size = Pt(10); r1.font.bold = True; r1.font.color.rgb = BLUE
        r2 = para.add_run(); r2.text = detail; r2.font.size = Pt(10); r2.font.color.rgb = MID

    _bottom_bar(slide,
        "Reliability ≥ 0.75 → High confidence (green)  ·  "
        "0.50–0.75 → Moderate (amber)  ·  < 0.50 → Low (red).  "
        "Content is always shown above 0.3 reliability so coaching is never silently suppressed.")


# ══════════════════════════════════════════════════════════════════════════════
def main():
    src  = Path(r"C:\Users\shrey\Downloads\InterviewLens_Presentation.pptx")
    dest = Path(r"C:\Users\shrey\Downloads\InterviewLens_LLM_Slides.pptx")

    prs = Presentation(str(src))
    n   = len(prs.slides)
    print(f"Loaded {src.name}  ({n} slides)")

    # Remove any previously appended slides (keep original 17)
    rIds = [prs.slides._sldIdLst[i].get("r:id") for i in range(n - 1, 16, -1)]
    for rId in rIds:
        slide_part = prs.part.related_parts[rId]
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[prs.slides._sldIdLst.index(
            next(s for s in prs.slides._sldIdLst if s.get("r:id") == rId))]

    slide_overview(prs, 18); print("  Slide 18 — Pipeline Overview")
    slide_inputs  (prs, 19); print("  Slide 19 — Signal Inputs")
    slide_model   (prs, 20); print("  Slide 20 — Nemotron Mini + Prompt Design")
    slide_output  (prs, 21); print("  Slide 21 — Validation & Report")

    prs.save(str(dest))
    print(f"\nSaved → {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
