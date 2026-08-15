"""
4 LLM & Reasoning slides — clean text formatting, no literal \\n chars,
proper paragraph breaks, short punchy content, correct text-box sizing.

Usage:  python scripts/generate_llm_slides.py
Output: C:/Users/shrey/Downloads/InterviewLens_LLM_Slides.pptx
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn

BLUE     = RGBColor(0x2C, 0x7F, 0xB8)
NAVY     = RGBColor(0x14, 0x30, 0x4F)
NAVY_ICN = RGBColor(0x1F, 0x38, 0x64)
MID      = RGBColor(0x1A, 0x2B, 0x3C)
BANNER   = RGBColor(0xDD, 0xEA, 0xF6)
CARD_GRY = RGBColor(0xF4, 0xF6, 0xF8)
AMBER    = RGBColor(0xF0, 0xB4, 0x29)
RED      = RGBColor(0xF0, 0x3B, 0x20)
GREEN    = RGBColor(0x21, 0x96, 0x53)
MUTED    = RGBColor(0x5B, 0x7A, 0x99)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
W = 12192000
H =  6858000


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

def line(sh, txt, pt, bold=False, clr=MID, al=PP_ALIGN.LEFT, sa=0, sb=0):
    """Add one paragraph to a shape's text frame. Returns the text frame."""
    tf = sh.text_frame; tf.word_wrap = True
    p = tf.paragraphs[-1] if tf.paragraphs[0].text == "" else None
    if p is None or p.text != "":
        tf._txBody.add_p()
        p = tf.paragraphs[-1]
    p.alignment = al
    if sa: p.space_after  = Pt(sa)
    if sb: p.space_before = Pt(sb)
    if txt:
        r = p.add_run()
        r.text = txt; r.font.size = Pt(pt); r.font.bold = bold
        r.font.color.rgb = clr
    return tf

def chrome(sl, sec, pg):
    O(sl, 514495, 419029, 615315, 615315, BLUE)
    sh = T(sl, 1252728, 588523, 9601200, 256032)
    line(sh, sec, 20, True, BLUE)
    sh2 = T(sl, 11140135, 6528816, 548640, 256032)
    line(sh2, str(pg), 9, False, MUTED, PP_ALIGN.RIGHT)

def deco(sl):
    O(sl, 10252478, 5202936, 3840480, 3840480, BLUE)

def banner_strip(sl, txt):
    R(sl, 502920, 5080000, W - 1005840, 300000, f=BANNER)
    sh = T(sl, 700000, 5100000, W - 1400000, 260000)
    line(sh, txt, 12, False, NAVY)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 18  Clean numbered list (Future Work style)
