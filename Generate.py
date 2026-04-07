#!/usr/bin/env python3
"""
🔮 Horoscope Instagram Reel Generator — Jyotish Edition
Visual Identity: Deep Saffron · Cosmic Maroon · Gold · Warm Ivory
Audio: Programmatic ambient drone (numpy + scipy) — no TTS, no AI audio
Format: 9:16 (1080x1920) — Instagram Reels / TikTok / YouTube Shorts

Dependencies:
    pip install google-generativeai pillow numpy scipy
    sudo apt install ffmpeg  (or brew install ffmpeg on macOS)
"""

import os
import json
import math
import random
import struct
import subprocess
import textwrap
import wave
import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.signal import butter, lfilter
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import frame_generator

# ─── CONFIG ───────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
OUTPUT_DIR     = Path("reels_output")

# Video specs — Instagram Reels 9:16
WIDTH    = 1080
HEIGHT   = 1920
FPS      = 30
SAMPLE_RATE = 44100  # audio sample rate

# ─── BRAND COLOR PALETTE ──────────────────────────────────────────────────────

PALETTE = {
    "saffron":      "#FF6B00",
    "maroon":       "#7B1F3A",
    "gold":         "#F5C518",
    "ivory":        "#FDF8F0",
    "cream":        "#FFFBF2",
    "charcoal":     "#1A1A2E",
    "warm_gray":    "#6B6B80",
    "vedic_green":  "#2D7A4F",
    "midnight":     "#0D0D1A",
}

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# Per-sign gradient pairs — all using brand palette tones
SIGN_GRADIENTS = {
    "Aries":       ("#7B1F3A", "#FF6B00"),   # Maroon → Saffron
    "Taurus":      ("#1A1A2E", "#2D7A4F"),   # Charcoal → Vedic Green
    "Gemini":      ("#FF6B00", "#F5C518"),   # Saffron → Gold
    "Cancer":      ("#1A1A2E", "#7B1F3A"),   # Charcoal → Maroon
    "Leo":         ("#7B1F3A", "#F5C518"),   # Maroon → Gold
    "Virgo":       ("#2D7A4F", "#1A1A2E"),   # Green → Charcoal
    "Libra":       ("#FDF8F0", "#F5C518"),   # Ivory → Gold
    "Scorpio":     ("#0D0D1A", "#7B1F3A"),   # Midnight → Maroon
    "Sagittarius": ("#FF6B00", "#7B1F3A"),   # Saffron → Maroon
    "Capricorn":   ("#1A1A2E", "#0D0D1A"),   # Charcoal → Midnight
    "Aquarius":    ("#1A1A2E", "#FF6B00"),   # Charcoal → Saffron
    "Pisces":      ("#7B1F3A", "#1A1A2E"),   # Maroon → Charcoal
}

SIGN_ACCENT = {
    "Aries": "#F5C518", "Taurus": "#FF6B00", "Gemini": "#FFFBF2",
    "Cancer": "#F5C518", "Leo": "#FF6B00", "Virgo": "#F5C518",
    "Libra": "#7B1F3A", "Scorpio": "#FF6B00", "Sagittarius": "#F5C518",
    "Capricorn": "#FF6B00", "Aquarius": "#F5C518", "Pisces": "#F5C518",
}

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

ZODIAC_EMOJIS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
}

HOOK_INTROS = [
    "The stars revealed something WILD about {sign} today... 👀",
    "If you're a {sign}, you NEED to hear this right now 🔮",
    "Astrologers are SHOCKED by what's coming for {sign} ⚡",
    "The universe has a MESSAGE for every {sign} today 💫",
    "{sign}... the cosmos is talking directly to YOU 🌌",
    "Stop scrolling — this is urgent for {sign} ✋🔮",
    "I wasn't going to post this but {sign} NEEDS to know 👁️",
    "Every {sign} is about to experience a MAJOR shift 🌀",
]

# ─── GEMINI SCRIPT GENERATION ─────────────────────────────────────────────────

