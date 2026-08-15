"""
4 LLM & Reasoning slides for InterviewLens_Presentation.pptx.
Matches exact deck style: dark navy hero cards, colored tier columns,
numbered badge strips, decorative corner circle.

Usage:  python scripts/generate_llm_slides.py
Output: C:/Users/shrey/Downloads/InterviewLens_LLM_Slides.pptx
"""
from __future__ import annotations
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# Exact palette from the deck
BLUE      = RGBColor(0x2C, 0x7F, 0xB8)
DARK_NAV  = RGBColor(0x14, 0x30, 0x4F)
NAVY_ICN  = RGBColor(0x1F, 0x38, 0x64)
MID       = RGBColor(0x1A, 0x2B, 0x3C)
CARD_LT   = RGBColor(0xDC, 0xEB, 0xF7)
CARD_MD   = RGBColor(0xEA, 0xF2, 0xFA)
CARD_GRY  = RGBColor(0xEE, 0xF1, 0xF4)
AMBER     = RGBColor(0xF0, 0xB4, 0x29)
AMBER_BG  = RGBColor(0xFC, 0xF3, 0xDC)
RED       = RGBColor(0xF0, 0x3B, 0x20)
RED_BG    = RGBColor(0xFC, 0xE3, 0xDD)
GREEN     = RGBColor(0x21, 0x96, 0x53)
GREEN_BG  = RGBColor(0xE6, 0xF4, 0xEA)
MUTED     = RGBColor(0x5B, 0x7A, 0x99)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
W = 12192000
H =  6858000


def _rect(s, l, t, w, h, fill=None, lc=None):
    sh = s.shapes.add_shape(1, l, t, w, h)
    sh.fill.solid() if fill else sh.fill.background()
    if fill: sh.fill.fore_color.rgb = fill
    if lc: sh.line.color.rgb = lc; sh.line.width = Emu(12700)
    else: sh.line.fill.background()
    return sh