# ═══════════════════════════════════════════════════════════════════════════
def s18(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    sh_h = T(sl, 1080412, 810000, 10037619, 500000)
    line(sh_h, "Detection Gives You Data.  Coaching Requires More.", 25, True, NAVY)

    # Three numbered items — short headline + one sentence each
    # No indentation, no long paragraphs
    sh = T(sl, 1129810, 1500000, 9122668, 3500000)
    tf = sh.text_frame; tf.word_wrap = True

    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT; p.space_after = Pt(2)
    r = p.add_run(); r.text = "1.  The pipeline produces flags — not feedback"
    r.font.size = Pt(20); r.font.bold = True; r.font.color.rgb = NAVY

    tf._txBody.add_p(); p = tf.paragraphs[-1]; p.space_after = Pt(14)
    r = p.add_run()
    r.text = ("The 34 detected signals have timestamps and confidence scores."
              "  A flag is not an explanation, and an explanation is not an action.")
    r.font.size = Pt(14); r.font.color.rgb = MID

    tf._txBody.add_p(); p = tf.paragraphs[-1]; p.space_after = Pt(2)
    r = p.add_run(); r.text = "2.  Rules cannot bridge the gap"
    r.font.size = Pt(20); r.font.bold = True; r.font.color.rgb = NAVY

    tf._txBody.add_p(); p = tf.paragraphs[-1]; p.space_after = Pt(14)
    r = p.add_run()
    r.text = ("There is no rule that explains why arms_crossed matters more"
              " in a finance interview than in a startup pitch."
              "  Context and combinations require reasoning, not branching.")
    r.font.size = Pt(14); r.font.color.rgb = MID

    tf._txBody.add_p(); p = tf.paragraphs[-1]; p.space_after = Pt(2)
    r = p.add_run(); r.text = "3.  The LLM reasons over evidence, not images"
    r.font.size = Pt(20); r.font.bold = True; r.font.color.rgb = NAVY

    tf._txBody.add_p(); p = tf.paragraphs[-1]; p.space_after = Pt(0)
    r = p.add_run()
    r.text = ("It reads a structured text document of every detected event"
              " and produces: what happened, why it hurts in an interview,"
              " and one specific action to rehearse.  Every claim is grounded.")
    r.font.size = Pt(14); r.font.color.rgb = MID

    banner_strip(sl,
        "Key design decision: no video frames are passed to the LLM."
        "  Every coaching claim is auditable against the original signal timestamps.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 19  Slide-9 badge style
# ═══════════════════════════════════════════════════════════════════════════
def s19(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    sh_h = T(sl, 1080412, 810000, 10037619, 500000)
    line(sh_h, "The LLM Can Only Say What It Was Told.", 25, True, NAVY)

    sh_sub = T(sl, 759005, 1350000, 10370934, 320000)
    line(sh_sub,
         "Four structural constraints prevent hallucination — not guidelines, but hard rules"
         " enforced before a single token is generated.", 13, False, MID)

    # Full-width thin banner
    R(sl, 995567, 1789424, 10370934, 674490, f=BANNER)

    # Three badge + body text groups
    BADGE = 548640
    BY    = 1862923
    groups = [
        (1122092,
         "TEXT", "ONLY",
         "No images.",
         "The LLM receives a structured text document:"
         " every detected signal, its timestamps, and confidence score.  Nothing else."),
        (4500000,
         "CLOSED", "VOCAB",
         "Signal tokens only.",
         "Every observation must begin with a <signal_type>: token"
         " drawn from this clip's evidence.  Invented names fail validation."),
        (7900000,
         "FULL", "COVER",
         "All signals covered.",
         "The prompt lists every signal type present."
         "  Coverage rose from 2 to 7 per clip after this rule was added."),
    ]
    for bx, line1, line2, bold_line, body in groups:
        R(sl, bx, BY, BADGE, BADGE, f=NAVY_ICN)
        sh_l = T(sl, bx, BY + 60000, BADGE, BADGE // 2 - 60000)
        line(sh_l, line1, 11, True, WHITE, PP_ALIGN.CENTER)
        sh_l2 = T(sl, bx, BY + BADGE // 2, BADGE, BADGE // 2 - 60000)
        line(sh_l2, line2, 11, True, WHITE, PP_ALIGN.CENTER)
        # Text to right of badge
        sh_b = T(sl, bx + BADGE + 120000, BY, 2450000, BADGE + 200000)
        tf_b = sh_b.text_frame; tf_b.word_wrap = True
        p1 = tf_b.paragraphs[0]; p1.space_after = Pt(4)
        r1 = p1.add_run(); r1.text = bold_line
        r1.font.size = Pt(13); r1.font.bold = True; r1.font.color.rgb = NAVY
        tf_b._txBody.add_p(); p2 = tf_b.paragraphs[-1]
        r2 = p2.add_run(); r2.text = body
        r2.font.size = Pt(12); r2.font.color.rgb = MID

    # Reliability result
    R(sl, 502920, 2840000, W - 1005840, 380000, f=NAVY)
    sh_r = T(sl, 700000, 2880000, W - 1400000, 300000)
    line(sh_r,
         "Result: reliability rose from 0.25 (model free-writing about the scene)"
         "  to 0.85+ after structural constraints were applied.", 14, True, WHITE)

    # 4 small summary boxes
    sh_t = T(sl, 759005, 3370000, W - 1600000, 340000)
    line(sh_t, "Four constraints working together", 16, True, NAVY)

    BW = (W - 1400000) // 4 - 80000
    items = [
        (RED,   "Closed vocabulary",  "Signal tokens only"),
        (AMBER, "Required coverage",  "All signals covered"),
        (GREEN, "Concrete fix rule",  "Specific actions only"),
        (NAVY,  "Validation gate",    "4 checks before output"),
    ]
    for i, (col, title, sub) in enumerate(items):
        x = 700000 + i * (BW + 80000)
        R(sl, x, 3780000, BW, 900000, f=CARD_GRY)
        R(sl, x, 3780000, BW, 120000, f=col)
        sh_i = T(sl, x + 70000, 3940000, BW - 140000, 700000)
        tf_i = sh_i.text_frame; tf_i.word_wrap = True
        p_t = tf_i.paragraphs[0]; p_t.space_after = Pt(4)
        r_t = p_t.add_run(); r_t.text = title
        r_t.font.size = Pt(13); r_t.font.bold = True; r_t.font.color.rgb = NAVY
        tf_i._txBody.add_p(); p_s = tf_i.paragraphs[-1]
        r_s = p_s.add_run(); r_s.text = sub
        r_s.font.size = Pt(12); r_s.font.color.rgb = MUTED


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 20  Two-col clean text, thin accent lines only
# ═══════════════════════════════════════════════════════════════════════════
def s20(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    sh_h = T(sl, 1080412, 810000, 10037619, 500000)
    line(sh_h, "What Broke — and What We Changed", 25, True, NAVY)

    R(sl, 502920, 1390000, W - 1005840, 280000, f=BANNER)
    sh_s = T(sl, 700000, 1410000, W - 1400000, 240000)
    line(sh_s, "Each failure drove a structural change — not a better prompt.", 13, False, NAVY)

    # Left: Nemotron facts — thin blue left accent line + clean text
    R(sl, 502920, 1800000, 14000, 3500000, f=BLUE)
    sh_l = T(sl, 600000, 1800000, 4800000, 3500000)
    tf_l = sh_l.text_frame; tf_l.word_wrap = True

    p = tf_l.paragraphs[0]; p.space_after = Pt(3)
    r = p.add_run(); r.text = "Nemotron Mini 4B"
    r.font.size = Pt(20); r.font.bold = True; r.font.color.rgb = NAVY

    tf_l._txBody.add_p(); p = tf_l.paragraphs[-1]; p.space_after = Pt(12)
    r = p.add_run(); r.text = "via Ollama  |  local  |  private"
    r.font.size = Pt(13); r.font.color.rgb = MUTED

    for fact in [
        "4 billion parameters  |  ~2.7 GB on-device",
        "No API key required",
        "No data leaves the machine",
        "format='json' enforces structured output every call",
        "Deterministic mock fallback when server is offline",
    ]:
        tf_l._txBody.add_p(); p = tf_l.paragraphs[-1]; p.space_after = Pt(4)
        r = p.add_run(); r.text = fact
        r.font.size = Pt(14); r.font.color.rgb = MID

    tf_l._txBody.add_p(); p = tf_l.paragraphs[-1]; p.space_before = Pt(14)
    r = p.add_run(); r.text = "Champion"
    r.font.size = Pt(14); r.font.bold = True; r.font.color.rgb = NAVY
    R(sl, 600000, 4960000, 2200000, 90000, f=BLUE)

    # Right: 3 failures — thin colored left accent + heading + body
    failures = [
        (RED,   "Model described the room, not the interview",
         "Given frames, it observed 'wearing a white towel' and 'sandwich and coffee'."
         "  Reliability: 0.25."
         "  Fix: no images — structured text only."),
        (AMBER, "Model stopped after 2 signals out of 7",
         "Without enforcement, obvious signals were covered and early stopping occurred."
         "  REQUIRED COVERAGE listed every present signal type."
         "  Coverage: 2 per clip rose to 7."),
        (GREEN, "Worked examples made things worse",
         "A GOOD / BAD example pair caused the model to copy the BAD sentence verbatim."
         "  Known small-model failure mode."
         "  Fix: dynamic signal lists, no static examples."),
    ]
    IH = 1100000
    RX = 5800000
    for i, (col, heading, body) in enumerate(failures):
        y = 1800000 + i * (IH + 100000)
        R(sl, RX, y, 14000, IH, f=col)
        sh_f = T(sl, RX + 100000, y + 60000, 6100000, IH - 120000)
        tf_f = sh_f.text_frame; tf_f.word_wrap = True
        p = tf_f.paragraphs[0]; p.space_after = Pt(5)
        r = p.add_run(); r.text = heading
        r.font.size = Pt(14); r.font.bold = True; r.font.color.rgb = NAVY
        tf_f._txBody.add_p(); p = tf_f.paragraphs[-1]
        r = p.add_run(); r.text = body
        r.font.size = Pt(13); r.font.color.rgb = MID


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 21  Dark signal panel + clean output rows
# ═══════════════════════════════════════════════════════════════════════════
def s21(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    sh_h = T(sl, 1080412, 810000, 10037619, 500000)
    line(sh_h, "Three Things Every Candidate Receives", 25, True, NAVY)

    # Left dark signal panel
    R(sl, 502920, 1420000, 5060000, 3780000, f=NAVY)

    sh_lh = T(sl, 660000, 1530000, 4780000, 340000)
    line(sh_lh, "DETECTED SIGNALS  (this clip)", 16, True, BANNER)

    sh_ld = T(sl, 660000, 1950000, 4780000, 2800000)
    tf_ld = sh_ld.text_frame; tf_ld.word_wrap = True

    header_p = tf_ld.paragraphs[0]; header_p.space_after = Pt(6)
    r = header_p.add_run(); r.text = "Signal               Time           Conf"
    r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = MUTED

    for sig, t, c in [
        ("hands_near_face", "2.1s - 4.8s", "0.82"),
        ("head_tilt",       "0.3s - 7.1s", "0.71"),
        ("body_lean",       "1.0s - 8.0s", "0.69"),
        ("looking_down",    "5.2s - 8.0s", "0.67"),
    ]:
        tf_ld._txBody.add_p(); p = tf_ld.paragraphs[-1]; p.space_after = Pt(3)
        r = p.add_run(); r.text = f"{sig:<20} {t:<14} {c}"
        r.font.size = Pt(13); r.font.color.rgb = WHITE

    tf_ld._txBody.add_p(); p = tf_ld.paragraphs[-1]; p.space_before = Pt(10)
    r = p.add_run(); r.text = "Filler words: 2  |  Speaking rate: 91 wpm"
    r.font.size = Pt(13); r.font.color.rgb = MUTED

    tf_ld._txBody.add_p(); p = tf_ld.paragraphs[-1]; p.space_before = Pt(14)
    r = p.add_run(); r.text = "Reliability score:  0.85"
    r.font.size = Pt(14); r.font.bold = True; r.font.color.rgb = AMBER

    # Right: 3 output rows — thin top strip, white body
    OX = 502920 + 5060000 + 260000
    OW = W - OX - 402920
    SH = 1185000

    tiers = [
        (BLUE,  "WHAT HAPPENED",
         "hands_near_face: You touched your face repeatedly"
         " during the opening 5 seconds of your answer."),
        (AMBER, "WHY IT MATTERS",
         "Repeated face-touching under pressure signals anxiety"
         " to interviewers and draws attention away from your words."),
        (GREEN, "WHAT TO DO",
         "Before you start, rest both hands flat on the desk."
         " When you notice them moving to your face,"
         " pause, reposition, then continue."),
    ]
    for i, (col, label, body) in enumerate(tiers):
        y = 1420000 + i * (SH + 55000)
        R(sl, OX, y, OW, 160000, f=col)
        sh_lbl = T(sl, OX + 110000, y + 195000, OW - 220000, 330000)
        line(sh_lbl, label, 14, True, NAVY)
        sh_bod = T(sl, OX + 110000, y + 580000, OW - 220000, SH - 640000)
        line(sh_bod, body, 13, False, MID)
        sh_bod.text_frame.word_wrap = True

    sh_note = T(sl, OX, 1420000 + 3 * (SH + 55000) + 70000, OW, 300000)
    line(sh_note, "Without all three, the candidate has data — not a direction.", 13, True, NAVY)


# ─────────────────────────────────────────────────────────────────────────────
def main():
    src  = Path(r"C:\Users\shrey\Downloads\InterviewLens_Presentation.pptx")
    dest = Path(r"C:\Users\shrey\Downloads\InterviewLens_LLM_Slides.pptx")
    prs  = Presentation(str(src))
    while len(prs.slides) > 17:
        rId = prs.slides._sldIdLst[-1].get("r:id")
        del prs.slides._sldIdLst[-1]
        prs.part.drop_rel(rId)
    s18(prs, 18); print("  18")
    s19(prs, 19); print("  19")
    s20(prs, 20); print("  20")
    s21(prs, 21); print("  21")
    prs.save(str(dest))
    print(f"\nSaved -> {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
