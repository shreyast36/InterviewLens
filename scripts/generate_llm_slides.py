"""
4 LLM & Reasoning slides matching the actual existing deck aesthetic:
  - Slide 18  Future Work text style — numbered clean list, mostly white
  - Slide 19  Slide-9 badge style   — thin banner + icon badges + text
  - Slide 20  Clean two-col text    — thin accent borders, no hero fills
  - Slide 21  Signal data + tiers   — dark left panel + white-bg output rows

NO large hero cards.  Colors used only for: thin strips (<1"), small badges, text.

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
BANNER   = RGBColor(0xDD, 0xEA, 0xF6)   # DDEAF6 — the exact banner color in slide 9
CARD_GRY = RGBColor(0xF4, 0xF6, 0xF8)   # very light grey, barely visible fill
AMBER    = RGBColor(0xF0, 0xB4, 0x29)
RED      = RGBColor(0xF0, 0x3B, 0x20)
GREEN    = RGBColor(0x21, 0x96, 0x53)
MUTED    = RGBColor(0x5B, 0x7A, 0x99)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
W = 12192000;  H = 6858000


def R(s, l, t, w, h, f=None, lc=None, lw=25400):
    sh = s.shapes.add_shape(1, l, t, w, h)
    sh.fill.solid() if f else sh.fill.background()
    if f: sh.fill.fore_color.rgb = f
    if lc: sh.line.color.rgb = lc; sh.line.width = Emu(lw)
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

def N(tf, txt, pt, bold=False, clr=MID, al=PP_ALIGN.LEFT, sb=0):
    tf._txBody.add_p(); p = tf.paragraphs[-1]; p.alignment = al
    if sb: p.space_before = Pt(sb)
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


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 18  — Future Work text style (slide 16)
# Single large text block, clean numbered items, mostly white
# ═══════════════════════════════════════════════════════════════════════════
def s18(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "Detection Gives You Data.  Coaching Requires More.", 25, True, NAVY)

    # Single large text block (slide 16 style)
    sh = T(sl, 1129810, 1466608, 9122668, 3600000)
    tf = P(sh, "1.  Detecting a signal is not coaching", 20, True, NAVY)
    N(tf, "     The pipeline flags that a candidate touched their face 14 times"
          " in the first 5 seconds.  It cannot explain why this damages their"
          " impression, or tell them what to physically do differently.", 14, False, MID, sb=4)

    N(tf, "", 10)
    N(tf, "2.  Rules cannot bridge the gap", 20, True, NAVY)
    N(tf, "     There are 34 distinct signal types — body language, framing, background,"
          " and audio.  A rule tree that handles combinations, context, and timing"
          " across all of them would need to be rebuilt for every new signal.", 14, False, MID, sb=4)

    N(tf, "", 10)
    N(tf, "3.  The LLM reasons over evidence", 20, True, NAVY)
    N(tf, "     The reasoning stage reads a structured text document of every detected"
          " event and produces: what happened and when, why it hurts in an interview,"
          " and one specific action to rehearse.  Every claim is grounded.", 14, False, MID, sb=4)

    # Thin blue accent bar at the bottom (matches the deck's DCEBF7 strip)
    R(sl, 502920, 5100000, W - 1005840, 260000, f=BANNER)
    tf_b = P(T(sl, 700000, 5120000, W - 1400000, 220000),
             "Key principle: the LLM receives structured text — not video frames."
             "  Every coaching claim is auditable against the original signal timestamps.", 12, False, NAVY)
    tf_b.word_wrap = True


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 19  — Slide-9 badge style (thin banner + icon badges)
# ═══════════════════════════════════════════════════════════════════════════
def s19(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "The LLM Can Only Say What It Was Told.", 25, True, NAVY)

    # Headline sub (matches slide 9's small text above the banner)
    P(T(sl, 759005, 1350000, 10370934, 300000),
      "Four structural constraints prevent hallucination — not guidelines, but hard rules enforced before output.", 13, False, MID)

    # Full-width thin banner (DDEAF6 — exactly slide 9)
    R(sl, 995567, 1789424, 10370934, 674490, f=BANNER)

    # Three badge + text groups (matching slide 9 geometry)
    BADGE_SZ = 548640
    badges = [
        (1122092, "TEXT\nONLY",
         "No images — the LLM receives a structured"
         " text document listing every detected event,"
         " its timestamps, and confidence score."
         " Nothing else."),
        (4500000, "CLOSED\nVOCAB",
         "Every observation must begin with a"
         " <signal_type>: token drawn from this clip's"
         " evidence.  Invented signal names fail"
         " the validation check downstream."),
        (7900000, "FULL\nCOVERAGE",
         "The prompt lists every signal type present."
         " The model must produce one observation per type."
         " Tested on clips with 7 signals — coverage rose"
         " from 2 to 7 after this rule was added."),
    ]
    BY = 1862923
    for bx, label, body in badges:
        # Dark badge icon
        R(sl, bx, BY, BADGE_SZ, BADGE_SZ, f=NAVY_ICN)
        tf_lbl = P(T(sl, bx, BY + 50000, BADGE_SZ, BADGE_SZ - 100000),
                   label, 10, True, WHITE, PP_ALIGN.CENTER)
        # Text to the right of badge
        sh = T(sl, bx + BADGE_SZ + 100000, BY, 2600000, BADGE_SZ + 200000)
        first_line = body.split(chr(10))[0] if chr(10) in body else body[:40]
        tf2 = P(sh, body, 12, False, MID)
        tf2.word_wrap = True

    # Reliability result strip
    R(sl, 502920, 2840000, W - 1005840, 380000, f=NAVY)
    tf_r = P(T(sl, 700000, 2880000, W - 1400000, 300000),
             "Result: reliability score rose from 0.25 (VLM free-writing)"
             "  to 0.85+ (constrained text-only LLM with validation gate).", 14, True, WHITE)
    tf_r.word_wrap = True

    # Key interview signals table area (matching slide 9 bottom layout)
    P(T(sl, 759005, 3370000, W - 1600000, 340000), "Four constraints working together", 16, True, NAVY)

    # 4 constraint summary boxes in a row
    BOX_W = (W - 1400000) // 4 - 100000
    SX = 700000
    constraint_items = [
        (RED,   "Closed vocabulary", "Signal tokens only"),
        (AMBER, "Required coverage", "All signals covered"),
        (GREEN, "Concrete fix rule",  "Specific actions only"),
        (NAVY,  "Validation gate",    "4 checks before output"),
    ]
    for i, (col, title, sub) in enumerate(constraint_items):
        x = SX + i * (BOX_W + 100000)
        R(sl, x, 3780000, BOX_W, 900000, f=CARD_GRY)
        R(sl, x, 3780000, BOX_W, 130000, f=col)
        tf = P(T(sl, x + 80000, 3940000, BOX_W - 160000, 600000), title, 13, True, NAVY)
        N(tf, sub, 12, False, MUTED)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 20  — Clean two-column text, thin accent borders, no hero fills
# ═══════════════════════════════════════════════════════════════════════════
def s20(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "What Broke — and What We Changed", 25, True, NAVY)

    R(sl, 502920, 1390000, W - 1005840, 280000, f=BANNER)
    tf_s = P(T(sl, 700000, 1415000, W - 1400000, 240000),
             "Each failure drove a structural change in the system, not a better prompt.", 13, False, NAVY)
    tf_s.word_wrap = True

    # Left: Nemotron Mini facts — clean text, no hero fill, thin left border accent
    R(sl, 502920, 1800000, 12000, 3600000, f=BLUE)   # thin 13px left accent line
    sh_l = T(sl, 600000, 1800000, 4800000, 3600000)
    tf_l = P(sh_l, "Nemotron Mini 4B", 20, True, NAVY)
    N(tf_l, "Champion model via Ollama", 13, False, MUTED)
    N(tf_l, "", 8)
    N(tf_l, "4 billion parameters  |  ~2.7 GB on-device", 14, False, MID)
    N(tf_l, "No API key, no data sent externally", 14, False, MID)
    N(tf_l, "format='json' enforces structure every call", 14, False, MID)
    N(tf_l, "Deterministic fallback when server offline", 14, False, MID)
    N(tf_l, "", 8)
    P(T(sl, 600000, 4700000, 2500000, 380000), "Champion", 14, True, NAVY)
    R(sl, 600000, 4800000, 2500000, 100000, f=BLUE)

    # Right: 3 failures as clean text items with thin colored left-border accents
    failures = [
        (RED,   "Model described the room, not the interview",
         "Given frames, it observed 'wearing a white towel' and"
         " 'sandwich and coffee on the counter' — neither was evidence."
         "  Reliability: 0.25.  Fix: no images, structured text only."),
        (AMBER, "Model stopped after 2 signals out of 7",
         "Without enforcement the model covered only the obvious signals."
         "  REQUIRED COVERAGE listed every signal type present."
         "  Coverage rose from 2 to 7 signals per clip."),
        (GREEN, "Worked examples made things worse",
         "Adding a GOOD / BAD example pair caused the model to copy"
         " the BAD sentence verbatim — a known small-model failure."
         "  Fix: dynamic signal lists, no static examples."),
    ]
    IH = 1100000
    RX = 5800000
    for i, (col, problem, fix) in enumerate(failures):
        y = 1800000 + i * (IH + 100000)
        R(sl, RX, y, 12000, IH, f=col)           # thin 13px accent line
        sh = T(sl, RX + 100000, y, 6100000, IH)
        tf = P(sh, problem, 14, True, NAVY)
        N(tf, fix, 13, False, MID, sb=5)


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 21  — Dark signal panel left + clean white-bg output rows right
# ═══════════════════════════════════════════════════════════════════════════
def s21(prs, pg):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
    chrome(sl, "LLM & REASONING", pg);  deco(sl)

    P(T(sl, 1080412, 810000, 10037619, 500000),
      "Three Things Every Candidate Receives", 25, True, NAVY)

    # Left dark signal panel — one clean block of data (this is justified as a data display)
    R(sl, 502920, 1420000, 5060000, 3780000, f=NAVY)
    P(T(sl, 660000, 1520000, 4780000, 360000), "DETECTED SIGNALS  (this clip)", 16, True, BANNER)

    sh_l = T(sl, 660000, 1970000, 4780000, 3180000)
    tf_l = P(sh_l, "Signal               Time         Conf", 12, True, MUTED)
    N(tf_l, "hands_near_face    2.1s - 4.8s   0.82", 13, False, WHITE)
    N(tf_l, "head_tilt          0.3s - 7.1s   0.71", 13, False, WHITE)
    N(tf_l, "body_lean          1.0s - 8.0s   0.69", 13, False, WHITE)
    N(tf_l, "looking_down       5.2s - 8.0s   0.67", 13, False, WHITE)
    N(tf_l, "", 8)
    N(tf_l, "Filler words:  2", 13, False, MUTED)
    N(tf_l, "Speaking rate: 91 wpm", 13, False, MUTED)
    N(tf_l, "", 14)
    N(tf_l, "Reliability score:  0.85", 14, True, AMBER)

    # Right: 3 output rows — thin colored top border, white body (no hero fill)
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
         " When you notice them moving to your face, pause,"
         " reposition, then continue."),
    ]
    for i, (col, label, body) in enumerate(tiers):
        y = 1420000 + i * (SH + 55000)
        # Thin top color strip (not a full fill)
        R(sl, OX, y, OW, 160000, f=col)
        P(T(sl, OX + 110000, y + 200000, OW - 220000, 340000), label, 14, True, NAVY)
        tf_b = P(T(sl, OX + 110000, y + 600000, OW - 220000, SH - 660000), body, 13, False, MID)
        tf_b.word_wrap = True

    # Bottom note
    P(T(sl, OX, 1420000 + 3 * (SH + 55000) + 60000, OW, 300000),
      "Without all three, the candidate has data — not a direction.", 13, True, NAVY)


# ─────────────────────────────────────────────────────────────────────────────
def main():
    src  = Path(r"C:\Users\shrey\Downloads\InterviewLens_Presentation.pptx")
    dest = Path(r"C:\Users\shrey\Downloads\InterviewLens_LLM_Slides.pptx")
    prs  = Presentation(str(src))
    while len(prs.slides) > 17:
        rId = prs.slides._sldIdLst[-1].get("r:id")
        del prs.slides._sldIdLst[-1]
        prs.part.drop_rel(rId)
    s18(prs, 18); print("  18  Future Work text style")
    s19(prs, 19); print("  19  Badge style (slide 9)")
    s20(prs, 20); print("  20  Clean two-column text")
    s21(prs, 21); print("  21  Signal panel + clean output rows")
    prs.save(str(dest))
    print(f"\nSaved -> {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