def generate_horoscope_script(sign: str) -> dict:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    today = datetime.now().strftime("%B %d, %Y")
    hook  = random.choice(HOOK_INTROS).format(sign=sign)

    prompt = f"""You are a viral astrology content creator for Instagram Reels.
Create a 25-30 second horoscope reel script for {sign} for {today}.

CRITICAL RULES for virality:
- Start with a SHOCKING or mysterious hook that makes people stop scrolling
- Use vague but emotionally charged language (not real predictions — just vibes)
- Include a "secret" or "what the stars are hiding" angle
- Add urgency ("today", "right now", "this week is critical")
- End with a strong call to action (follow, share, comment their sign)
- Keep sentences SHORT and punchy — one idea per line
- Use emotional triggers: love, money, career, unexpected change
- Mention specific numbers (like "3 things", "the number 7", etc.) for credibility
- This does NOT need to be accurate — it just needs to FEEL real and urgent

Return ONLY a valid JSON object with these exact keys:
{{
  "hook": "opening line (1-2 sentences, very dramatic)",
  "body": ["line 1", "line 2", "line 3", "line 4", "line 5"],
  "reveal": "the big 'secret' or main prediction (1-2 sentences)",
  "cta": "call to action at the end",
  "lucky_number": 7,
  "lucky_color": "gold",
  "vibe_word": "TRANSFORMATIVE"
}}

Sign: {sign}
Hook suggestion (you can rewrite it): {hook}
"""

    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {
            "hook": f"The stars have a MAJOR message for {sign} today...",
            "body": [
                "Something unexpected is coming your way.",
                "The universe has been preparing you for this moment.",
                "Don't ignore the signs around you right now.",
                "Your energy is at an all-time high this week.",
                "Someone from your past may reach out soon.",
            ],
            "reveal": f"The cosmos say: trust your instincts, {sign}. Big changes are near.",
            "cta": f"Follow for daily {sign} updates! Drop your sign below 👇",
            "lucky_number": random.randint(1, 9),
            "lucky_color": random.choice(["gold", "saffron", "crimson", "ivory"]),
            "vibe_word": random.choice(["POWERFUL", "TRANSFORMATIVE", "MAGICAL", "INTENSE"]),
        }

    data["sign"] = sign
    data["date"] = today
    return data


# ─── AMBIENT AUDIO GENERATION (pure numpy — no AI, no TTS) ───────────────────

def butter_lowpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def apply_lowpass(data, cutoff=800, fs=SAMPLE_RATE, order=4):
    b, a = butter_lowpass(cutoff, fs, order)
    return lfilter(b, a, data)

def generate_ambient_audio(duration_sec: float, audio_path: Path, sign: str = "Leo"):
    """
    Generates a mystical ambient drone using additive synthesis.
    Technique:
      - Root tone (low fundamental ~55 Hz) with harmonics
      - Slow LFO tremolo (0.08 Hz) for breathing feel
      - Shimmer layer: high partial with random flutter
      - Bell chime hits at segment boundaries (pentatonic)
      - Fade in/out to avoid clicks
      - All 100% numpy — no downloads, no AI
    """
    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)

    # ── Drone root: fundamental + harmonics ──
    root_hz  = 55.0   # A1 — deep, grounding
    harmonics = [
        (1.0,   0.38),   # fundamental
        (2.0,   0.22),   # octave
        (3.0,   0.12),   # perfect 5th above octave
        (4.0,   0.08),   # 2 octaves
        (5.0,   0.05),   # major 3rd
        (6.0,   0.03),   # natural 7th
        (9.0,   0.02),   # shimmer
    ]
    drone = np.zeros_like(t)
    for mult, amp in harmonics:
        phase = random.uniform(0, 2 * math.pi)
        drone += amp * np.sin(2 * math.pi * root_hz * mult * t + phase)

    # Slow tremolo LFO (breathing)
    lfo_rate = 0.07
    lfo = 0.75 + 0.25 * np.sin(2 * math.pi * lfo_rate * t)
    drone *= lfo

    # ── Shimmer pad: high detuned layer ──
    shimmer_hz = root_hz * 8   # 3 octaves up
    shimmer = 0.12 * np.sin(2 * math.pi * shimmer_hz * t + np.sin(2 * math.pi * 0.3 * t))

    # ── Bell chime hits at segment starts ──
    chime_times = [0.5]  # hook start
    body_count = 5
    seg_durations = [5] + [4] * body_count + [5, 4, 4]
    elapsed = 0
    for d in seg_durations:
        elapsed += d
        if elapsed < duration_sec - 1:
            chime_times.append(elapsed)

    # Pentatonic chime frequencies (A minor pentatonic)
    pentatonic = [220.0, 261.63, 329.63, 392.0, 440.0, 523.25]
    chime_signal = np.zeros_like(t)
    for ct in chime_times:
        freq = random.choice(pentatonic)
        chime_amp = 0.28
        chime_decay = 2.5   # seconds
        start_idx = int(ct * SAMPLE_RATE)
        chime_len = min(int(chime_decay * SAMPLE_RATE), len(t) - start_idx)
        if chime_len <= 0:
            continue
        ct_arr = np.arange(chime_len) / SAMPLE_RATE
        chime_env = np.exp(-3.0 * ct_arr / chime_decay)
        chime_wave = chime_amp * chime_env * np.sin(2 * math.pi * freq * ct_arr)
        # Add slight inharmonic shimmer to the chime
        chime_wave += (chime_amp * 0.15) * chime_env * np.sin(2 * math.pi * freq * 2.01 * ct_arr)
        chime_signal[start_idx:start_idx + chime_len] += chime_wave

    # ── Mix ──
    mix = drone + shimmer + chime_signal

    # ── Low-pass filter to remove harshness ──
    mix = apply_lowpass(mix, cutoff=3500)

    # ── Normalize ──
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.82

    # ── Fade in / fade out ──
    fade_samples = int(SAMPLE_RATE * 1.5)
    fade_in  = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    mix[:fade_samples]  *= fade_in
    mix[-fade_samples:] *= fade_out

    # ── Write WAV ──
    audio_path_wav = audio_path.with_suffix(".wav")
    with wave.open(str(audio_path_wav), 'w') as wf:
        wf.setnchannels(1)       # mono
        wf.setsampwidth(2)       # 16-bit
        wf.setframerate(SAMPLE_RATE)
        pcm = (mix * 32767).astype(np.int16)
        wf.writeframes(pcm.tobytes())

    print(f"  🎵 Ambient audio saved: {audio_path_wav}")
    return audio_path_wav


