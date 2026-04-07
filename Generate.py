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


# ─── DRAWING HELPERS ──────────────────────────────────────────────────────────

def draw_gradient_bg(draw, width, height, color1: str, color2: str):
    """Vertical gradient background."""
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    for y in range(height):
        t  = y / height
        r  = int(r1 + (r2 - r1) * t)
        g  = int(g1 + (g2 - g1) * t)
        b  = int(b1 + (b2 - b1) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

def draw_mandala_watermark(draw, cx, cy, radius=480):
    """
    Lightweight SVG-style mandala approximation using PIL circles + lines.
    Opacity ~4% — purely decorative brand watermark.
    """
    petal_count = 12
    ring_fill = (245, 197, 24, 8)     # Gold, very low alpha
    ring_stroke = (255, 107, 0, 18)   # Saffron, low alpha

    # Concentric rings
    for r in range(radius, 40, -60):
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=ring_stroke, width=1)

    # Radial petals
    for i in range(petal_count):
        angle = (2 * math.pi / petal_count) * i
        x1 = cx + int(radius * 0.25 * math.cos(angle))
        y1 = cy + int(radius * 0.25 * math.sin(angle))
        x2 = cx + int(radius * 0.92 * math.cos(angle))
        y2 = cy + int(radius * 0.92 * math.sin(angle))
        draw.line([(x1, y1), (x2, y2)], fill=ring_stroke, width=1)

    # Inner petal circles
    for i in range(petal_count):
        angle = (2 * math.pi / petal_count) * i + math.pi / petal_count
        pr = radius * 0.55
        px = cx + int(pr * math.cos(angle))
        py = cy + int(pr * math.sin(angle))
        pr2 = radius * 0.12
        draw.ellipse([px-pr2, py-pr2, px+pr2, py+pr2],
                     outline=ring_stroke, width=1)

def draw_star_field(draw, width, height, count=220):
    """Scattered star dots in ivory/gold tones."""
    for _ in range(count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.choice([1, 1, 1, 2, 2, 3])
        alpha = random.randint(60, 200)
        color = random.choice([
            (255, 255, 255, alpha),
            (245, 197, 24, alpha),     # gold shimmer
            (253, 248, 240, alpha),    # ivory
        ])
        draw.ellipse([x, y, x+size, y+size], fill=color)

def get_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def wrap_text(text: str, max_chars: int = 26) -> list:
    return textwrap.wrap(text, width=max_chars)

def draw_pill(draw, cx, y, text, font, bg_color, text_color):
    """Rounded pill badge."""
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = 36, 18
    rx0 = cx - tw // 2 - pad_x
    ry0 = y - th // 2 - pad_y
    rx1 = cx + tw // 2 + pad_x
    ry1 = y + th // 2 + pad_y
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=40, fill=bg_color)
    draw.text((cx, y), text, font=font, anchor="mm", fill=text_color)
    return ry1

