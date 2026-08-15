"""
4 LLM & Reasoning slides for the InterviewLens academic presentation.
Font sizes match the deck exactly (body=14pt, headlines=20-25pt, card labels=18pt).

Usage:  python scripts/generate_llm_slides.py
Output: C:/Users/shrey/Downloads/InterviewLens_LLM_Slides.pptx
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# Deck palette
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
W = 12192000
H =  6858000


# ── Primitives ─────────────────────────────────────────────────────────────────
def rect(s, l, t, w, h, fill=None, lc=None, lw=12700):
    sh = s.shapes.add_shape(1, l, t, w, h)
    sh.fill.solid() if fill else sh.fill.background()
    if fill: sh.fill.fore_color.rgb = fill
    if lc: sh.line.color.rgb = lc; sh.line.width = Emu(lw)
    else: sh.line.fill.background()
    return sh

def oval(s, l, t, w, h, fill):
    sh = s.shapes.add_shape(9, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background(); return sh

def tb(s, l, t, w, h):
    sh = s.shapes.add_textbox(l, t, w, h)
    sh.line.fill.background(); return sh

def first(sh, text, pt, bold=False, color=MID, align=PP_ALIGN.LEFT):
    tf = sh.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run()
    r.text = text; r.font.size = Pt(pt); r.font.bold = bold
    r.font.color.rgb = color
    return tf

def nxt(tf, text, pt, bold=False, color=MID, align=PP_ALIGN.LEFT):
    tf._txBody.add_p()
    p = tf.paragraphs[-1]; p.alignment = align
    if text:
        r = p.add_run()
        r.text = text; r.font.size = Pt(pt); r.font.bold = bold
        r.font.color.rgb = color
    return tf

def chrome(slide, section, page):
    oval(slide, 514495, 419029, 615315, 615315, BLUE)
    first(tb(slide, 1252728, 588523, 9601200, 256032), section, 20, True, BLUE)
    first(tb(slide, 11140135, 6528816, 548640, 256032), str(page), 9, False, MUTED, PP_ALIGN.RIGHT)

def deco(slide):
    oval(slide, 10252478, 5202936, 3840480, 3840480, BLUE)

def insight(slide, text):
    rect(slide, 502920, 5160000, W - 1005840, 1080000, fill=NAVY)
    sh = tb(slide, 700000, 5230000, W - 1400000, 960000)
    tf = first(sh, text, 13, False, WHITE)
    tf.word_wrap = True


# =============================================================================
# SLIDE 18  Evidence-Grounded Coaching Reasoning
# Three-card layout matching slide 7 (champion/baseline/image columns)
# =============================================================================
def s18(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg)
    deco(sl)

    # Main headline -- 25pt bold, matches deck's large results headlines
    first(tb(sl, 1080412, 820000, 10037619, 460000),
          "Evidence-Grounded Coaching Reasoning", 25, True, NAVY)

    # Sub-headline bar (DCEBF7, matches slide 9)
    rect(sl, 502920, 1390000, W - 1005840, 400000, fill=CARD_LT)
    sh_s = tb(sl, 700000, 1420000, W - 1400000, 360000)
    first(sh_s,
          "Detecting a signal is not coaching. The reasoning stage turns"
          " timestamped evidence into explanations and specific actions.", 14, False, NAVY)

    # Three columns, slide-7 geometry
    cols = [
        (502920,  NAVY,     "THE CHALLENGE",  WHITE, [
            ("Detection produces:", False, WHITE),
            ("timestamps + signal type", False, WHITE),
            ("+ confidence score", False, WHITE),
            ("", False, WHITE),
            ("It cannot tell you why", False, WHITE),
            ("or what to do about it", False, WHITE),
        ]),
        (4307738, CARD_GRY, "THE APPROACH",   NAVY,  [
            ("Ground every LLM claim in a", False, MID),
            ("timestamped, confidence-gated", False, MID),
            ("pipeline event", False, MID),
            ("", False, MID),
            ("No claim without evidence", True,  NAVY),
        ]),
        (8112557, CARD_MD,  "THE OUTPUT",     NAVY,  [
            ("For each signal:", False, MID),
            ("What happened and when", False, MID),
            ("Why it matters for interviews", False, MID),
            ("One concrete fix to rehearse", False, MID),
            ("", False, MID),
            ("Reliability-scored", True, BLUE),
        ]),
    ]
    for l, fill, title, tc, rows in cols:
        rect(sl, l, 1920000, 3576218, 2700000, fill=fill)
        first(tb(sl, l + 140000, 2040000, 3296218, 480000), title, 18, True, tc)
        sh = tb(sl, l + 140000, 2580000, 3296218, 2000000)
        tf = first(sh, rows[0][0], 14, rows[0][1], rows[0][2])
        for text, bold, clr in rows[1:]:
            nxt(tf, text, 14, bold, clr)

    # Arrows
    for ax in [4040000, 7846000]:
        first(tb(sl, ax + 60000, 3100000, 148000, 280000), ">", 20, True, BLUE, PP_ALIGN.CENTER)

    insight(sl,
        "Key design decision: the LLM receives no video frames -- only structured text."
        " This means every coaching claim is auditable: a reviewer can check it"
        " against the original signal timestamps.")


# =============================================================================
# SLIDE 19  Why the LLM Cannot Hallucinate
# Four-column tier layout matching slide 10 (Neutral / Negative / Distracting)
# =============================================================================
def s19(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg)
    deco(sl)

    first(tb(sl, 1080412, 820000, 10037619, 460000),
          "Why the LLM Cannot Hallucinate", 25, True, NAVY)

    sh_i = tb(sl, 700000, 1360000, W - 1400000, 380000)
    first(sh_i,
          "The system constrains what the model can say before it generates a single token."
          " Constraints are structural -- not guidelines.", 14, False, NAVY)

    CW, GAP, SX = 2750000, 105000, 466344
    LH, BH = 480000, 3200000
    LY, BY = 1880000, 2360000

    cols = [
        (BLUE,  CARD_MD,  "WHAT IT RECEIVES",   14, [
            "A text document listing",
            "every detected event:",
            "",
            "  hands_near_face",
            "  start=2.1s  end=4.8s",
            "  confidence=0.82",
            "",
            "No images. No video.",
        ]),
        (AMBER, AMBER_BG, "WHAT IT MUST DO",    14, [
            "Every observation must",
            "start with a <signal_type>:",
            "token from the evidence",
            "",
            "One observation per",
            "signal type present --",
            "no early stopping",
        ]),
        (RED,   RED_BG,   "WHAT IS BLOCKED",    14, [
            "Clothing, hair, skin",
            "Food, furniture, decor",
            "",
            "Any claim with no",
            "matching event in the",
            "evidence document",
        ]),
        (GREEN, GREEN_BG, "HOW IT IS CHECKED",  14, [
            "Validation layer runs",
            "4 checks on every claim",
            "",
            "Failed checks reduce",
            "the reliability score",
            "shown to the user",
        ]),
    ]
    for i, (lf, bf, title, bsz, rows) in enumerate(cols):
        x = SX + i * (CW + GAP)
        rect(sl, x, LY, CW, LH, fill=lf)
        first(tb(sl, x + 80000, LY + 80000, CW - 160000, LH - 120000),
              title, 14, True, WHITE, PP_ALIGN.CENTER)
        rect(sl, x, BY, CW, BH, fill=bf)
        sh = tb(sl, x + 100000, BY + 130000, CW - 200000, BH - 200000)
        tf = first(sh, rows[0], bsz, False, NAVY)
        for row in rows[1:]:
            nxt(tf, row, bsz, False, NAVY)

    insight(sl,
        "Early tests with a multimodal model produced observations like"
        " 'wearing a white towel' and 'sandwich and coffee on the counter'"
        " -- neither was in the evidence."
        " Removing image tokens from the prompt eliminated appearance hallucinations entirely.")


# =============================================================================
# SLIDE 20  Three Failures We Observed -- and Fixed
# Champion card + numbered problem/fix rows
# =============================================================================
def s20(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg)
    deco(sl)

    first(tb(sl, 1080412, 820000, 10037619, 460000),
          "Three Failures Observed -- and How We Fixed Them", 25, True, NAVY)

    # Dark champion card
    rect(sl, 502920, 1480000, 3800000, 3500000, fill=NAVY)
    rect(sl, 502920, 1370000, 3800000, 110000,  fill=BLUE)
    first(tb(sl, 502920, 1260000, 3800000, 280000), "Champion", 16, True, NAVY)

    sh_c = tb(sl, 650000, 1580000, 3500000, 3300000)
    tf_c = first(sh_c, "Nemotron Mini 4B", 20, True, WHITE)
    nxt(tf_c, "via Ollama  |  local  |  private", 13, False, CARD_MD)
    nxt(tf_c, "", 8)
    nxt(tf_c, "Runs on-device -- no data leaves", 14, False, WHITE)
    nxt(tf_c, "the machine, no API key needed.", 14, False, WHITE)
    nxt(tf_c, "", 8)
    nxt(tf_c, "format='json' enforces structured", 14, False, WHITE)
    nxt(tf_c, "output on every inference call.", 14, False, WHITE)
    nxt(tf_c, "", 8)
    nxt(tf_c, "Offline fallback: when the server", 14, False, WHITE)
    nxt(tf_c, "is unreachable, deterministic mock", 14, False, WHITE)
    nxt(tf_c, "output keeps the pipeline running.", 14, False, WHITE)

    # Three failure rows
    rows = [
        ("Model free-wrote about the scene",
         "REQUIRED FORMAT: every observation must begin with a <signal_type>: token"
         " drawn from this clip's evidence."
         " The model cannot describe what it sees -- only what was measured."),
        ("Model stopped after 1-2 signals out of 7",
         "REQUIRED COVERAGE: the prompt lists every signal type flagged in the clip"
         " and mandates one observation each."
         " Coverage rose from 2 to 7 signals after this rule was added."),
        ("Suggestions were too vague to act on",
         "CONCRETE FIX MANDATE: lighting and audio signals require a specific remedy."
         " 'low_light' must produce 'move toward a front-facing light source'"
         " -- not 'consider improving your lighting'."),
    ]
    RH = 1100000
    for i, (problem, fix) in enumerate(rows):
        y = 1400000 + i * (RH + 80000)
        rect(sl, 4450000, y, 7300000, RH, fill=CARD_MD)
        rect(sl, 4450000, y, 380000, RH, fill=NAVY_ICN)
        first(tb(sl, 4460000, y + RH // 2 - 240000, 360000, 480000),
              str(i + 1), 22, True, WHITE, PP_ALIGN.CENTER)
        sh = tb(sl, 4900000, y + 100000, 6750000, RH - 200000)
        tf = first(sh, problem, 14, True, NAVY)
        nxt(tf, fix, 13, False, MID)

    insight(sl,
        "A worked GOOD/BAD example pair in the prompt made things worse:"
        " the model copied the example verbatim, word-for-word, including the BAD sentence."
        " Dynamic signal-name lists replaced all static examples.")


# =============================================================================
# SLIDE 21  A Coaching Report -- What a Candidate Receives
# Shows a concrete real-world example of the full output
# =============================================================================
def s21(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg)
    deco(sl)

    first(tb(sl, 1080412, 820000, 10037619, 460000),
          "A Coaching Report -- What a Candidate Receives", 25, True, NAVY)

    # Signal input (left)
    rect(sl, 502920, 1430000, 5200000, 3700000, fill=NAVY)
    first(tb(sl, 660000, 1530000, 5000000, 380000), "SIGNAL DETECTED", 14, True, CARD_LT)

    sh_sig = tb(sl, 660000, 1980000, 4900000, 3100000)
    tf_sig = first(sh_sig, "Type:         hands_near_face", 13, False, WHITE)
    nxt(tf_sig, "Duration:     2.1 s  --  4.8 s", 13, False, WHITE)
    nxt(tf_sig, "Confidence:   0.82", 13, False, WHITE)
    nxt(tf_sig, "", 8)
    nxt(tf_sig, "Also flagged in this clip:", 13, False, CARD_MD)
    nxt(tf_sig, "  head_tilt       0.3s -- 7.1s", 13, False, WHITE)
    nxt(tf_sig, "  body_lean       1.0s -- 8.0s", 13, False, WHITE)
    nxt(tf_sig, "  looking_down    5.2s -- 8.0s", 13, False, WHITE)
    nxt(tf_sig, "", 8)
    nxt(tf_sig, "Audio:  91 wpm  |  2 fillers", 13, False, CARD_MD)
    nxt(tf_sig, "Reliability score:  0.85", 13, True, AMBER)

    # Three output sections (right)
    OX = 502920 + 5200000 + 220000
    OW = W - OX - 402920

    sections = [
        (BLUE,    WHITE,    "WHAT HAPPENED",
         "hands_near_face: You touched your face 14 times"
         " in the opening 5 seconds of your answer."),
        (AMBER,   NAVY,     "WHY IT MATTERS",
         "Repeated face-touching under pressure signals"
         " anxiety to interviewers and draws attention"
         " away from your words."),
        (GREEN,   WHITE,    "WHAT TO DO",
         "Before you answer, rest both hands flat on the desk."
         " If they move to your face, pause, reposition, then continue."),
    ]
    SH = 1160000
    for i, (lf, lc, label, body) in enumerate(sections):
        y = 1430000 + i * (SH + 50000)
        rect(sl, OX, y, OW, 360000, fill=lf)
        first(tb(sl, OX + 110000, y + 80000, OW - 220000, 260000), label, 14, True, lc)
        rect(sl, OX, y + 360000, OW, SH - 360000, fill=CARD_GRY)
        sh = tb(sl, OX + 110000, y + 420000, OW - 220000, SH - 460000)
        first(sh, body, 13, False, MID)

    insight(sl,
        "The three-part structure (what / why / what to do) is deliberate:"
        " observation alone does not change behaviour."
        " Candidates leave every session with one specific, rehearsable target.")


# =============================================================================
def main():
    src  = Path(r"C:\Users\shrey\Downloads\InterviewLens_Presentation.pptx")
    dest = Path(r"C:\Users\shrey\Downloads\InterviewLens_LLM_Slides.pptx")
    prs  = Presentation(str(src))

    while len(prs.slides) > 17:
        rId = prs.slides._sldIdLst[-1].get("r:id")
        del prs.slides._sldIdLst[-1]
        prs.part.drop_rel(rId)

    s18(prs, 18); print("  18 -- Evidence-Grounded Coaching Reasoning")
    s19(prs, 19); print("  19 -- Why the LLM Cannot Hallucinate")
    s20(prs, 20); print("  20 -- Three Failures Fixed")
    s21(prs, 21); print("  21 -- A Coaching Report Example")

    prs.save(str(dest))
    print(f"\nSaved -> {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