# ─── FFMPEG ASSEMBLY ──────────────────────────────────────────────────────────

def build_video(script: dict, frames_dir: Path, audio_wav: Path,
                output_path: Path, saved_frames: list):
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.jpg"),
        "-i", str(audio_wav),
        "-vf", (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,"
            "format=yuv420p"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    print(f"\n  🎬 Running FFmpeg ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ FFmpeg error:\n{result.stderr[-2000:]}")
        raise RuntimeError("FFmpeg failed.")
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ Video saved: {output_path}  ({size_mb:.1f} MB)")


# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────

def generate_reel(sign: str = None, output_dir: Path = OUTPUT_DIR) -> Path:
    if sign is None:
        sign = random.choice(ZODIAC_SIGNS)

    date_str   = datetime.now().strftime("%Y%m%d")
    reel_name  = f"{sign.lower()}_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames" / reel_name
    audio_path = output_dir / f"{reel_name}_ambient"   # .wav added by function
    out_video  = output_dir / f"{reel_name}_reel.mp4"

    print(f"\n{'═'*56}")
    print(f"  🔮  {ZODIAC_EMOJIS.get(sign,'⭐')} {sign}  ·  {datetime.now().strftime('%B %d, %Y')}")
    print(f"{'═'*56}")

    # 1. Script
    print("\n  🤖  Calling Gemini for script...")
    script = generate_horoscope_script(sign)
    print(f"  ✅  Hook: {script['hook'][:65]}...")
    script_path = output_dir / f"{reel_name}_script.json"
    with open(script_path, "w") as f:
        json.dump(script, f, indent=2)
    print(f"  📝  Script: {script_path}")

    # 2. Frames
    print("\n  🖼️   Generating frames...")
    saved_frames = frame_generator.generate_all_frames(script, frames_dir)

    # 3. Ambient audio (programmatic — no AI, no TTS)
    body_count    = len(script.get("body", []))
    seg_durations = [5] + [4] * body_count + [5, 4, 4]
    total_secs    = sum(seg_durations)
    print(f"\n  🎵  Synthesizing {total_secs}s ambient drone...")
    audio_wav = generate_ambient_audio(total_secs + 2, audio_path, sign)

    # 4. Video
    print("\n  🎬  Assembling with FFmpeg...")
    build_video(script, frames_dir, audio_wav, out_video, saved_frames)

    print(f"\n  🎉  REEL COMPLETE → {out_video}")
    return out_video


def generate_all_signs(output_dir: Path = OUTPUT_DIR):
    print("\n🌟 Generating all 12 zodiac reels...")
    results = []
    for sign in ZODIAC_SIGNS:
        try:
            path = generate_reel(sign, output_dir)
            results.append((sign, "✅", path))
        except Exception as e:
            print(f"  ❌ {sign}: {e}")
            results.append((sign, f"❌ {e}", None))

    print("\n" + "═"*56)
    print("  📊  BATCH SUMMARY")
    print("═"*56)
    for sign, status, path in results:
        print(f"  {ZODIAC_EMOJIS.get(sign,'⭐')} {sign:<15} {status}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🔮 Horoscope Reel Generator — Jyotish Edition")
    parser.add_argument("--sign", choices=ZODIAC_SIGNS + ["all"], default=None,
                        help="Zodiac sign (or 'all'). Random if omitted.")
    parser.add_argument("--output", default="reels_output",
                        help="Output directory (default: reels_output/)")
    parser.add_argument("--api-key", default=None,
                        help="Gemini API key (or set GEMINI_API_KEY env var)")
    args = parser.parse_args()

    if args.api_key:
        GEMINI_API_KEY = args.api_key
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("❌ Provide Gemini API key via --api-key or GEMINI_API_KEY env var")
        raise SystemExit(1)

    out = Path(args.output)
    if args.sign == "all":
        generate_all_signs(out)
    else:
        generate_reel(args.sign, out)