def draw_divider(draw, cx, y, width=880, color=(245, 197, 24, 90)):
    """Gold accent divider line."""
    draw.line([(cx - width//2, y), (cx + width//2, y)], fill=color, width=2)
    # Small diamond ornament at center
    d = 8
    draw.polygon([(cx, y-d), (cx+d, y), (cx, y+d), (cx-d, y)],
                 fill=(245, 197, 24, 160))


# ─── FRAME FACTORY ───────────────────────────────────────────────────────────

def create_frame(script: dict, frame_type: str) -> Image.Image:
    sign     = script["sign"]
    c1, c2   = SIGN_GRADIENTS.get(sign, ("#1A1A2E", "#7B1F3A"))
    accent   = SIGN_ACCENT.get(sign, "#F5C518")
    acc_rgb  = hex_to_rgb(accent)

    img  = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    # ── Background gradient ──
    draw_gradient_bg(draw, WIDTH, HEIGHT, c1, c2)

    # ── Mandala watermark (very subtle) ──
    draw_mandala_watermark(draw, WIDTH // 2, HEIGHT // 2, radius=500)

    # ── Star field ──
    draw_star_field(draw, WIDTH, HEIGHT)

    # ── Glow circle behind sign symbol ──
    cx, cy = WIDTH // 2, 640
    glow_r = 200
    for offset in range(glow_r, 80, -20):
        alpha = int(55 * (1 - (offset - 80) / glow_r))
        draw.ellipse(
            [cx - offset, cy - offset, cx + offset, cy + offset],
            fill=(*acc_rgb, alpha)
        )

    # ── Zodiac symbol ──
    emoji    = ZODIAC_EMOJIS.get(sign, "⭐")
    font_em  = get_font(170, bold=True)
    draw.text((cx, cy), emoji, font=font_em, anchor="mm",
              fill=(255, 255, 255, 240))

    # ── Sign name pill badge ──
    font_sign = get_font(58, bold=True)
    sign_y    = cy + 230
    draw_pill(draw, cx, sign_y, sign.upper(), font_sign,
              (*acc_rgb, 220), hex_to_rgb(PALETTE["charcoal"]) + (255,))

    # ── Date ──
    font_date = get_font(34)
    draw.text((cx, sign_y + 80), script["date"], font=font_date,
              anchor="mm", fill=(253, 248, 240, 140))

    # ── Gold divider ──
    draw_divider(draw, cx, sign_y + 130)

    # ── Content block ──
    text_y   = sign_y + 190
    font_h   = get_font(56, bold=True)
    font_b   = get_font(50, bold=True)
    font_sm  = get_font(42)
    ivory    = hex_to_rgb(PALETTE["ivory"]) + (255,)
    gold     = (*hex_to_rgb(PALETTE["gold"]), 255)
    saffron  = (*hex_to_rgb(PALETTE["saffron"]), 255)

    if frame_type == "hook":
        lines = wrap_text(script["hook"], max_chars=22)
        for line in lines:
            draw.text((cx, text_y), line, font=font_h, anchor="mm",
                      fill=(*hex_to_rgb(PALETTE["ivory"]), 255))
            text_y += 100

    elif frame_type.startswith("body_"):
        idx   = int(frame_type.split("_")[1])
        body  = script.get("body", [])
        total = len(body)
        if idx < total:
            # Progress dots
            dot_y = text_y - 30
            dot_spacing = 28
            total_w = total * dot_spacing
            for di in range(total):
                dx = cx - total_w // 2 + di * dot_spacing + dot_spacing // 2
                col = gold if di == idx else (255, 255, 255, 60)
                r   = 8 if di == idx else 5
                draw.ellipse([dx-r, dot_y-r, dx+r, dot_y+r], fill=col)
            text_y += 30

            lines = wrap_text(body[idx], max_chars=24)
            for line in lines:
                draw.text((cx, text_y), line, font=font_b, anchor="mm",
                          fill=ivory)
                text_y += 95

    elif frame_type == "reveal":
        lbl_font = get_font(42, bold=True)
        draw_pill(draw, cx, text_y, "🔮  THE VERDICT", lbl_font,
                  (*hex_to_rgb(PALETTE["maroon"]), 220), gold)
        text_y += 80
        lines = wrap_text(script["reveal"], max_chars=22)
        for line in lines:
            draw.text((cx, text_y), line, font=font_b, anchor="mm",
                      fill=(*hex_to_rgb(PALETTE["ivory"]), 255))
            text_y += 95

    elif frame_type == "stats":
        lbl_font = get_font(44, bold=True)
        draw.text((cx, text_y), "TODAY'S ENERGY", font=lbl_font,
                  anchor="mm", fill=gold)
        text_y += 90
        draw_divider(draw, cx, text_y, width=600,
                     color=(*hex_to_rgb(PALETTE["saffron"]), 80))
        text_y += 40

        stats = [
            (f"✨  {script.get('vibe_word', 'POWERFUL')}",  gold),
            (f"🍀  Lucky #{script.get('lucky_number', 7)}",   ivory),
            (f"🎨  {script.get('lucky_color', 'Gold').title()}", ivory),
        ]
        for stat_text, stat_col in stats:
            draw.text((cx, text_y), stat_text, font=font_sm,
                      anchor="mm", fill=stat_col)
            text_y += 90

    elif frame_type == "cta":
        lbl_font = get_font(46, bold=True)
        draw_pill(draw, cx, text_y, "👇  DON'T FORGET", lbl_font,
                  (*hex_to_rgb(PALETTE["saffron"]), 200),
                  hex_to_rgb(PALETTE["charcoal"]) + (255,))
        text_y += 90
        lines = wrap_text(script["cta"], max_chars=24)
        for line in lines:
            draw.text((cx, text_y), line, font=font_sm,
                      anchor="mm", fill=ivory)
            text_y += 80

    # ── Bottom branding strip ──
    brand_y = HEIGHT - 70
    draw.rectangle([(0, brand_y - 45), (WIDTH, HEIGHT)],
                   fill=(*hex_to_rgb(PALETTE["charcoal"]), 180))
    draw.text((cx, brand_y), "✨  JyoteshAI  ✨",
              font=get_font(34), anchor="mm",
              fill=(*hex_to_rgb(PALETTE["gold"]), 200))

    return img.convert("RGB")


# ─── FRAME SEQUENCE ───────────────────────────────────────────────────────────

def generate_frames(script: dict, frames_dir: Path) -> list:
    frames_dir.mkdir(parents=True, exist_ok=True)

    body_count = len(script.get("body", []))
    segments   = (
        [("hook", 5)]
        + [(f"body_{i}", 4) for i in range(body_count)]
        + [("reveal", 5), ("stats", 4), ("cta", 4)]
    )

    saved_frames = []
    for idx, (ftype, duration) in enumerate(segments):
        img  = create_frame(script, ftype)
        path = frames_dir / f"frame_{idx:05d}.jpg"
        img.save(path, quality=95)
        saved_frames.append((path, duration))
        print(f"    🖼️  frame {idx+1}/{len(segments)}: {ftype}")

    return saved_frames, segments


# ─── FFMPEG ASSEMBLY ──────────────────────────────────────────────────────────

def build_video(script: dict, frames_dir: Path, audio_wav: Path,
                output_path: Path):
    segments_def = (
        [("hook", 5)]
        + [(f"body_{i}", 4) for i in range(len(script.get("body", [])))]
        + [("reveal", 5), ("stats", 4), ("cta", 4)]
    )

    concat_file = frames_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for idx, (_, duration) in enumerate(segments_def):
            img_path = frames_dir / f"frame_{idx:05d}.jpg"
            f.write(f"file '{img_path.resolve()}'\n")
            f.write(f"duration {duration}\n")
        last_img = frames_dir / f"frame_{len(segments_def)-1:05d}.jpg"
        f.write(f"file '{last_img.resolve()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
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
        "-r", str(FPS),
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
    generate_frames(script, frames_dir)

    # 3. Ambient audio (programmatic — no AI, no TTS)
    body_count    = len(script.get("body", []))
    seg_durations = [5] + [4] * body_count + [5, 4, 4]
    total_secs    = sum(seg_durations)
    print(f"\n  🎵  Synthesizing {total_secs}s ambient drone...")
    audio_wav = generate_ambient_audio(total_secs + 2, audio_path, sign)

    # 4. Video
    print("\n  🎬  Assembling with FFmpeg...")
    build_video(script, frames_dir, audio_wav, out_video)

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