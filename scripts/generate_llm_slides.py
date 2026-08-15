"""
4 LLM & Reasoning slides — each with a distinct palette and layout.

  18  NAVY / RED / AMBER  — 3-column problem-gap-solution
  19  DARK full-width left + AMBER constraint boxes right
  20  NAVY champion + RED / AMBER / GREEN failure rows
  21  NAVY signal panel + BLUE / AMBER / GREEN output tiers

Usage:  python scripts/generate_llm_slides.py
Output: C:/Users/shrey/Downloads/InterviewLens_LLM_Slides.pptx
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# Palette
BLUE     = RGBColor(0x2C, 0x7F, 0xB8)
NAVY     = RGBColor(0x14, 0x30, 0x4F)
NAVY2    = RGBColor(0x1F, 0x38, 0x64)
MID      = RGBColor(0x1A, 0x2B, 0x3C)
CARD_LT  = RGBColor(0xDC, 0xEB, 0xF7)
CARD_GRY = RGBColor(0xEE, 0xF1, 0xF4)
AMBER    = RGBColor(0xF0, 0xB4, 0x29)
AMBER_BG = RGBColor(0xFC, 0xF3, 0xDC)
RED      = RGBColor(0xF0, 0x3B, 0x20)
RED_BG   = RGBColor(0xFC, 0xE3, 0xDD)
GREEN    = RGBColor(0x21, 0x96, 0x53)
GREEN_BG = RGBColor(0xE6, 0xF4, 0xEA)
MUTED    = RGBColor(0x5B, 0x7A, 0x99)
TEAL_BG  = RGBColor(0xE0, 0xF2, 0xF1)
TEAL     = RGBColor(0x00, 0x89, 0x7B)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
W = 12192000;  H = 6858000


def R(s, l, t, w, h, f=None, lc=None):
    sh = s.shapes.add_shape(1, l, t, w, h)
    sh.fill.solid() if f else sh.fill.background()
    if f: sh.fill.fore_color.rgb = f
    if lc: sh.line.color.rgb = lc; sh.line.width = Emu(12700)
    else: sh.line.fill.background()
    return sh

def O(s, l, t, w, h, f):
    sh = s.shapes.add_shape(9, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = f
    sh.line.fill.background(); return sh

def T(s, l, t, w, h):
    sh = s.shapes.add_textbox(l, t, w, h)
    sh.line.fill.background(); return sh

def P(sh, txt, pt, bold=False, clr=MID, al=PP_ALIGN.LEFT):
    tf = sh.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = al
    r = p.add_run()
    r.text = txt; r.font.size = Pt(pt); r.font.bold = bold; r.font.color.rgb = clr
    return tf

def N(tf, txt, pt, bold=False, clr=MID, al=PP_ALIGN.LEFT):
    tf._txBody.add_p(); p = tf.paragraphs[-1]; p.alignment = al
    if txt:
        r = p.add_run()
        r.text = txt; r.font.size = Pt(pt); r.font.bold = bold; r.font.color.rgb = clr
    return tf

def chrome(sl, sec, pg):
    O(sl, 514495, 419029, 615315, 615315, BLUE)
    P(T(sl, 1252728, 588523, 9601200, 256032), sec, 20, True, BLUE)
    P(T(sl, 11140135, 6528816, 548640, 256032), str(pg), 9, False, MUTED, PP_ALIGN.RIGHT)

def deco(sl, col=BLUE):
    O(sl, 10252478, 5202936, 3840480, 3840480, col)

def bar(sl, txt, bg=NAVY, fg=WHITE):
    R(sl, 502920, 5160000, W - 1005840, 1100000, f=bg)
    tf = P(T(sl, 700000, 5220000, W - 1400000, 1000000), txt, 14, False, fg)
    tf.word_wrap = True


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 18  PALETTE: NAVY / RED / AMBER
# Layout: 3 equal columns — data  |  gap  |  solution
# ═══════════════════════════════════════════════════════════════════════════
def s18(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg)
    deco(sl, AMBER)   # amber decorative circle — distinct from the blue on other slides

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "Detection Gives You Data.  Coaching Requires More.", 25, True, NAVY)

    R(sl, 502920, 1390000, W - 1005840, 400000, f=CARD_LT)
    tf_s = P(T(sl, 700000, 1420000, W - 1400000, 360000),
             "The pose and audio pipelines produce timestamped signals with confidence scores."
             "  That is necessary — but not sufficient for a candidate to improve.", 14, False, NAVY)
    tf_s.word_wrap = True

    # Column 1 — DARK NAVY  (what you get)
    L1 = 502920
    R(sl, L1, 1920000, 3576218, 2700000, f=NAVY)
    P(T(sl, L1+140000, 2040000, 3300000, 420000), "WHAT YOU GET", 18, True, CARD_LT)
    sh = T(sl, L1+140000, 2530000, 3300000, 2040000)
    tf = P(sh, "hands_near_face", 14, True, AMBER)
    N(tf, "  2.1s - 4.8s  conf=0.82", 13, False, WHITE)
    N(tf, "", 6)
    N(tf, "head_tilt", 14, True, AMBER)
    N(tf, "  0.3s - 7.1s  conf=0.71", 13, False, WHITE)
    N(tf, "", 6)
    N(tf, "body_lean", 14, True, AMBER)
    N(tf, "  1.0s - 8.0s  conf=0.69", 13, False, WHITE)
    N(tf, "", 10)
    N(tf, "Filler words: 2  |  91 wpm", 13, False, CARD_LT)

    P(T(sl, L1+140000, 4550000, 3300000, 260000), ">", 22, True, AMBER, PP_ALIGN.CENTER)

    # Column 2 — RED  (the gap)
    L2 = L1 + 3576218 + 200000
    R(sl, L2, 1920000, 3576218, 2700000, f=RED)
    P(T(sl, L2+140000, 2040000, 3300000, 420000), "THE GAP", 18, True, WHITE)
    sh2 = T(sl, L2+140000, 2530000, 3300000, 2040000)
    tf2 = P(sh2, "No context — why does this", 14, False, WHITE)
    N(tf2, "signal matter for interviews?", 14, False, WHITE)
    N(tf2, "", 8)
    N(tf2, "No pattern — does it peak", 14, False, WHITE)
    N(tf2, "when the questions get harder?", 14, False, WHITE)
    N(tf2, "", 8)
    N(tf2, "No action — what exactly", 14, False, WHITE)
    N(tf2, "should the candidate rehearse?", 14, False, WHITE)
    N(tf2, "", 10)
    N(tf2, "Rules cannot bridge this.", 14, True, AMBER_BG)

    P(T(sl, L2+140000, 4550000, 3300000, 260000), ">", 22, True, WHITE, PP_ALIGN.CENTER)

    # Column 3 — AMBER  (the solution)
    L3 = L2 + 3576218 + 200000
    R(sl, L3, 1920000, 3576218, 2700000, f=AMBER)
    P(T(sl, L3+140000, 2040000, 3300000, 420000), "THE SOLUTION", 18, True, NAVY)
    sh3 = T(sl, L3+140000, 2530000, 3300000, 2040000)
    tf3 = P(sh3, "An LLM that reads the evidence", 14, False, NAVY)
    N(tf3, "and explains each signal with:", 14, False, NAVY)
    N(tf3, "", 10)
    N(tf3, "  Context and timing", 14, True, NAVY)
    N(tf3, "  Why it affects perception", 14, True, NAVY)
    N(tf3, "  One specific fix to rehearse", 14, True, NAVY)
    N(tf3, "", 10)
    N(tf3, "Every claim grounded in a", 14, False, NAVY)
    N(tf3, "timestamped pipeline event.", 14, False, NAVY)

    bar(sl, "34 distinct signal types across body language, framing, background, and audio."
        "  An LLM that reasons over evidence handles combinations and context"
        " that a rule tree never could.", bg=RED, fg=WHITE)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 19  PALETTE: DARK full-width left + AMBER right
# Layout: wide dark panel | 4 amber constraint blocks
# ═══════════════════════════════════════════════════════════════════════════
def s19(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg)
    deco(sl, RED)   # red decorative circle

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "The LLM Can Only Say What It Was Told.", 25, True, NAVY)

    # Full-height dark left panel
    LW = 4600000
    R(sl, 502920, 1420000, LW, 3800000, f=NAVY)
    P(T(sl, 660000, 1530000, LW-320000, 380000), "THE DESIGN DECISION", 16, True, CARD_LT)

    sh = T(sl, 660000, 2010000, LW-320000, 3160000)
    tf = P(sh, "We do not show the LLM any video frames.", 14, True, WHITE)
    N(tf, "", 8)
    N(tf, "Multimodal models are trained to describe", 14, False, WHITE)
    N(tf, "images. Given interview footage, they describe", 14, False, WHITE)
    N(tf, "clothing, furniture, and food — none of which", 14, False, WHITE)
    N(tf, "the candidate can act on.", 14, False, WHITE)
    N(tf, "", 8)
    N(tf, "Instead, the LLM receives a structured text", 14, False, WHITE)
    N(tf, "document: every detected signal, its timestamps,", 14, False, WHITE)
    N(tf, "and confidence score. Nothing else.", 14, False, WHITE)
    N(tf, "", 12)
    N(tf, "Result: reliability rose from 0.25 to 0.85+", 14, True, AMBER)

    # 4 amber constraint blocks (right)
    RX = 502920 + LW + 240000
    RW = W - RX - 402920
    CH = 870000

    constraints = [
        (AMBER,    NAVY,     "CLOSED VOCABULARY",
         "Every observation must start with a <signal_type>: token"
         " drawn from this clip's evidence. No invented signal names."),
        (RED,      WHITE,    "REQUIRED COVERAGE",
         "The prompt lists every signal type present in this clip."
         " The model must cover all of them. No early stopping."),
        (GREEN,    WHITE,    "CONCRETE FIX MANDATE",
         "'low_light' must produce 'move toward a front-facing light source'."
         " Vague advice is structurally blocked."),
        (NAVY2,    WHITE,    "VALIDATION GATE",
         "Claims with no evidence match, bad timestamps, or low confidence"
         " reduce the reliability score before the report is shown."),
    ]
    for i, (hf, hc, title, body) in enumerate(constraints):
        y = 1420000 + i * (CH + 75000)
        R(sl, RX, y, RW, CH, f=CARD_GRY)
        R(sl, RX, y, RW, 340000, f=hf)
        P(T(sl, RX+120000, y+70000, RW-240000, 260000), title, 14, True, hc)
        tf = P(T(sl, RX+120000, y+380000, RW-240000, CH-430000), body, 13, False, MID)
        tf.word_wrap = True

    bar(sl, "The validation layer runs 4 checks on every claim."
        "  Reliability = max(0, 1.0 - 0.15 x failed checks)."
        "  The score is shown to candidates so they know how much to trust each observation.",
        bg=AMBER, fg=NAVY)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 20  PALETTE: NAVY champion + RED / AMBER / GREEN failure rows
# Layout: champion card left | 3 distinctly-coloured failure rows right
# ═══════════════════════════════════════════════════════════════════════════
def s20(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg)
    deco(sl, GREEN)  # green decorative circle

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "What Broke — and What We Changed", 25, True, NAVY)

    # Champion card
    R(sl, 502920, 1480000, 3760000, 3550000, f=NAVY)
    R(sl, 502920, 1375000, 3760000, 105000,  f=BLUE)
    P(T(sl, 502920, 1265000, 3760000, 260000), "Champion", 16, True, NAVY)

    sh_c = T(sl, 650000, 1580000, 3460000, 3400000)
    tf_c = P(sh_c, "Nemotron Mini 4B", 20, True, WHITE)
    N(tf_c, "via Ollama  |  local  |  private", 13, False, CARD_LT)
    N(tf_c, "", 10)
    N(tf_c, "4 billion parameters", 14, False, WHITE)
    N(tf_c, "~2.7 GB  —  runs on-device", 14, False, WHITE)
    N(tf_c, "", 6)
    N(tf_c, "No data leaves the machine", 14, False, WHITE)
    N(tf_c, "No API key required", 14, False, WHITE)
    N(tf_c, "", 6)
    N(tf_c, "format='json' enforces structured", 14, False, WHITE)
    N(tf_c, "output on every inference call", 14, False, WHITE)
    N(tf_c, "", 6)
    N(tf_c, "Deterministic fallback when", 14, False, WHITE)
    N(tf_c, "server is unreachable", 14, False, WHITE)

    # 3 failure rows — each a different colour
    rows = [
        (RED,   RED_BG,   WHITE, MID,
         "Model described the room, not the interview",
         "Given frames, it observed 'wearing a white towel' and 'sandwich and coffee'."
         " Neither was in the evidence.  Reliability: 0.25."
         "  Fix: no images — structured text document only."),
        (AMBER, AMBER_BG, NAVY,  MID,
         "Model stopped after covering 2 signals out of 7",
         "Without enforcement, it always led with the most obvious signal and stopped."
         " REQUIRED COVERAGE listed every present signal type explicitly."
         " Coverage rose from 2 to 7 per clip."),
        (GREEN, GREEN_BG, WHITE, MID,
         "Worked examples made things worse, not better",
         "A GOOD / BAD example pair caused the model to copy the BAD sentence verbatim."
         " A known small-model failure mode.  Fix: dynamic signal lists, no static examples."),
    ]
    RH = 1100000
    for i, (hf, bf, hc, bc, problem, fix) in enumerate(rows):
        y = 1400000 + i * (RH + 80000)
        R(sl, 4360000, y, 7440000, RH, f=bf)
        R(sl, 4360000, y, 7440000, 340000, f=hf)
        P(T(sl, 4480000, y+70000, 7200000, 260000), problem, 14, True, hc)
        tf = P(T(sl, 4480000, y+380000, 7200000, RH-440000), fix, 13, False, bc)
        tf.word_wrap = True

    bar(sl, "Each failure led to a structural change in the system, not a better prompt."
        "  The constraints on the previous slide emerged directly from these three observations.",
        bg=GREEN, fg=NAVY)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 21  PALETTE: NAVY signal panel + BLUE / AMBER / GREEN tiers
# Layout: signal data dark left | 3 coloured output tiers right
# ═══════════════════════════════════════════════════════════════════════════
def s21(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg)
    deco(sl, TEAL)   # teal decorative circle — fourth distinct accent

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "Three Things Every Candidate Receives", 25, True, NAVY)

    # Left dark signal panel
    R(sl, 502920, 1420000, 5060000, 3780000, f=NAVY)
    P(T(sl, 660000, 1520000, 4780000, 360000), "DETECTED SIGNALS  (this clip)", 16, True, CARD_LT)

    sh_l = T(sl, 660000, 1970000, 4780000, 3180000)
    tf_l = P(sh_l, "Signal               Time         Conf", 12, True, CARD_LT)
    N(tf_l, "hands_near_face    2.1s - 4.8s   0.82", 13, False, WHITE)
    N(tf_l, "head_tilt          0.3s - 7.1s   0.71", 13, False, WHITE)
    N(tf_l, "body_lean          1.0s - 8.0s   0.69", 13, False, WHITE)
    N(tf_l, "looking_down       5.2s - 8.0s   0.67", 13, False, WHITE)
    N(tf_l, "", 8)
    N(tf_l, "Filler words:  2", 13, False, CARD_LT)
    N(tf_l, "Speaking rate: 91 wpm", 13, False, CARD_LT)
    N(tf_l, "", 12)

    # Reliability badge in teal
    R(sl, 660000, 4800000, 2000000, 340000, f=TEAL)
    P(T(sl, 680000, 4830000, 1960000, 280000), "Reliability  0.85", 14, True, WHITE, PP_ALIGN.CENTER)

    # Right: 3 output tiers
    OX = 502920 + 5060000 + 220000
    OW = W - OX - 402920
    SH = 1185000

    tiers = [
        (BLUE,   WHITE, "WHAT HAPPENED",
         "hands_near_face: You touched your face repeatedly"
         " during the opening 5 seconds of your answer."),
        (AMBER,  NAVY,  "WHY IT MATTERS",
         "Repeated face-touching under pressure signals"
         " anxiety to interviewers and draws attention"
         " away from what you are saying."),
        (GREEN,  WHITE, "WHAT TO DO",
         "Before you start, rest both hands flat on the desk."
         " When you notice them moving to your face,"
         " pause, reposition, then continue."),
    ]
    for i, (hf, hc, label, body) in enumerate(tiers):
        y = 1420000 + i * (SH + 53000)
        R(sl, OX, y, OW, 370000, f=hf)
        P(T(sl, OX+110000, y+80000, OW-220000, 270000), label, 16, True, hc)
        R(sl, OX, y+370000, OW, SH-370000, f=CARD_GRY)
        tf = P(T(sl, OX+110000, y+440000, OW-220000, SH-500000), body, 13, False, MID)
        tf.word_wrap = True

    bar(sl, "WHAT HAPPENED answers a factual question."
        "  WHY IT MATTERS connects the signal to interview perception."
        "  WHAT TO DO gives one specific, rehearsable action."
        "  Without all three, the candidate has data — not a direction.",
        bg=TEAL, fg=WHITE)


# ─────────────────────────────────────────────────────────────────────────────
def main():
    src  = Path(r"C:\Users\shrey\Downloads\InterviewLens_Presentation.pptx")
    dest = Path(r"C:\Users\shrey\Downloads\InterviewLens_LLM_Slides.pptx")
    prs  = Presentation(str(src))
    while len(prs.slides) > 17:
        rId = prs.slides._sldIdLst[-1].get("r:id")
        del prs.slides._sldIdLst[-1]
        prs.part.drop_rel(rId)
    s18(prs, 18); print("  18  NAVY / RED / AMBER")
    s19(prs, 19); print("  19  DARK panel + AMBER constraint boxes")
    s20(prs, 20); print("  20  NAVY champion + RED/AMBER/GREEN rows")
    s21(prs, 21); print("  21  NAVY signal panel + BLUE/AMBER/GREEN tiers")
    prs.save(str(dest))
    print(f"\nSaved -> {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
