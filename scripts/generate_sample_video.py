"""Generate a synthetic interview-style video with real TTS audio for pipeline testing.

Creates samples/interview_sample.mp4 — a 15-second clip of an animated
interview candidate with:
  • Professional office background, animated speaking face (mouth + blink)
  • Real TTS speech via pyttsx3 (Windows SAPI) synced to the video
  • Deliberate signals: hand-near-face gestures, head tilt, body sway

Usage:
    python scripts/generate_sample_video.py
    python scripts/generate_sample_video.py --out my_clip.mp4 --duration 20
    python scripts/generate_sample_video.py --voice zira   # female voice
"""
from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import cv2
import numpy as np

# ── Interview answer spoken in the video ──────────────────────────────────────
INTERVIEW_ANSWER = (
    "In my previous role I was leading a cross-functional team when two members "
    "had conflicting approaches to the same problem. "
    "I organised a quick meeting, gave both a chance to present their ideas, "
    "and we built a hybrid solution together. "
    "The project was delivered on time, the team left the meeting feeling aligned, "
    "and we shipped a cleaner result than either approach alone would have produced."
)


def _generate_speech(text: str, wav_path: Path, voice_hint: str = "david",
                     rate: int = 155) -> bool:
    """Synthesise speech to a WAV file using pyttsx3 (Windows SAPI).
    Returns True on success."""
    try:
        import pyttsx3  # noqa: PLC0415
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.setProperty("volume", 0.95)
        # Pick voice by hint substring
        voices = engine.getProperty("voices")
        for v in voices:
            if voice_hint.lower() in v.name.lower() or voice_hint.lower() in v.id.lower():
                engine.setProperty("voice", v.id)
                break
        engine.save_to_file(text, str(wav_path))
        engine.runAndWait()
        return wav_path.exists() and wav_path.stat().st_size > 1024
    except Exception as exc:
        print(f"  [TTS] pyttsx3 failed: {exc}")
        return False


def _combine(video_path: Path, audio_path: Path, out_path: Path) -> bool:
    """Merge silent video + WAV audio into a final MP4 with AAC audio.
    Tries moviepy first, then falls back to ffmpeg subprocess."""
    # ── moviepy ──────────────────────────────────────────────────────────────
    try:
        from moviepy import AudioFileClip, VideoFileClip  # noqa: PLC0415

        vclip = VideoFileClip(str(video_path))
        aclip = AudioFileClip(str(audio_path))
        # loop or trim audio to match video duration
        if aclip.duration < vclip.duration:
            from moviepy import afx  # noqa: PLC0415
            aclip = aclip.with_effects([afx.AudioLoop(duration=vclip.duration)])
        else:
            aclip = aclip.subclipped(0, vclip.duration)
        final = vclip.with_audio(aclip)
        final.write_videofile(
            str(out_path), codec="libx264", audio_codec="aac",
            fps=vclip.fps, verbose=False, logger=None,
        )
        vclip.close(); aclip.close(); final.close()
        return True
    except Exception as exc:
        print(f"  [moviepy] {exc} — trying ffmpeg …")

    # ── ffmpeg subprocess ─────────────────────────────────────────────────────
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_path),
             "-c:v", "copy", "-c:a", "aac", "-shortest", str(out_path)],
            capture_output=True, timeout=120,
        )
        return r.returncode == 0 and out_path.exists()
    except Exception as exc:
        print(f"  [ffmpeg] {exc}")
        return False

# ── Config ─────────────────────────────────────────────────────────────────────
W, H   = 1280, 720
FPS    = 30
SEED   = 42

random.seed(SEED)
rng = np.random.default_rng(SEED)


# ── Background ─────────────────────────────────────────────────────────────────
def _background(frame_i: int, n_frames: int) -> np.ndarray:
    """Soft gradient office wall + desk edge."""
    canvas = np.zeros((H, W, 3), dtype=np.uint8)

    # Wall gradient (warm grey)
    for y in range(H):
        t = y / H
        r = int(38  + 22 * t)
        g = int(42  + 20 * t)
        b = int(52  + 18 * t)
        canvas[y, :] = (b, g, r)   # OpenCV BGR

    # Subtle desk surface (bottom 18 % of frame)
    desk_y = int(H * 0.82)
    desk_col = np.array([40, 30, 25], dtype=np.uint8)      # dark wood (BGR)
    canvas[desk_y:, :] = desk_col

    # Desk edge highlight
    cv2.line(canvas, (0, desk_y), (W, desk_y), (70, 55, 45), 3)

    # Faint vignette
    for y in range(H):
        for x_edge in range(120):
            alpha = (120 - x_edge) / 120 * 0.35
            canvas[y, x_edge] = (canvas[y, x_edge] * (1 - alpha)).astype(np.uint8)
            canvas[y, W - 1 - x_edge] = (canvas[y, W - 1 - x_edge] * (1 - alpha)).astype(np.uint8)

    return canvas


