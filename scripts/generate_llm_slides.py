"""
4 LLM & Reasoning slides — business value framing.

  18  The coaching gap that LLM reasoning closes
  19  Why candidates can trust the feedback
  20  Three iterations that made the feedback more useful
  21  What a candidate walks away with

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


def R(s, l, t, w, h, f=None):
    sh = s.shapes.add_shape(1, l, t, w, h)
    sh.fill.solid() if f else sh.fill.background()
    if f: sh.fill.fore_color.rgb = f
    sh.line.fill.background()
    return sh

def O(s, l, t, w, h, f):
    sh = s.shapes.add_shape(9, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = f
    sh.line.fill.background(); return sh

def TB(s, l, t, w, h, auto=True):
    sh = s.shapes.add_textbox(l, t, w, h)
    sh.line.fill.background()
    sh.text_frame.word_wrap = True
    if auto:
        sh.text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
    return sh

def P(sh, txt, pt, bold=False, clr=MID, al=PP_ALIGN.LEFT, sa=0, sb=0):
    tf = sh if hasattr(sh, '_txBody') else sh.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0] if tf.paragraphs[0].text == "" else None
    if p is None:
        tf._txBody.add_p(); p = tf.paragraphs[-1]
    p.alignment = al
    if sa: p.space_after  = Pt(sa)
    if sb: p.space_before = Pt(sb)
    if txt:
        r = p.add_run()
        r.text = txt; r.font.size = Pt(pt)
        r.font.bold = bold; r.font.color.rgb = clr
    return tf

def chrome(sl, pg):
    O(sl, 514495, 419029, 615315, 615315, BLUE)
    P(TB(sl, 1252728, 588523, 9601200, 256032), "LLM & REASONING", 20, True, BLUE)
    P(TB(sl, 11140135, 6528816, 548640, 256032), str(pg), 9, False, MUTED, PP_ALIGN.RIGHT)

def deco(sl):
    O(sl, 10252478, 5202936, 3840480, 3840480, BLUE)

def strip(sl, txt):
    R(sl, 502920, 5080000, W - 1005840, 300000, f=BANNER)
    P(TB(sl, 700000, 5100000, W - 1400000, 260000), txt, 12, False, NAVY)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 18  The coaching gap — Future Work text style
# ═══════════════════════════════════════════════════════════════════════════
def s18(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, pg);  deco(sl)

    P(TB(sl, 1080412, 810000, 10037619, 500000),
      "Personalised Interview Coaching at Scale", 25, True, NAVY)

    sh = TB(sl, 1129810, 1500000, 9100000, 100000)
    tf = sh.text_frame

    P(tf, "1.  Most candidates who practise get no useful feedback",
      20, True, NAVY, sa=3)
    P(tf, "Human coaching costs hundreds of dollars per session."
      "  InterviewLens delivers the same specificity after every practice run"
      " at zero marginal cost.",
      14, False, MID, sa=16)

    P(tf, "2.  Generic feedback does not change behaviour",
      20, True, NAVY, sa=3)
    P(tf, "Telling a candidate they \"seemed nervous\" is not actionable."
      "  Telling them their hands moved to their face in the first 5 seconds"
      " — and giving them one specific thing to rehearse — is.",
      14, False, MID, sa=16)

    P(tf, "3.  The LLM bridges detection and coaching",
      20, True, NAVY, sa=3)
    P(tf, "The pipeline detects signals.  The LLM explains why they matter"
      " and what to do about them — grounded in the evidence, not opinion.",
      14, False, MID)

    strip(sl,
          "Scalability without specificity is noise."
          "  Every candidate receives the same depth of feedback"
          " regardless of volume.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 19  Why candidates can trust the feedback — badge style
# ═══════════════════════════════════════════════════════════════════════════
def s19(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, pg);  deco(sl)

    P(TB(sl, 1080412, 810000, 10037619, 500000),
      "Why Candidates Can Trust the Feedback", 25, True, NAVY)

    P(TB(sl, 759005, 1350000, 10370934, 280000),
      "AI feedback is often dismissed as hallucination."
      "  InterviewLens makes every claim auditable.", 13, False, MID)

    R(sl, 995567, 1789424, 10370934, 674490, f=BANNER)

    BADGE = 548640
    BY    = 1862923
    groups = [
        (1122092, "AUDIT", "TRAIL",
         "Every claim cites a timestamped signal.",
         "A reviewer can verify any observation"
         " against the original detection data."),
        (4500000, "RELI", "SCORE",
         "Reliability shown to the candidate.",
         "Failed validation checks reduce the score."
         "  Candidates see how much to trust each claim."),
        (7900000, "NO", "OPINION",
         "No claims beyond the evidence.",
         "The model cannot comment on anything"
         " not in the detected signal list."),
    ]
    for bx, l1, l2, bold_txt, body_txt in groups:
        R(sl, bx, BY, BADGE, BADGE, f=NAVY_ICN)
        sh_lbl = sl.shapes.add_textbox(bx, BY, BADGE, BADGE)
        sh_lbl.line.fill.background()
        sh_lbl.text_frame.word_wrap = False
        p1 = sh_lbl.text_frame.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
        r1 = p1.add_run(); r1.text = l1
        r1.font.size = Pt(12); r1.font.bold = True; r1.font.color.rgb = WHITE
        sh_lbl.text_frame._txBody.add_p()
        p2 = sh_lbl.text_frame.paragraphs[-1]; p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = l2
        r2.font.size = Pt(12); r2.font.bold = True; r2.font.color.rgb = WHITE

        tb = TB(sl, bx + BADGE + 120000, BY, 2450000, 100000)
        P(tb, bold_txt, 13, True, NAVY, sa=4)
        P(tb, body_txt, 12, False, MID)

    R(sl, 502920, 2860000, W - 1005840, 360000, f=NAVY)
    P(TB(sl, 700000, 2890000, W - 1400000, 300000),
      "Before evidence grounding: 1 in 4 claims referenced something"
      " not in the interview (reliability 0.25)."
      "  After: 0.85+.", 14, True, WHITE)

    P(TB(sl, 759005, 3380000, W - 1600000, 300000),
      "The validation layer — 4 checks on every claim", 16, True, NAVY)

    BW = (W - 1400000) // 4 - 80000
    checks = [
        (RED,   "Signal vocabulary", "Does the claim name a real detected signal?"),
        (AMBER, "Timestamp bounds",  "Is every cited time inside the clip?"),
        (GREEN, "Confidence gate",   "Is the underlying detection trustworthy?"),
        (NAVY,  "Evidence support",  "Is there enough data to support this claim?"),
    ]
    for i, (col, title, sub) in enumerate(checks):
        x = 700000 + i * (BW + 80000)
        R(sl, x, 3770000, BW, 880000, f=CARD_GRY)
        R(sl, x, 3770000, BW, 120000, f=col)
        tb = TB(sl, x + 70000, 3930000, BW - 140000, 100000)
        P(tb, title, 13, True, NAVY, sa=4)
        P(tb, sub, 12, False, MUTED)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 20  Three iterations that made feedback more useful
# ═══════════════════════════════════════════════════════════════════════════
def s20(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, pg);  deco(sl)

    P(TB(sl, 1080412, 810000, 10037619, 500000),
      "Three Iterations That Improved Feedback Quality", 25, True, NAVY)

    R(sl, 502920, 1390000, W - 1005840, 280000, f=BANNER)
    P(TB(sl, 700000, 1415000, W - 1400000, 240000),
      "Each failure in development directly reduced the usefulness of the coaching a candidate received.",
      13, False, NAVY)

    # Left: what the system delivers now
    R(sl, 502920, 1800000, 14000, 3300000, f=BLUE)
    tb_l = TB(sl, 600000, 1800000, 4800000, 100000)
    P(tb_l, "What the system delivers today", 18, True, NAVY, sa=3)
    P(tb_l, "After all three iterations", 13, False, MUTED, sa=12)
    for outcome in [
        "Feedback grounded in measured signals, not scene description",
        "Every signal in the clip addressed — none skipped",
        "Each suggestion is a specific, rehearsable action",
        "Reliability score tells the candidate how much to trust each claim",
        "Validated before it reaches the user",
    ]:
        P(tb_l, outcome, 14, False, MID, sa=4)

    # Right: three iterations
    iterations = [
        (RED,
         "Iteration 1 — from 0.25 to 0.85 reliability",
         "The model was describing the room, not the interview."
         "  We removed images and gave it structured signal text only."),
        (AMBER,
         "Iteration 2 — from 2 signals covered to 7",
         "The model stopped after the most obvious signal."
         "  We required it to cover every signal type detected in the clip."),
        (GREEN,
         "Iteration 3 — from vague advice to specific actions",
         "Suggestions like 'improve your lighting' are not rehearsable."
         "  We mandated a concrete fix for every signal type."),
    ]
    IH = 1100000
    for i, (col, heading, body) in enumerate(iterations):
        y = 1800000 + i * (IH + 100000)
        R(sl, 5800000, y, 14000, IH, f=col)
        tb_f = TB(sl, 5900000, y + 80000, 6100000, 100000)
        P(tb_f, heading, 14, True, NAVY, sa=6)
        P(tb_f, body, 13, False, MID)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 21  What a candidate walks away with
# ═══════════════════════════════════════════════════════════════════════════
def s21(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, pg);  deco(sl)

    P(TB(sl, 1080412, 810000, 10037619, 500000),
      "What a Candidate Walks Away With", 25, True, NAVY)

    # Left dark panel — what was detected
    R(sl, 502920, 1420000, 5060000, 3780000, f=NAVY)
    P(TB(sl, 660000, 1530000, 4780000, 340000, auto=False),
      "DETECTED IN THIS SESSION", 16, True, BANNER)

    tb_d = TB(sl, 660000, 1970000, 4780000, 100000)
    P(tb_d, "Signal               Time           Conf", 12, True, MUTED, sa=6)
    for sig, t, c in [
        ("hands_near_face", "2.1s - 4.8s", "0.82"),
        ("head_tilt",       "0.3s - 7.1s", "0.71"),
        ("body_lean",       "1.0s - 8.0s", "0.69"),
        ("looking_down",    "5.2s - 8.0s", "0.67"),
    ]:
        P(tb_d, f"{sig:<20} {t:<14} {c}", 13, False, WHITE, sa=3)
    P(tb_d, "", 8)
    P(tb_d, "Filler words: 2  |  Speaking rate: 91 wpm", 13, False, MUTED)
    P(tb_d, "Reliability:  0.85", 14, True, AMBER, sb=12)

    # Right: 3 output tiers
    OX = 502920 + 5060000 + 260000
    OW = W - OX - 402920
    SH = 1185000

    tiers = [
        (BLUE,  "WHAT HAPPENED",
         "hands_near_face: face touched repeatedly"
         " in the opening 5 seconds of the answer."),
        (AMBER, "WHY IT MATTERS",
         "Face-touching under pressure signals anxiety"
         " and draws the interviewer's attention away from the answer."),
        (GREEN, "WHAT TO DO",
         "Rest both hands flat on the desk before starting."
         "  When they move to the face, pause, reposition, then continue."),
    ]
    for i, (col, label, body) in enumerate(tiers):
        y = 1420000 + i * (SH + 55000)
        R(sl, OX, y, OW, 160000, f=col)
        P(TB(sl, OX + 110000, y + 195000, OW - 220000, 300000, auto=False),
          label, 14, True, NAVY)
        P(TB(sl, OX + 110000, y + 560000, OW - 220000, SH - 600000),
          body, 13, False, MID)

    P(TB(sl, OX, 1420000 + 3 * (SH + 55000) + 70000, OW, 300000),
      "The report is downloadable as a PDF — candidates keep it as a rehearsal target.",
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
    s18(prs, 18); print("  18  The coaching gap")
    s19(prs, 19); print("  19  Why candidates trust the feedback")
    s20(prs, 20); print("  20  Three iterations that improved quality")
    s21(prs, 21); print("  21  What a candidate walks away with")
    prs.save(str(dest))
    print(f"\nSaved -> {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
