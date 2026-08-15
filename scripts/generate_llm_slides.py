"""
4 LLM & Reasoning slides.  Story arc:
  18 -- Detection gives data. Coaching needs more.
  19 -- The LLM can only say what it was told.
  20 -- What broke and what we changed.
  21 -- Three things every candidate receives.

Font sizes match the existing deck exactly.
Usage:  python scripts/generate_llm_slides.py
Output: C:/Users/shrey/Downloads/InterviewLens_LLM_Slides.pptx
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

BLUE     = RGBColor(0x2C, 0x7F, 0xB8)
NAVY     = RGBColor(0x14, 0x30, 0x4F)
NAVY_ICN = RGBColor(0x1F, 0x38, 0x64)
MID      = RGBColor(0x1A, 0x2B, 0x3C)
CARD_LT  = RGBColor(0xDC, 0xEB, 0xF7)
CARD_MD  = RGBColor(0xEA, 0xF2, 0xFA)
CARD_GRY = RGBColor(0xEE, 0xF1, 0xF4)
AMBER    = RGBColor(0xF0, 0xB4, 0x29)
AMBER_BG = RGBColor(0xFC, 0xF3, 0xDC)
RED      = RGBColor(0xF0, 0x3B, 0x20)
RED_BG   = RGBColor(0xFC, 0xE3, 0xDD)
GREEN    = RGBColor(0x21, 0x96, 0x53)
GREEN_BG = RGBColor(0xE6, 0xF4, 0xEA)
MUTED    = RGBColor(0x5B, 0x7A, 0x99)
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

def deco(sl):
    O(sl, 10252478, 5202936, 3840480, 3840480, BLUE)

def bar(sl, txt):
    R(sl, 502920, 5160000, W - 1005840, 1100000, f=NAVY)
    tf = P(T(sl, 700000, 5220000, W - 1400000, 1000000), txt, 14, False, WHITE)
    tf.word_wrap = True


# ─────────────────────────────────────────────────────────────────────────────
# 18  "Detection gives you data.  Coaching requires more."
# ─────────────────────────────────────────────────────────────────────────────
def s18(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg); deco(sl)

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "Detection Gives You Data.  Coaching Requires More.", 25, True, NAVY)

    R(sl, 502920, 1390000, W - 1005840, 400000, f=CARD_LT)
    tf_s = P(T(sl, 700000, 1420000, W - 1400000, 360000),
             "The pose and audio pipelines produce timestamped signals with confidence scores."
             "  That is necessary -- but it is not sufficient for a candidate to improve.", 14, False, NAVY)
    tf_s.word_wrap = True

    # Left dark card: raw detection output
    R(sl, 502920, 1930000, 3576218, 2700000, f=NAVY)
    P(T(sl, 640000, 2040000, 3300000, 420000), "WHAT DETECTION GIVES YOU", 16, True, CARD_LT)
    sh = T(sl, 640000, 2540000, 3300000, 2050000)
    tf = P(sh, "hands_near_face", 14, True, AMBER)
    N(tf, "  start=2.1s  end=4.8s  conf=0.82", 13, False, WHITE)
    N(tf, "", 6)
    N(tf, "head_tilt", 14, True, AMBER)
    N(tf, "  start=0.3s  end=7.1s  conf=0.71", 13, False, WHITE)
    N(tf, "", 6)
    N(tf, "body_lean", 14, True, AMBER)
    N(tf, "  start=1.0s  end=8.0s  conf=0.69", 13, False, WHITE)
    N(tf, "", 10)
    N(tf, "Filler words: 2", 13, False, CARD_MD)
    N(tf, "Speaking rate: 91 wpm", 13, False, CARD_MD)

    # Arrow
    P(T(sl, 4120000, 3080000, 200000, 300000), ">", 22, True, BLUE, PP_ALIGN.CENTER)

    # Middle card: what coaching needs
    R(sl, 4380000, 1930000, 3576218, 2700000, f=CARD_GRY)
    P(T(sl, 4520000, 2040000, 3300000, 420000), "WHAT COACHING REQUIRES", 16, True, NAVY)
    sh2 = T(sl, 4520000, 2540000, 3300000, 2050000)
    tf2 = P(sh2, "Detection has no context:", 14, False, MID)
    N(tf2, "", 6)
    N(tf2, "  No explanation of why the", 14, False, MID)
    N(tf2, "  signal hurts in interviews", 14, False, MID)
    N(tf2, "", 6)
    N(tf2, "  No indication of when it", 14, False, MID)
    N(tf2, "  peaks under question pressure", 14, False, MID)
    N(tf2, "", 6)
    N(tf2, "  No specific action to rehearse", 14, False, MID)
    N(tf2, "", 6)
    N(tf2, "  No sense of how reliable", 14, False, MID)
    N(tf2, "  the observation is", 14, False, MID)
    N(tf2, "", 10)
    N(tf2, "Rules cannot provide this.", 14, True, RED)

    # Arrow
    P(T(sl, 7990000, 3080000, 200000, 300000), ">", 22, True, BLUE, PP_ALIGN.CENTER)

    # Right card: solution
    R(sl, 8240000, 1930000, 3576218, 2700000, f=BLUE)
    P(T(sl, 8380000, 2040000, 3300000, 420000), "THE LLM REASONING STAGE", 16, True, WHITE)
    sh3 = T(sl, 8380000, 2540000, 3300000, 2050000)
    tf3 = P(sh3, "Reads the evidence.", 14, True, WHITE)
    N(tf3, "Explains each signal.", 14, True, WHITE)
    N(tf3, "Suggests one specific fix.", 14, True, WHITE)
    N(tf3, "", 8)
    N(tf3, "Every claim is grounded in", 14, False, CARD_LT)
    N(tf3, "a timestamped pipeline event.", 14, False, CARD_LT)
    N(tf3, "", 8)
    N(tf3, "Reliability-scored on output.", 14, False, CARD_LT)

    bar(sl, "Rules scale poorly: there are 34 distinct signal types across body language,"
        " framing, background, and audio.  An LLM that reasons over evidence handles"
        " combinations and context that a rule tree never could.")


# ─────────────────────────────────────────────────────────────────────────────
# 19  "The LLM Can Only Say What It Was Told."
# ─────────────────────────────────────────────────────────────────────────────
def s19(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg); deco(sl)

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "The LLM Can Only Say What It Was Told.", 25, True, NAVY)

    # Dark left: what multimodal models do vs. what we do
    R(sl, 502920, 1430000, 5100000, 3800000, f=NAVY)
    P(T(sl, 660000, 1540000, 4800000, 380000), "THE DESIGN DECISION", 16, True, CARD_LT)

    sh = T(sl, 660000, 2020000, 4800000, 3150000)
    tf = P(sh, "We do not show the LLM any video frames.", 14, True, WHITE)
    N(tf, "", 8)
    N(tf, "Multimodal models are trained to describe", 14, False, WHITE)
    N(tf, "images. Given interview footage, they describe", 14, False, WHITE)
    N(tf, "clothing, hairstyles, and furniture -- none of", 14, False, WHITE)
    N(tf, "which the candidate can act on.", 14, False, WHITE)
    N(tf, "", 8)
    N(tf, "Instead: a structured text document listing", 14, False, WHITE)
    N(tf, "every detected signal with its timestamps.", 14, False, WHITE)
    N(tf, "", 8)
    N(tf, "Result: reliability rose from 0.25 to 0.85+.", 14, True, AMBER)

    # Four constraints on the right
    R(sl, 5760000, 1430000, 6000000, 3800000, f=CARD_MD)
    P(T(sl, 5900000, 1520000, 5720000, 360000), "FOUR STRUCTURAL CONSTRAINTS", 16, True, NAVY)

    constraints = [
        (NAVY_ICN, "Closed vocabulary",
         "Every observation must start with a <signal_type>:"
         " token drawn from the evidence for this clip."),
        (NAVY_ICN, "Required coverage",
         "The prompt lists every signal type present."
         " The model must cover all of them -- no early stopping."),
        (NAVY_ICN, "Concrete fix mandate",
         "'low_light' requires 'move toward a front-facing"
         " light source' -- vague advice is not accepted."),
        (NAVY_ICN, "Validation gate",
         "Claims with no matching evidence, bad timestamps,"
         " or low-confidence sources are flagged."),
    ]
    CH = 760000
    for i, (bf, title, body) in enumerate(constraints):
        y = 1960000 + i * (CH + 60000)
        R(sl, 5760000, y, 5900000, CH, f=CARD_GRY)
        R(sl, 5760000, y, 340000, CH, f=bf)
        P(T(sl, 5760000, y + CH // 2 - 200000, 340000, 400000),
          str(i + 1), 20, True, WHITE, PP_ALIGN.CENTER)
        sh = T(sl, 6160000, y + 80000, 5480000, CH - 160000)
        tf = P(sh, title, 13, True, NAVY)
        N(tf, body, 13, False, MID)

    bar(sl, "The validation layer runs 4 checks on every claim before the report is shown."
        "  Reliability = max(0, 1.0 - 0.15 x failed checks)."
        "  The score is visible to the candidate so they know how much to trust each observation.")


# ─────────────────────────────────────────────────────────────────────────────
# 20  "What Broke and What We Changed."
# ─────────────────────────────────────────────────────────────────────────────
def s20(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg); deco(sl)

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "What Broke -- and What We Changed", 25, True, NAVY)

    # Dark champion card
    R(sl, 502920, 1480000, 3760000, 3550000, f=NAVY)
    R(sl, 502920, 1375000, 3760000, 105000,  f=BLUE)
    P(T(sl, 502920, 1270000, 3760000, 260000), "Champion", 16, True, NAVY)

    sh_c = T(sl, 650000, 1580000, 3460000, 3400000)
    tf_c = P(sh_c, "Nemotron Mini 4B", 20, True, WHITE)
    N(tf_c, "via Ollama  |  local  |  private", 13, False, CARD_MD)
    N(tf_c, "", 10)
    N(tf_c, "4 billion parameters", 14, False, WHITE)
    N(tf_c, "~2.7 GB  --  runs on-device", 14, False, WHITE)
    N(tf_c, "", 6)
    N(tf_c, "No data leaves the machine", 14, False, WHITE)
    N(tf_c, "No API key required", 14, False, WHITE)
    N(tf_c, "", 6)
    N(tf_c, "format='json' enforces", 14, False, WHITE)
    N(tf_c, "structured output on every call", 14, False, WHITE)
    N(tf_c, "", 6)
    N(tf_c, "Falls back to deterministic mock", 14, False, WHITE)
    N(tf_c, "when server is unreachable", 14, False, WHITE)

    # Three failure rows
    failures = [
        ("Model described the room, not the interview",
         "A multimodal model given frames observed 'wearing a white towel'"
         " and 'sandwich and coffee on the counter'."
         " Neither was in the evidence.  Reliability: 0.25."
         "  Fix: no images -- structured text only."),
        ("Model stopped after covering 2 signals out of 7",
         "Without enforcement, the model always led with the most obvious signal"
         " and finished early.  Coverage jumped from 2 to 7 signals per clip"
         " after REQUIRED COVERAGE listed every present signal type explicitly."),
        ("Worked examples made things worse, not better",
         "Adding a GOOD / BAD example pair to the prompt caused the model"
         " to copy the BAD example verbatim in its output."
         " A known small-model failure mode.  Fix: dynamic signal lists, no static examples."),
    ]
    RH = 1100000
    for i, (problem, fix) in enumerate(failures):
        y = 1400000 + i * (RH + 80000)
        R(sl, 4360000, y, 7440000, RH, f=CARD_MD)
        R(sl, 4360000, y, 360000, RH, f=NAVY_ICN)
        P(T(sl, 4360000, y + RH // 2 - 240000, 360000, 480000),
          str(i + 1), 22, True, WHITE, PP_ALIGN.CENTER)
        sh = T(sl, 4780000, y + 90000, 6920000, RH - 180000)
        tf = P(sh, problem, 14, True, NAVY)
        N(tf, fix, 13, False, MID)

    bar(sl, "Each failure led to a structural change in the system, not a better prompt."
        "  The constraints described on the previous slide emerged directly"
        " from these three observations during development.")


# ─────────────────────────────────────────────────────────────────────────────
# 21  "Three Things Every Candidate Receives."
# ─────────────────────────────────────────────────────────────────────────────
def s21(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg); deco(sl)

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "Three Things Every Candidate Receives", 25, True, NAVY)

    # Left: detected signals
    R(sl, 502920, 1420000, 5060000, 3780000, f=NAVY)
    P(T(sl, 660000, 1520000, 4780000, 360000), "DETECTED SIGNALS (this clip)", 16, True, CARD_LT)

    sh_l = T(sl, 660000, 1970000, 4780000, 3180000)
    tf_l = P(sh_l, "Signal               Time         Conf", 12, True, CARD_MD)
    N(tf_l, "hands_near_face    2.1s - 4.8s   0.82", 13, False, WHITE)
    N(tf_l, "head_tilt          0.3s - 7.1s   0.71", 13, False, WHITE)
    N(tf_l, "body_lean          1.0s - 8.0s   0.69", 13, False, WHITE)
    N(tf_l, "looking_down       5.2s - 8.0s   0.67", 13, False, WHITE)
    N(tf_l, "", 8)
    N(tf_l, "Filler words       2", 13, False, CARD_MD)
    N(tf_l, "Speaking rate      91 wpm", 13, False, CARD_MD)
    N(tf_l, "", 12)
    R(sl, 660000, 4790000, 1400000, 350000, f=GREEN)
    P(T(sl, 680000, 4820000, 1360000, 280000), "Reliability  0.85", 13, True, WHITE, PP_ALIGN.CENTER)

    # Right: three output sections
    OX = 502920 + 5060000 + 220000
    OW = W - OX - 402920
    SH = 1180000

    sections = [
        (BLUE,  WHITE,    "WHAT HAPPENED",
         "hands_near_face: You touched your face repeatedly"
         " during the opening 5 seconds of your answer."),
        (AMBER, NAVY,     "WHY IT MATTERS",
         "Repeated face-touching under pressure signals"
         " anxiety to interviewers and shifts attention"
         " away from what you are saying."),
        (GREEN, WHITE,    "WHAT TO DO",
         "Before you start, rest both hands flat on the desk."
         " When you notice them moving to your face,"
         " pause, reposition, then continue."),
    ]
    for i, (lf, lc, lbl, body) in enumerate(sections):
        y = 1420000 + i * (SH + 55000)
        R(sl, OX, y, OW, 360000, f=lf)
        P(T(sl, OX + 110000, y + 75000, OW - 220000, 260000), lbl, 16, True, lc)
        R(sl, OX, y + 360000, OW, SH - 360000, f=CARD_GRY)
        tf = P(T(sl, OX + 110000, y + 430000, OW - 220000, SH - 480000), body, 13, False, MID)
        tf.word_wrap = True

    bar(sl, "WHAT HAPPENED answers a factual question."
        "  WHY IT MATTERS connects the signal to interview perception."
        "  WHAT TO DO gives one specific, rehearsable action."
        "  Without all three, the candidate has data -- not a direction.")


# ─────────────────────────────────────────────────────────────────────────────
def main():
    src  = Path(r"C:\Users\shrey\Downloads\InterviewLens_Presentation.pptx")
    dest = Path(r"C:\Users\shrey\Downloads\InterviewLens_LLM_Slides.pptx")
    prs  = Presentation(str(src))
    while len(prs.slides) > 17:
        rId = prs.slides._sldIdLst[-1].get("r:id")
        del prs.slides._sldIdLst[-1]
        prs.part.drop_rel(rId)
    s18(prs, 18); print("  18 -- Detection gives data, coaching requires more")
    s19(prs, 19); print("  19 -- The LLM can only say what it was told")
    s20(prs, 20); print("  20 -- What broke and what we changed")
    s21(prs, 21); print("  21 -- Three things every candidate receives")
    prs.save(str(dest))
    print(f"\nSaved -> {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