# ── Drawing helpers ────────────────────────────────────────────────────────────
def _filled_ellipse(img, cx, cy, rx, ry, color, angle=0):
    cv2.ellipse(img, (cx, cy), (rx, ry), angle, 0, 360, color, -1)


def _shadow_ellipse(img, cx, cy, rx, ry, alpha=0.18):
    """Subtle shadow blob."""
    overlay = img.copy()
    cv2.ellipse(overlay, (cx + 6, cy + 8), (rx, ry), 0, 0, 360,
                (10, 10, 10), -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


# ── Person drawing ─────────────────────────────────────────────────────────────
SKIN    = (130, 160, 195)   # BGR   warm skin
SKIN_D  = (100, 128, 162)   # darker skin (shadows)
HAIR    = (30,  25,  20)
SHIRT   = (60,  80, 130)    # dark blue shirt
SHIRT_L = (75,  95, 148)

# Anchor points (at centre of frame, slightly left)
CX = W // 2 - 20
# Head top sits at ~28% of height; face centre ~38%
HEAD_CY = int(H * 0.345)
HEAD_RX, HEAD_RY = 88, 108


def _draw_person(canvas: np.ndarray, t: float, phase: float) -> None:
    """Draw a full person figure.

    t       : normalised time 0-1
    phase   : continuous phase for animations (radians)
    """

    # --- subtle sway / lean signal ---
    sway   = int(8  * math.sin(phase * 0.7))          # slow lateral sway
    hbob   = int(4  * math.sin(phase * 1.3))          # head bob
    htilt  = int(12 * math.sin(phase * 0.4))          # head tilt angle (deg)

    # Centre offset from sway
    cx = CX + sway

    # ── Torso / shoulders ────────────────────────────────────────────────────
    sh_w, sh_h = 220, 260
    torso_y = HEAD_CY + HEAD_RY + 20
    # Shirt body
    pts_shirt = np.array([
        [cx - sh_w, H],
        [cx - sh_w, torso_y + 20],
        [cx - sh_w // 2, torso_y - 10],
        [cx + sh_w // 2, torso_y - 10],
        [cx + sh_w, torso_y + 20],
        [cx + sh_w, H],
    ], dtype=np.int32)
    cv2.fillPoly(canvas, [pts_shirt], SHIRT)

    # Collar highlight
    collar_pts = np.array([
        [cx - 38, torso_y - 10],
        [cx, torso_y + 30],
        [cx + 38, torso_y - 10],
    ], dtype=np.int32)
    cv2.fillPoly(canvas, [collar_pts], (85, 105, 160))

    # Shirt shadow/fold lines
    cv2.line(canvas, (cx - sh_w // 2, torso_y),
             (cx - 20, torso_y + sh_h), SHIRT_L, 2)
    cv2.line(canvas, (cx + sh_w // 2, torso_y),
             (cx + 20, torso_y + sh_h), SHIRT_L, 2)

    # ── Neck ────────────────────────────────────────────────────────────────
    neck_y_top  = HEAD_CY + HEAD_RY - 18 + hbob
    neck_y_bot  = torso_y - 8
    cv2.rectangle(canvas, (cx - 28, neck_y_top), (cx + 28, neck_y_bot), SKIN, -1)
    # neck shadow
    cv2.rectangle(canvas, (cx - 28, neck_y_top), (cx - 20, neck_y_bot), SKIN_D, -1)

    # ── Head ────────────────────────────────────────────────────────────────
    hcy = HEAD_CY + hbob
    _shadow_ellipse(canvas, cx, hcy + 10, HEAD_RX + 10, HEAD_RY + 10, alpha=0.12)
    # Hair (slightly larger ellipse, drawn first)
    _filled_ellipse(canvas, cx, hcy - 12, HEAD_RX + 6, HEAD_RY + 8, HAIR, htilt)
    # Face skin
    _filled_ellipse(canvas, cx, hcy, HEAD_RX, HEAD_RY, SKIN, htilt)
    # Face shadow (left side)
    shadow_overlay = canvas.copy()
    _filled_ellipse(shadow_overlay, cx - 30, hcy, 60, HEAD_RY, SKIN_D, htilt)
    cv2.addWeighted(shadow_overlay, 0.25, canvas, 0.75, 0, canvas)

    # ── Eyes ────────────────────────────────────────────────────────────────
    # blink: eyes closed ~3 % of the time
    blink = (math.sin(phase * 0.4) > 0.97)
    eye_y  = hcy - 18 + hbob // 2
    for ex in [cx - 32, cx + 32]:
        # white
        if not blink:
            _filled_ellipse(canvas, ex, eye_y, 18, 11, (230, 230, 228))
            # iris
            _filled_ellipse(canvas, ex, eye_y, 11, 11, (68, 90, 52))
            # pupil
            _filled_ellipse(canvas, ex, eye_y,  6,  6, (18, 18, 18))
            # catchlight
            cv2.circle(canvas, (ex + 3, eye_y - 3), 2, (240, 240, 240), -1)
        else:
            # closed eye line
            cv2.line(canvas, (ex - 16, eye_y), (ex + 16, eye_y), SKIN_D, 3)
        # eyebrow
        brow_y = eye_y - 22
        cv2.line(canvas, (ex - 18, brow_y + 2), (ex + 18, brow_y - 2),
                 HAIR, 4)

    # ── Nose ────────────────────────────────────────────────────────────────
    nose_y = hcy + 12
    cv2.line(canvas, (cx, nose_y - 14), (cx - 8,  nose_y + 14), SKIN_D, 2)
    cv2.line(canvas, (cx - 8, nose_y + 14), (cx + 8, nose_y + 14), SKIN_D, 2)

    # ── Mouth (animated speech) ──────────────────────────────────────────────
    mouth_y = hcy + 46
    # mouth opening oscillates with "speech" pattern
    speech_amp  = 10 * abs(math.sin(phase * 4.1)) * abs(math.sin(phase * 1.3))
    mouth_open  = int(speech_amp)
    # lips
    mouth_w = 34
    cv2.ellipse(canvas, (cx, mouth_y), (mouth_w, max(4, mouth_open + 4)),
                0, 0, 180, (85, 80, 110), -1)   # lower lip
    cv2.ellipse(canvas, (cx, mouth_y), (mouth_w, 5), 0, 180, 360,
                (95, 88, 118), -1)               # upper lip
    # teeth when open
    if mouth_open > 4:
        cv2.ellipse(canvas, (cx, mouth_y + 2), (mouth_w - 6, mouth_open - 2),
                    0, 0, 180, (220, 218, 215), -1)
    # mouth line
    cv2.ellipse(canvas, (cx, mouth_y), (mouth_w, max(3, mouth_open)),
                0, 0, 180, (60, 50, 70), 2)

    # ── Deliberate signals for pipeline detection ────────────────────────────

    # 1. Intermittent hand-near-face gesture (every ~4 s for ~1.5 s)
    cycle_4 = phase % (FPS * 4 * (2 * math.pi / FPS))   # 4-s cycle in radians
    hand_active = (cycle_4 % (2 * math.pi) < (2 * math.pi * 0.35))
    if hand_active:
        hand_t   = (cycle_4 % (2 * math.pi)) / (2 * math.pi * 0.35)
        hand_cx  = cx + 55 + int(15 * math.sin(hand_t * math.pi))
        hand_cy  = hcy + 30 + int(20 * math.sin(hand_t * math.pi * 2))
        # draw a fist/hand shape (rough ellipse)
        _filled_ellipse(canvas, hand_cx, hand_cy, 26, 22, SKIN)
        _filled_ellipse(canvas, hand_cx, hand_cy - 18, 18, 12, SKIN)
        # finger bumps
        for fi, fx in enumerate(range(hand_cx - 18, hand_cx + 20, 12)):
            cy_f = hand_cy - 22 - fi % 2 * 4
            _filled_ellipse(canvas, fx, cy_f, 8, 10, SKIN)
        # wrist / arm stub
        arm_pts = np.array([
            [cx + sh_w - 40, H],
            [cx + sh_w - 60, torso_y + 60],
            [hand_cx - 22, hand_cy + 15],
            [hand_cx + 22, hand_cy + 15],
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [arm_pts], SHIRT)
    else:
        # arm resting on desk
        arm_pts = np.array([
            [cx + sh_w - 40, H],
            [cx + sh_w - 60, torso_y + 70],
            [cx + sh_w + 20, int(H * 0.87)],
            [cx + sh_w + 80, H],
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [arm_pts], SHIRT)

    # left arm (static, resting)
    arm_l = np.array([
        [cx - sh_w + 40, H],
        [cx - sh_w + 60, torso_y + 70],
        [cx - sh_w - 20, int(H * 0.87)],
        [cx - sh_w - 80, H],
    ], dtype=np.int32)
    cv2.fillPoly(canvas, [arm_l], SHIRT)


# ── Overlay text ───────────────────────────────────────────────────────────────
def _overlay(canvas: np.ndarray, frame_i: int, total: int) -> None:
    ts = frame_i / FPS
    dur = total / FPS
    # Watermark
    cv2.putText(canvas, "InterviewLens · Sample Candidate",
                (22, H - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (80, 80, 90), 1, cv2.LINE_AA)
    # Timer
    cv2.putText(canvas, f"{ts:.1f} / {dur:.0f}s",
                (W - 130, H - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                (80, 80, 90), 1, cv2.LINE_AA)
    # REC dot
    if (frame_i // 15) % 2 == 0:
        cv2.circle(canvas, (W - 30, 28), 8, (0, 0, 210), -1)
        cv2.putText(canvas, "REC", (W - 22, 33),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 210), 1, cv2.LINE_AA)


# ── Main ───────────────────────────────────────────────────────────────────────
def generate(out_path: Path, duration_s: int = 15, voice: str = "zira") -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use sibling temp files (avoids TemporaryDirectory handle-lock on Windows)
    silent_path = out_path.with_name(out_path.stem + "_silent_tmp.mp4")
    wav_path    = out_path.with_name(out_path.stem + "_speech_tmp.wav")

    try:
        # ── Step 1: render silent video ──────────────────────────────────────
        fourcc   = cv2.VideoWriter_fourcc(*"mp4v")
        writer   = cv2.VideoWriter(str(silent_path), fourcc, FPS, (W, H))
        n_frames = FPS * duration_s
        print(f"Rendering {n_frames} frames …")
        for fi in range(n_frames):
            phase  = fi * (2 * math.pi / FPS)
            canvas = _background(fi, n_frames)
            _draw_person(canvas, fi / n_frames, phase)
            _overlay(canvas, fi, n_frames)
            noise  = rng.integers(-4, 5, (H, W, 3), dtype=np.int16)
            canvas = np.clip(canvas.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            writer.write(canvas)
            if fi % (FPS * 3) == 0:
                print(f"  {fi // FPS}s / {duration_s}s …")
        writer.release()
        print("  silent video written.")

        # ── Step 2: TTS speech ────────────────────────────────────────────────
        print(f"Synthesising speech (voice={voice}, rate=155 wpm) …")
        tts_ok = _generate_speech(INTERVIEW_ANSWER, wav_path, voice_hint=voice)
        if not tts_ok:
            print("  TTS failed — final video will be silent.")
            import shutil
            shutil.copy(silent_path, out_path)
            return

        print(f"  WAV: {wav_path.stat().st_size // 1024} KB")

        # ── Step 3: combine with moviepy ──────────────────────────────────────
        print("Combining video + audio with moviepy …")
        try:
            import gc
            from moviepy import AudioFileClip, VideoFileClip  # noqa: PLC0415

            vclip = VideoFileClip(str(silent_path))
            aclip = AudioFileClip(str(wav_path))

            # trim or loop audio to match video
            if aclip.duration > vclip.duration:
                aclip = aclip.subclipped(0, vclip.duration)
            else:
                from moviepy import afx  # noqa: PLC0415
                aclip = aclip.with_effects(
                    [afx.AudioLoop(duration=vclip.duration)]
                )

            final = vclip.with_audio(aclip)
            final.write_videofile(
                str(out_path),
                fps=FPS,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )
            # Release all handles before any cleanup
            final.close()
            aclip.close()
            vclip.close()
            gc.collect()
            print("  combine done.")

        except Exception as exc:
            print(f"  moviepy combine failed: {exc}")
            # Fall back: copy the silent video
            import shutil
            shutil.copy(silent_path, out_path)

    finally:
        # Clean up temp files (ignore errors from lingering handles on Windows)
        for p in (silent_path, wav_path):
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\nDone — {out_path}  ({size_mb:.1f} MB, {duration_s}s @ {FPS}fps)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate a synthetic interview video with speech audio.")
    ap.add_argument("--out",      default="samples/interview_sample.mp4",
                    help="Output path (default: samples/interview_sample.mp4)")
    ap.add_argument("--duration", type=int,  default=15,
                    help="Duration in seconds (default: 15)")
    ap.add_argument("--voice",    default="zira",
                    help="Voice hint: 'zira' (female) or 'david' (male) (default: zira)")
    args = ap.parse_args()
    generate(Path(args.out), args.duration, args.voice)
