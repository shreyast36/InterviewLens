"""
4 LLM & Reasoning slides.
Strict content discipline:
  - Every body paragraph <= 80 chars (1 line at 14pt in a 9in box)
  - auto_size = SHAPE_TO_FIT_TEXT on all text boxes so nothing ever clips
  - Max 2 body lines per item

Usage:  python scripts/generate_llm_slides.py
Output: C:/Users/shrey/Downloads/InterviewLens_LLM_Slides.pptx
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE

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


# ── Primitives ─────────────────────────────────────────────────────────────────
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

def textbox(s, l, t, w, h):
    """Create a text box with auto-size so text is never clipped."""
    sh = s.shapes.add_textbox(l, t, w, h)
    sh.line.fill.background()
    sh.text_frame.word_wrap = True
    sh.text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
    return sh

def para(sh_or_tf, txt, pt, bold=False, clr=MID, al=PP_ALIGN.LEFT,
         sa=0, sb=0):
    """Append one paragraph to a shape or text frame. Returns the text frame."""
    tf = sh_or_tf if hasattr(sh_or_tf, '_txBody') else sh_or_tf.text_frame
    tf.word_wrap = True
    # Use first paragraph if empty, otherwise add new
    if tf.paragraphs[0].text == "":
        p = tf.paragraphs[0]
    else:
        tf._txBody.add_p()
        p = tf.paragraphs[-1]
    p.alignment = al
    if sa: p.space_after  = Pt(sa)
    if sb: p.space_before = Pt(sb)
    if txt:
        r = p.add_run()
        r.text = txt; r.font.size = Pt(pt)
        r.font.bold = bold; r.font.color.rgb = clr
    return tf

def chrome(sl, sec, pg):
    O(sl, 514495, 419029, 615315, 615315, BLUE)
    para(textbox(sl, 1252728, 588523, 9601200, 256032), sec, 20, True, BLUE)
    para(textbox(sl, 11140135, 6528816, 548640, 256032),
         str(pg), 9, False, MUTED, PP_ALIGN.RIGHT)

def deco(sl):
    O(sl, 10252478, 5202936, 3840480, 3840480, BLUE)

def accent_strip(sl, txt):
    """Thin BANNER strip at bottom with one sentence."""
    R(sl, 502920, 5080000, W - 1005840, 300000, f=BANNER)
    para(textbox(sl, 700000, 5100000, W - 1400000, 260000), txt, 12, False, NAVY)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 18  Clean numbered list — Future Work style
# ═══════════════════════════════════════════════════════════════════════════
def s18(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    para(textbox(sl, 1080412, 810000, 10037619, 500000),
         "Detection Gives You Data.  Coaching Requires More.",
         25, True, NAVY)

    # One large auto-sizing text box with 3 numbered items
    sh = textbox(sl, 1129810, 1500000, 9100000, 100000)  # height grows
    tf = sh.text_frame

    para(tf, "1.  The pipeline produces flags — not feedback",
         20, True, NAVY, sa=3)
    para(tf, "A timestamp and confidence score cannot explain why a signal hurts"
         " or what a candidate should rehearse.",
         14, False, MID, sa=16)

    para(tf, "2.  Rules cannot bridge this gap",
         20, True, NAVY, sa=3)
    para(tf, "No rule handles context, signal combinations, or interview type."
         "  A rule tree for 34 signals would need to be rebuilt for every new one.",
         14, False, MID, sa=16)

    para(tf, "3.  The LLM reasons over evidence — not images",
         20, True, NAVY, sa=3)
    para(tf, "For each signal: what happened and when, why it matters,"
         " and one specific action to rehearse.",
         14, False, MID, sa=0)

    accent_strip(sl,
        "Key design decision: no video frames are passed to the LLM."
        "  Every claim is auditable against the original signal timestamps.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 19  Icon badge style (Slide 9)
# ═══════════════════════════════════════════════════════════════════════════
def s19(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    para(textbox(sl, 1080412, 810000, 10037619, 500000),
         "The LLM Can Only Say What It Was Told.", 25, True, NAVY)

    para(textbox(sl, 759005, 1350000, 10370934, 280000),
         "Four structural constraints prevent hallucination."
         "  Not guidelines — hard rules enforced before output.", 13, False, MID)

    # Full-width thin banner (exact slide 9 dimensions)
    R(sl, 995567, 1789424, 10370934, 674490, f=BANNER)

    # Three badge groups — badge (0.6") + text right (2.5")
    BADGE = 548640
    BY    = 1862923
    groups = [
        (1122092,
         "TEXT", "ONLY",
         "No images.",
         "The LLM reads a structured text list of events."
         "  Not video."),
        (4500000,
         "CLOSED", "VOCAB",
         "Signal tokens only.",
         "Every claim must start with a <signal_type>:"
         " token from this clip."),
        (7900000,
         "FULL", "COVER",
         "All signals covered.",
         "Every flagged signal type needs one observation."
         "  No early stopping."),
    ]
    for bx, l1, l2, bold_txt, body_txt in groups:
        R(sl, bx, BY, BADGE, BADGE, f=NAVY_ICN)
        # Single fixed-size label inside the badge — no auto_size or they overlap
        sh_lbl = sl.shapes.add_textbox(bx, BY, BADGE, BADGE)
        sh_lbl.line.fill.background()
        tf_lbl = sh_lbl.text_frame; tf_lbl.word_wrap = False
        p1 = tf_lbl.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
        r1 = p1.add_run(); r1.text = l1
        r1.font.size = Pt(12); r1.font.bold = True; r1.font.color.rgb = WHITE
        tf_lbl._txBody.add_p(); p2 = tf_lbl.paragraphs[-1]
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = l2
        r2.font.size = Pt(12); r2.font.bold = True; r2.font.color.rgb = WHITE
        # Body text to the right
        tb = textbox(sl, bx + BADGE + 120000, BY, 2450000, 100000)
        para(tb, bold_txt, 13, True, NAVY, sa=4)
        para(tb, body_txt, 12, False, MID)

    # Result strip
    R(sl, 502920, 2860000, W - 1005840, 360000, f=NAVY)
    para(textbox(sl, 700000, 2890000, W - 1400000, 300000),
         "Result: reliability rose from 0.25 (model free-writing about the scene)"
         "  to 0.85+ after structural constraints were applied.",
         14, True, WHITE)

    # 4 summary boxes
    para(textbox(sl, 759005, 3380000, W - 1600000, 300000),
         "Four constraints working together", 16, True, NAVY)

    BW = (W - 1400000) // 4 - 80000
    items = [
        (RED,   "Closed vocabulary",  "Signal tokens only"),
        (AMBER, "Required coverage",  "All signals covered"),
        (GREEN, "Concrete fix rule",  "Specific actions only"),
        (NAVY,  "Validation gate",    "4 checks before output"),
    ]
    for i, (col, title, sub) in enumerate(items):
        x = 700000 + i * (BW + 80000)
        R(sl, x, 3770000, BW, 880000, f=CARD_GRY)
        R(sl, x, 3770000, BW, 120000, f=col)
        tb = textbox(sl, x + 70000, 3930000, BW - 140000, 100000)
        para(tb, title, 13, True, NAVY, sa=4)
        para(tb, sub, 12, False, MUTED)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 20  Two-column clean text
# ═══════════════════════════════════════════════════════════════════════════
def s20(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    para(textbox(sl, 1080412, 810000, 10037619, 500000),
         "What Broke — and What We Changed", 25, True, NAVY)

    R(sl, 502920, 1390000, W - 1005840, 280000, f=BANNER)
    para(textbox(sl, 700000, 1415000, W - 1400000, 240000),
         "Each failure drove a structural change in the system — not a better prompt.",
         13, False, NAVY)

    # Left column: thin accent line + Nemotron facts
    R(sl, 502920, 1800000, 14000, 3300000, f=BLUE)
    tb_l = textbox(sl, 600000, 1800000, 4800000, 100000)
    para(tb_l, "Nemotron Mini 4B", 20, True, NAVY, sa=3)
    para(tb_l, "Stage 5 of the InterviewLens pipeline", 13, False, MUTED, sa=12)
    for fact in [
        "Receives the fused EvidencePackage as structured text",
        "Produces one observation per detected signal type",
        "Grounds every claim in a timestamped pipeline event",
        "Output: observations, explanations, suggestions",
        "Output is validated in Stage 6 before reaching the user",
    ]:
        para(tb_l, fact, 14, False, MID, sa=4)
    para(tb_l, "", 8)
    para(tb_l, "Champion", 14, True, NAVY, sb=10)
    R(sl, 600000, 4860000, 2200000, 90000, f=BLUE)

    # Right column: 3 failures — thin accent left + heading + one-line fix
    failures = [
        (RED,
         "Model described the room, not the interview",
         "Reliability 0.25.  Fix: no images — structured text document only."),
        (AMBER,
         "Model stopped after 2 signals out of 7",
         "REQUIRED COVERAGE listed every present signal type.  Coverage: 2 → 7."),
        (GREEN,
         "Worked examples made things worse",
         "Model copied the BAD example verbatim.  Fix: dynamic lists, no examples."),
    ]
    IH = 1100000
    for i, (col, heading, fix) in enumerate(failures):
        y = 1800000 + i * (IH + 100000)
        R(sl, 5800000, y, 14000, IH, f=col)
        tb_f = textbox(sl, 5900000, y + 80000, 6100000, 100000)
        para(tb_f, heading, 14, True, NAVY, sa=6)
        para(tb_f, fix, 13, False, MID)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 21  Signal data + three output rows
# ═══════════════════════════════════════════════════════════════════════════
def s21(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    para(textbox(sl, 1080412, 810000, 10037619, 500000),
         "Three Things Every Candidate Receives", 25, True, NAVY)

    # Left dark signal panel
    R(sl, 502920, 1420000, 5060000, 3780000, f=NAVY)
    para(textbox(sl, 660000, 1530000, 4780000, 340000),
         "DETECTED SIGNALS  (this clip)", 16, True, BANNER)

    tb_d = textbox(sl, 660000, 1970000, 4780000, 100000)
    para(tb_d, "Signal               Time           Conf",
         12, True, MUTED, sa=6)
    for sig, t, c in [
        ("hands_near_face", "2.1s - 4.8s", "0.82"),
        ("head_tilt",       "0.3s - 7.1s", "0.71"),
        ("body_lean",       "1.0s - 8.0s", "0.69"),
        ("looking_down",    "5.2s - 8.0s", "0.67"),
    ]:
        para(tb_d, f"{sig:<20} {t:<14} {c}", 13, False, WHITE, sa=3)
    para(tb_d, "", 8)
    para(tb_d, "Filler words: 2  |  Speaking rate: 91 wpm", 13, False, MUTED, sa=0)
    para(tb_d, "Reliability score:  0.85", 14, True, AMBER, sb=12)

    # Right: 3 output rows — thin top strip + white body, short text
    OX = 502920 + 5060000 + 260000
    OW = W - OX - 402920
    SH = 1185000

    tiers = [
        (BLUE,  "WHAT HAPPENED",
         "hands_near_face: face touched repeatedly"
         " in the opening 5 seconds."),
        (AMBER, "WHY IT MATTERS",
         "Face-touching signals anxiety and distracts"
         " the interviewer from your words."),
        (GREEN, "WHAT TO DO",
         "Rest both hands flat on the desk."
         "  When they move to your face, pause and reposition."),
    ]
    for i, (col, label, body) in enumerate(tiers):
        y = 1420000 + i * (SH + 55000)
        R(sl, OX, y, OW, 160000, f=col)
        para(textbox(sl, OX + 110000, y + 195000, OW - 220000, 300000),
             label, 14, True, NAVY)
        para(textbox(sl, OX + 110000, y + 560000, OW - 220000, SH - 600000),
             body, 13, False, MID)

    para(textbox(sl, OX, 1420000 + 3 * (SH + 55000) + 70000, OW, 300000),
         "Without all three, the candidate has data — not a direction.",
         13, True, NAVY)


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