def _oval(s, l, t, w, h, fill):
    sh = s.shapes.add_shape(9, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    return sh

def _tb(s, l, t, w, h):
    sh = s.shapes.add_textbox(l, t, w, h)
    sh.line.fill.background()
    return sh

def _p(sh, txt, sz, bold=False, clr=MID, align=PP_ALIGN.LEFT):
    tf = sh.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = txt
    r.font.size = Pt(sz); r.font.bold = bold; r.font.color.rgb = clr
    return tf

def _row(tf, txt, sz, bold=False, clr=MID):
    tf._txBody.add_p()
    para = tf.paragraphs[-1]
    if txt:
        r = para.add_run(); r.text = txt
        r.font.size = Pt(sz); r.font.bold = bold; r.font.color.rgb = clr
    return para

def _chrome(slide, section, page):
    _oval(slide, 514495, 419029, 615315, 615315, BLUE)
    _p(_tb(slide, 1252728, 588523, 9601200, 256032), section, 18, True, BLUE)
    _p(_tb(slide, 11140135, 6528816, 548640, 256032), str(page), 9, False, MUTED, PP_ALIGN.RIGHT)

def _deco(slide):
    _oval(slide, 10252478, 5202936, 3840480, 3840480, BLUE)

def _bar(slide, txt):
    _rect(slide, 502920, 5180000, W - 1005840, 1050000, fill=DARK_NAV)
    tf = _p(_tb(slide, 700000, 5260000, W - 1400000, 900000), txt, 11, False, WHITE)
    tf.word_wrap = True


# =============================================================================
# SLIDE 18  The gap between detection and explanation
# =============================================================================
def s18(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    _chrome(sl, "LLM & REASONING", pg)
    _deco(sl)

    _p(_tb(sl, 1080412, 820000, 10037619, 520000),
       "From Signal Detection to Coaching Explanation", 28, True, DARK_NAV)

    _rect(sl, 502920, 1420000, W - 1005840, 380000, fill=CARD_LT)
    tf_s = _p(_tb(sl, 700000, 1460000, W - 1400000, 340000),
              "Detecting that a candidate fidgets is not coaching. Explaining when it "
              "happened, why it hurts, and exactly how to fix it -- that is.", 12, False, DARK_NAV)
    tf_s.word_wrap = True

    cards = [
        (502920,  DARK_NAV, "THE PROBLEM", WHITE, [
            "Pose & audio pipelines produce",
            "timestamped events -- not advice",
            "",
            "A flag list is not feedback",
            "a candidate can act on",
        ]),
        (4307738, CARD_GRY, "OUR APPROACH", DARK_NAV, [
            "Ground every LLM claim in a",
            "timestamped, confidence-gated",
            "event from the pipeline",
            "",
            "No claim without evidence",
        ]),
        (8112557, CARD_MD,  "THE OUTPUT", DARK_NAV, [
            "For each signal: what happened",
            "and when, why it matters in an",
            "interview, one concrete fix",
            "",
            "Reliability-scored end-to-end",
        ]),
    ]
    for l, fill, title, tclr, bullets in cards:
        _rect(sl, l, 1930000, 3576218, 2606040, fill=fill)
        _p(_tb(sl, l + 150000, 2060000, 3276218, 560000), title, 15, True, tclr)
        tb = _tb(sl, l + 150000, 2680000, 3276218, 1800000)
        tf = _p(tb, bullets[0], 11, False, tclr)
        for b in bullets[1:]:
            _row(tf, b, 11, False, tclr)

    for ax in [4040000, 7846000]:
        _p(_tb(sl, ax + 50000, 3086000, 168000, 300000), "\u25b6", 18, True, BLUE, PP_ALIGN.CENTER)

    _bar(sl, "Key design principle: the LLM never sees raw video frames. It reads only "
         "structured evidence -- the same data a human reviewer would check -- so every "
         "coaching claim is auditable against the original signals.")


# =============================================================================
# SLIDE 19  No hallucination by design
# =============================================================================
def s19(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    _chrome(sl, "LLM & REASONING", pg)
    _deco(sl)

    _p(_tb(sl, 1080412, 820000, 10037619, 520000),
       "No Hallucination by Design", 28, True, DARK_NAV)

    tf_i = _p(_tb(sl, 700000, 1360000, W - 1400000, 360000),
              "The LLM is constrained to what the pipeline actually measured. "
              "It cannot invent behaviour, appearance, or context it was not given.",
              12, False, DARK_NAV)
    tf_i.word_wrap = True

    CW, GAP, SX = 2750000, 105000, 466344
    LH, BH = 430000, 3200000
    LY, BY = 1870000, 2300000

    cols = [
        (BLUE,  CARD_MD,  "WHAT IS\nMEASURED",  [
            "Every signal has a type,",
            "start time, end time,",
            "and confidence score",
            "",
            "e.g.  hands_near_face",
            "      2.1s - 4.8s  conf=0.82",
        ]),
        (AMBER, AMBER_BG, "WHAT THE\nLLM SEES", [
            "Timestamped event list",
            "for this clip only --",
            "no static vocabulary",
            "",
            "Signal summary counts,",
            "longest clean streak",
        ]),
        (RED,   RED_BG,   "WHAT IS\nFORBIDDEN", [
            "Clothing, hair, skin,",
            "food, furniture, decor",
            "",
            "Any claim not backed",
            "by a named event in",
            "the evidence text",
        ]),
        (GREEN, GREEN_BG, "HOW IT IS\nENFORCED", [
            "Every observation must",
            "begin with a signal type",
            "token from this clip",
            "",
            "Validation layer rejects",
            "uncategorised claims",
        ]),
    ]
    for i, (lf, bf, title, bullets) in enumerate(cols):
        x = SX + i * (CW + GAP)
        _rect(sl, x, LY, CW, LH, fill=lf)
        _p(_tb(sl, x + 60000, LY + 50000, CW - 120000, LH - 80000), title, 11, True, WHITE, PP_ALIGN.CENTER)
        _rect(sl, x, BY, CW, BH, fill=bf)
        tb = _tb(sl, x + 100000, BY + 120000, CW - 200000, BH - 200000)
        tf = _p(tb, bullets[0], 10, False, DARK_NAV)
        for b in bullets[1:]:
            _row(tf, b, 10, False, DARK_NAV)

    _bar(sl, "Early tests produced observations like 'wearing a white towel' and "
         "'sandwich and coffee on the counter' -- neither was in the evidence. "
         "Both were rejected by the validation layer (reliability 0.25). "
         "Removing image tokens from the prompt eliminated appearance hallucinations entirely.")


# =============================================================================
# SLIDE 20  Three prompt failures we solved
# =============================================================================
def s20(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    _chrome(sl, "LLM & REASONING", pg)
    _deco(sl)

    _p(_tb(sl, 1080412, 820000, 10037619, 520000),
       "Three Prompt Failures -- and How We Fixed Them", 28, True, DARK_NAV)

    # Dark champion card (left)
    _rect(sl, 502920, 1480000, 3800000, 3500000, fill=DARK_NAV)
    _rect(sl, 502920, 1370000, 3800000, 110000,  fill=BLUE)
    _p(_tb(sl, 502920, 1270000, 3800000, 280000), "Champion", 16, True, DARK_NAV)

    tb_c = _tb(sl, 650000, 1580000, 3500000, 3300000)
    tf_c = _p(tb_c, "Nemotron Mini 4B", 18, True, WHITE)
    _row(tf_c, "via Ollama  |  local  |  private", 10, False, CARD_MD)
    _row(tf_c, "", 6)
    _row(tf_c, "Why local?", 11, True, CARD_LT)
    _row(tf_c, "", 4)
    _row(tf_c, "Interview responses contain", 10, False, WHITE)
    _row(tf_c, "personal performance data.", 10, False, WHITE)
    _row(tf_c, "Nothing leaves the device.", 10, False, WHITE)
    _row(tf_c, "", 6)
    _row(tf_c, "Why instruction-tuned?", 11, True, CARD_LT)
    _row(tf_c, "", 4)
    _row(tf_c, "format='json' enforces", 10, False, WHITE)
    _row(tf_c, "structured output on every call", 10, False, WHITE)
    _row(tf_c, "-- no parsing workarounds.", 10, False, WHITE)

    # Three failure/fix cards (right)
    fixes = [
        ("Failure: model ignores evidence and free-writes",
         "Fix: REQUIRED FORMAT forces every observation to start with a <signal_type>: "
         "token present in this clip's evidence. The model cannot describe what it sees -- "
         "only what was measured."),
        ("Failure: model stops after 1-2 signals out of 7+",
         "Fix: REQUIRED COVERAGE lists every signal type flagged in the clip and mandates "
         "one observation each. Coverage jumped from 2 to 7 after this rule was added."),
        ("Failure: vague suggestions candidates cannot act on",
         "Fix: lighting and audio signals require a specific remedy. "
         "'low_light' must produce 'move toward a front light source' -- "
         "not 'consider improving your lighting'."),
    ]
    rh = 1100000
    for i, (problem, fix) in enumerate(fixes):
        y = 1400000 + i * (rh + 80000)
        _rect(sl, 4450000, y, 7300000, rh, fill=CARD_MD)
        _rect(sl, 4450000, y, 380000, rh, fill=NAVY_ICN)
        _p(_tb(sl, 4460000, y + rh // 2 - 200000, 360000, 400000),
           str(i + 1), 22, True, WHITE, PP_ALIGN.CENTER)
        tb = _tb(sl, 4900000, y + 80000, 6750000, rh - 160000)
        tf = _p(tb, problem, 11, True, DARK_NAV)
        _row(tf, fix, 10, False, MID)

    _bar(sl, "A worked example in the prompt made things worse: the model copied the example "
         "verbatim -- word-for-word, including the sentence explicitly labelled BAD -- "
         "instead of reasoning about the actual clip. "
         "Dynamic signal-name lists replaced static examples entirely.")


# =============================================================================
# SLIDE 21  What candidates actually receive
# =============================================================================
def s21(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    _chrome(sl, "LLM & REASONING", pg)
    _deco(sl)

    _p(_tb(sl, 1080412, 820000, 10037619, 520000),
       "What Candidates Actually Receive", 28, True, DARK_NAV)

    # Left: 4 validation checks
    checks = [
        (BLUE,     "Does every claim name a real signal?",
         "Generic statements ('you seemed nervous') have no signal anchor "
         "and are rejected before the report reaches the user."),
        (DARK_NAV, "Are timestamps inside the actual clip?",
         "Any second cited in a claim must fall within 0 - clip duration. "
         "Out-of-range citations are caught automatically."),
        (BLUE,     "Is the underlying detection trustworthy?",
         "Low-confidence detections (< 0.5) reduce the reliability score. "
         "The report shows how much to trust each observation."),
        (DARK_NAV, "Is there enough evidence for this claim?",
         "If no visual events and no audio flags exist, strong conclusions "
         "are blocked. The system self-limits when the data is thin."),
    ]
    CW, CH, CT = 5500000, 920000, 1480000
    for i, (accent, title, body) in enumerate(checks):
        y = CT + i * (CH + 80000)
        bg = CARD_MD if accent == BLUE else CARD_LT
        _rect(sl, 502920, y, CW, CH, fill=bg)
        _rect(sl, 502920, y, 380000, CH, fill=accent)
        _p(_tb(sl, 502920, y + CH // 2 - 200000, 380000, 400000),
           str(i + 1), 22, True, WHITE, PP_ALIGN.CENTER)
        tb = _tb(sl, 990000, y + 100000, CW - 600000, CH - 200000)
        tf = _p(tb, title, 11, True, DARK_NAV)
        _row(tf, body, 10, False, MID)

    # Reliability formula bar
    ry = CT + 4 * (CH + 80000) + 20000
    _rect(sl, 502920, ry, CW, 360000, fill=BLUE)
    _p(_tb(sl, 620000, ry + 60000, CW - 240000, 240000),
       "Reliability = max(0,  1.0 - 0.15 x failed checks)   --   shown as a percentage",
       11, True, WHITE)

    # Right: 3 output sections + PDF strip
    OX = 502920 + CW + 220000
    OW = W - OX - 502920
    outputs = [
        (BLUE,    WHITE,    "WHAT HAPPENED",
         "Timestamped observation tied to each signal.\n"
         "e.g. 'hands_near_face: detected 2.1s - 4.8s'"),
        (AMBER,   DARK_NAV, "WHY IT MATTERS",
         "How the signal affects interview perception.\n"
         "e.g. 'touching your face signals anxiety to interviewers'"),
        (GREEN,   WHITE,    "WHAT TO DO",
         "One concrete, specific action per signal.\n"
         "e.g. 'Rest hands on the desk; notice when they move to your face'"),
    ]
    EH = (4 * (CH + 80000) - 80000) // 3 - 60000
    for i, (lf, lc, title, body) in enumerate(outputs):
        y = CT + i * (EH + 80000)
        _rect(sl, OX, y, OW, 380000, fill=lf)
        _p(_tb(sl, OX + 120000, y + 80000, OW - 240000, 280000), title, 13, True, lc)
        _rect(sl, OX, y + 380000, OW, EH - 380000, fill=CARD_GRY)
        tf = _p(_tb(sl, OX + 120000, y + 470000, OW - 240000, EH - 550000), body, 10, False, MID)
        tf.word_wrap = True

    _rect(sl, OX, CT + 3 * (EH + 80000) - 60000, OW, 420000, fill=DARK_NAV)
    _p(_tb(sl, OX + 120000, CT + 3 * (EH + 80000) - 60000 + 80000, OW - 240000, 260000),
       "\u2b07   Downloadable as a branded PDF report after every session", 11, True, WHITE)

    _bar(sl, "The three-part structure (what / why / what to do) is deliberate: "
         "an observation alone does not change behaviour. "
         "Candidates leave with a specific rehearsal target, not a score card.")


# =============================================================================
def main():
    src  = Path(r"C:\Users\shrey\Downloads\InterviewLens_Presentation.pptx")
    dest = Path(r"C:\Users\shrey\Downloads\InterviewLens_LLM_Slides.pptx")
    prs  = Presentation(str(src))

    while len(prs.slides) > 17:
        rId = prs.slides._sldIdLst[-1].get("r:id")
        del prs.slides._sldIdLst[-1]
        prs.part.drop_rel(rId)

    s18(prs, 18); print("  18 -- From Detection to Explanation")
    s19(prs, 19); print("  19 -- No Hallucination by Design")
    s20(prs, 20); print("  20 -- Three Prompt Failures Fixed")
    s21(prs, 21); print("  21 -- What Candidates Receive")

    prs.save(str(dest))
    print(f"\nSaved -> {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
