#!/usr/bin/env python3
"""
🔮 Viral Horoscope Instagram Reel Generator — Jyotish Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Visual Identity: Deep Saffron · Cosmic Maroon · Gold · Warm Ivory
Audio: Programmatic ambient drone (numpy + scipy)
Format: 9:16 (1080x1920) — Instagram Reels / TikTok / YouTube Shorts

5 Viral Content Categories:
  relationships · career · current_events · emotional_healing · manifestation

Each category generates TWO reels per sign:
  → English reel    : {sign}_{category}_{date}_en_reel.mp4
  → Hindi reel      : {sign}_{category}_{date}_hi_reel.mp4

Dependencies (Windows):
    pip install google-genai pillow numpy scipy python-dotenv
    Download ffmpeg from https://www.gyan.dev/ffmpeg/builds/ and add to PATH
"""

import os
import json
import math
import random
import shutil
import subprocess
import textwrap
import wave
import argparse
from datetime import datetime
from pathlib import Path

# Load .env automatically
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── WINDOWS UTF-8 CONSOLE FIX ──────────────────────────────────────────────
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

import numpy as np
from scipy.signal import butter, lfilter
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import frame_generator
import fun_genre_frame_generator
from content_categories import (
    ALL_CATEGORIES, CATEGORY_VISUAL, get_prompt, make_fallback
)
from fun_genre_categories import (
    FUN_GENRES, get_genre_prompt, make_genre_fallback,
    get_all_subjects, get_subject, GENRE_DISPLAY,
)

# ─── CONFIG ───────────────────────────────────────────────────────────────────

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "YOUR_NVIDIA_API_KEY_HERE")
OUTPUT_DIR     = Path("reels_output")

WIDTH    = 1080
HEIGHT   = 1920
FPS      = 30
SAMPLE_RATE = 44100

# ─── BRAND PALETTE ────────────────────────────────────────────────────────────

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

SIGN_GRADIENTS = {
    "Aries":       ("#7B1F3A", "#FF6B00"),
    "Taurus":      ("#1A1A2E", "#2D7A4F"),
    "Gemini":      ("#FF6B00", "#F5C518"),
    "Cancer":      ("#1A1A2E", "#7B1F3A"),
    "Leo":         ("#7B1F3A", "#F5C518"),
    "Virgo":       ("#2D7A4F", "#1A1A2E"),
    "Libra":       ("#FDF8F0", "#F5C518"),
    "Scorpio":     ("#0D0D1A", "#7B1F3A"),
    "Sagittarius": ("#FF6B00", "#7B1F3A"),
    "Capricorn":   ("#1A1A2E", "#0D0D1A"),
    "Aquarius":    ("#1A1A2E", "#FF6B00"),
    "Pisces":      ("#7B1F3A", "#1A1A2E"),
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

# ─── BILINGUAL SCRIPT GENERATION ──────────────────────────────────────────────

def generate_bilingual_script(sign: str, category: str) -> dict:
    """
    Single NVIDIA API call that returns BOTH English and Hindi scripts.
    Returns: { "en": {...}, "hi": {...} }
    Falls back to built-in scripts on any failure.
    """
    import sys
    today = datetime.now().strftime("%B %d, %Y")
    prompt = get_prompt(sign, category, today)

    api_script = f'''
import os, json, sys, requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
api_key = os.environ.get("NVIDIA_API_KEY", "{NVIDIA_API_KEY}")
if not api_key or api_key == "YOUR_NVIDIA_API_KEY_HERE":
    print(json.dumps({{"error": "no_key"}}))
    sys.exit(0)
try:
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {{
        "Authorization": f"Bearer {{api_key}}",
        "Content-Type": "application/json"
    }}
    data = {{
        "model": "meta/llama-3.1-8b-instruct",
        "messages": [{{"role": "user", "content": {json.dumps(prompt)}}}],
        "temperature": 0.7,
        "max_tokens": 2000
    }}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        text = result['choices'][0]['message']['content'].strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.split("\\n")
            lines = [l for l in lines if not l.startswith("```")]
            text = "\\n".join(lines).strip()
        # Find JSON object boundaries
        start = text.find("{{")
        end   = text.rfind("}}") + 1
        if start != -1 and end > start:
            text = text[start:end]
        data = json.loads(text)
        print(json.dumps(data, ensure_ascii=True))
    else:
        print(json.dumps({{"error": f"API error {{response.status_code}}"}}))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
'''

    print(f"  [API] Calling NVIDIA API (bilingual, 40s timeout)...")
    try:
        result = subprocess.run(
            [sys.executable, "-c", api_script],
            capture_output=True,
            text=True,
            timeout=45,
            encoding="utf-8",
        )
        stdout = result.stdout.strip()
        if stdout:
            try:
                data = json.loads(stdout)
                # print(repr(data["hi"]["hook"][:50]))
                if "error" in data:
                    print(f"  [WARN] API error ({data['error']}) -- using fallback.")
                    return _make_bilingual_fallback(sign, category, today)
                if "en" not in data or "hi" not in data:
                    print(f"  [WARN] Unexpected JSON shape -- using fallback.")
                    return _make_bilingual_fallback(sign, category, today)
                # Inject metadata
                for lang in ("en", "hi"):
                    data[lang]["sign"]     = sign
                    data[lang]["date"]     = today
                    data[lang]["category"] = category
                    data[lang]["lang"]     = lang
                print(f"  [OK] Bilingual script generated via NVIDIA.")
                return data
            except json.JSONDecodeError as je:
                print(f"  [WARN] JSON parse failed ({je}) -- using fallback.")
        if result.returncode != 0:
                print(f"  [WARN] Subprocess error -- using fallback.")
    except subprocess.TimeoutExpired:
        print(f"  [WARN] NVIDIA timed out after 45s -- using fallback.")
    except Exception as e:
        print(f"  ⚠️  {e} — using fallback.")

    return _make_bilingual_fallback(sign, category, today)


def _make_bilingual_fallback(sign: str, category: str, today: str = None) -> dict:
    if today is None:
        today = datetime.now().strftime("%B %d, %Y")
    return {
        "en": make_fallback(sign, category, "en"),
        "hi": make_fallback(sign, category, "hi"),
    }


# ─── HOROSCOPE SCRIPT (backward-compat for basic horoscope usage) ─────────────

def _make_fallback_script(sign, today):
    return {
        "hook":         f"The stars have a MAJOR message for {sign} today...",
        "body":         [
            "Something unexpected is coming your way.",
            "The universe has been preparing you for this moment.",
            "Don't ignore the signs around you right now.",
            "Your energy is at an all-time high this week.",
            "Someone from your past may reach out soon.",
        ],
        "reveal":       f"The cosmos say: trust your instincts, {sign}. Big changes are near.",
        "cta":          f"Follow for daily {sign} updates! Drop your sign below",
        "lucky_number": random.randint(1, 9),
        "lucky_color":  random.choice(["gold", "saffron", "crimson", "ivory"]),
        "vibe_word":    random.choice(["POWERFUL", "TRANSFORMATIVE", "MAGICAL", "INTENSE"]),
        "sign":         sign,
        "date":         today,
        "category":     "horoscope",
        "lang":         "en",
    }


def generate_horoscope_script(sign: str) -> dict:
    """Backward-compatible single-language horoscope generation."""
    import sys
    today = datetime.now().strftime("%B %d, %Y")

    api_script = f'''
import os, json, sys, requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
api_key = os.environ.get("NVIDIA_API_KEY", "{NVIDIA_API_KEY}")
if not api_key or api_key == "YOUR_NVIDIA_API_KEY_HERE":
    print(json.dumps({{"error": "no_key"}}))
    sys.exit(0)
try:
    prompt = """You are a viral astrology content creator for Instagram Reels.
Create a 25-30 second horoscope reel script for {sign} for {today}.

Return ONLY a valid JSON object with exactly these keys:
{{
  "hook": "opening line (1-2 sentences, very dramatic)",
  "body": ["line 1", "line 2", "line 3", "line 4", "line 5"],
  "reveal": "the big secret or main prediction (1-2 sentences)",
  "cta": "call to action at the end",
  "lucky_number": 7,
  "lucky_color": "gold",
  "vibe_word": "TRANSFORMATIVE"
}}
"""
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {{
        "Authorization": f"Bearer {{api_key}}",
        "Content-Type": "application/json"
    }}
    data = {{
        "model": "meta/llama-3.1-8b-instruct",
        "messages": [{{"role": "user", "content": prompt}}],
        "temperature": 0.7,
        "max_tokens": 1000
    }}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        text = result['choices'][0]['message']['content'].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        data = json.loads(text)
        print(json.dumps(data))
    else:
        print(json.dumps({{"error": f"API error {{response.status_code}}"}}))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
'''

    print(f"  Calling NVIDIA API (30s timeout)...")
    try:
        result = subprocess.run(
            [sys.executable, "-c", api_script],
            capture_output=True, text=True, timeout=35, encoding="utf-8",
        )
        stdout = result.stdout.strip()
        if stdout:
            try:
                data = json.loads(stdout)
                if "error" in data:
                    return _make_fallback_script(sign, today)
                data["sign"] = sign
                data["date"] = today
                data["category"] = "horoscope"
                data["lang"] = "en"
                return data
            except json.JSONDecodeError:
                pass
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  NVIDIA timed out — using fallback.")
    except Exception as e:
        print(f"  ⚠️  {e} — using fallback.")

    return _make_fallback_script(sign, today)


# ─── AMBIENT AUDIO GENERATION ────────────────────────────────────────────────

def butter_lowpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    return butter(order, cutoff / nyq, btype='low', analog=False)

def apply_lowpass(data, cutoff=800, fs=SAMPLE_RATE, order=4):
    b, a = butter_lowpass(cutoff, fs, order)
    return lfilter(b, a, data)

def generate_ambient_audio(duration_sec: float, audio_path: Path, sign: str = "Leo",
                           category: str = "horoscope"):
    """
    Mystical ambient drone via additive synthesis.
    Category subtly shifts the root pitch and shimmer character.
    """
    # Slightly different root tone per category for emotional color
    root_map = {
        "relationships":     61.74,   # B1 — warm, longing
        "career":            65.41,   # C2 — grounded, determined
        "current_events":    55.00,   # A1 — neutral, news-like
        "emotional_healing": 58.27,   # Bb1 — soft, healing
        "manifestation":     69.30,   # C#2/Db2 — mystical, golden
        "horoscope":         55.00,   # A1 — default
    }
    root_hz = root_map.get(category, 55.0)

    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    harmonics = [
        (1.0, 0.38), (2.0, 0.22), (3.0, 0.12),
        (4.0, 0.08), (5.0, 0.05), (6.0, 0.03), (9.0, 0.02),
    ]
    drone = np.zeros_like(t)
    for mult, amp in harmonics:
        phase = random.uniform(0, 2 * math.pi)
        drone += amp * np.sin(2 * math.pi * root_hz * mult * t + phase)

    lfo_rate = 0.07
    lfo = 0.75 + 0.25 * np.sin(2 * math.pi * lfo_rate * t)
    drone *= lfo

    shimmer_hz = root_hz * 8
    shimmer = 0.12 * np.sin(2 * math.pi * shimmer_hz * t + np.sin(2 * math.pi * 0.3 * t))

    chime_times = [0.5]
    seg_durations = [6] + [6] * 5 + [8]
    elapsed = 0
    for d in seg_durations:
        elapsed += d
        if elapsed < duration_sec - 1:
            chime_times.append(elapsed)

    pentatonic = [220.0, 261.63, 329.63, 392.0, 440.0, 523.25]
    chime_signal = np.zeros_like(t)
    for ct in chime_times:
        freq = random.choice(pentatonic)
        chime_amp = 0.28
        chime_decay = 2.5
        start_idx = int(ct * SAMPLE_RATE)
        chime_len = min(int(chime_decay * SAMPLE_RATE), len(t) - start_idx)
        if chime_len <= 0:
            continue
        ct_arr = np.arange(chime_len) / SAMPLE_RATE
        chime_env = np.exp(-3.0 * ct_arr / chime_decay)
        chime_wave = chime_amp * chime_env * np.sin(2 * math.pi * freq * ct_arr)
        chime_wave += (chime_amp * 0.15) * chime_env * np.sin(2 * math.pi * freq * 2.01 * ct_arr)
        chime_signal[start_idx:start_idx + chime_len] += chime_wave

    mix = drone + shimmer + chime_signal
    mix = apply_lowpass(mix, cutoff=3500)
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.82

    fade_samples = int(SAMPLE_RATE * 1.5)
    mix[:fade_samples]  *= np.linspace(0, 1, fade_samples)
    mix[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    audio_path_wav = audio_path.with_suffix(".wav")
    with wave.open(str(audio_path_wav), 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        pcm = (mix * 32767).astype(np.int16)
        wf.writeframes(pcm.tobytes())

    print(f"  [AUDIO] Ambient audio: {audio_path_wav}")
    return audio_path_wav


# ─── FFMPEG ───────────────────────────────────────────────────────────────────

def _find_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    common_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "ffmpeg" / "bin" / "ffmpeg.exe",
        Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
        Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
    ]
    for p in common_paths:
        if p.exists():
            return str(p)
    return "ffmpeg"


def build_video(script: dict, frames_dir: Path, audio_wav: Path,
                output_path: Path, frame_count: int = 0,
                soundtrack_path: Path = None):
    ffmpeg = _find_ffmpeg()

    if soundtrack_path and soundtrack_path.exists():
        print(f"  [AUDIO] Mixing soundtrack: {soundtrack_path.name} (skipping ambient drone)")
        cmd = [
            ffmpeg, "-y",
            "-framerate", str(FPS),
            "-i", str(frames_dir / "frame_%05d.jpg"),
            "-i", str(soundtrack_path),
            "-map", "0:v", "-map", "1:a",
            "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        cmd = [
            ffmpeg, "-y",
            "-framerate", str(FPS),
            "-i", str(frames_dir / "frame_%05d.jpg"),
            "-i", str(audio_wav),
            "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(output_path),
        ]

    print(f"\n  [FFMPEG] Running FFmpeg ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [ERROR] FFmpeg error:\n{result.stderr[-2000:]}")
        raise RuntimeError("FFmpeg failed.")
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  [OK] Video: {output_path}  ({size_mb:.1f} MB)")


# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────

def select_soundtrack():
    """Selects a soundtrack evenly using a state file, returning the Path and its metadata."""
    music_json_path = Path("soundtrack/music.json")
    music_state_path = Path("soundtrack/.music_state.json")

    if not music_json_path.exists():
        return None, None

    try:
        with open(music_json_path, "r", encoding="utf-8") as f:
            music_data = json.load(f)
    except Exception as e:
        print(f"  [WARN] Failed to read music.json: {e}")
        return None, None

    if not music_data:
        return None, None

    state = {"queue": []}
    if music_state_path.exists():
        try:
            with open(music_state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    import random
    available_keys = list(music_data.keys())
    
    # Filter queue to available tracks
    queue = [k for k in state.get("queue", []) if k in available_keys]
    
    # Refill queue if empty
    if not queue:
        queue = available_keys.copy()
        random.shuffle(queue)
    
    selected_key = queue.pop(0)
    
    # Save updated queue
    state["queue"] = queue
    try:
        with open(music_state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass
    
    return Path("soundtrack") / selected_key, music_data[selected_key]

def generate_reel_bilingual(sign: str, category: str,
                            output_dir: Path = OUTPUT_DIR,
                            soundtrack: Path = None) -> tuple:
    """
    Generate two reels (English + Hindi) for one sign + category.
    Returns (en_path, hi_path).
    """
    date_str = datetime.now().strftime("%Y%m%d")
    slug     = f"{sign.lower()}_{category}_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n" + "="*60)
    print(f"  {sign}  [{category.upper()}]  {datetime.now().strftime('%B %d, %Y')}")
    print("="*60)

    # ── 1. Generate bilingual script ──────────────────────────────
    print("\n  [SCRIPT] Generating bilingual script via Gemini...")
    bilingual = generate_bilingual_script(sign, category)
    script_en = bilingual["en"]
    script_hi = bilingual["hi"]

    # ── 1.5 Soundtrack Selection ──────────────────────────────────
    actual_soundtrack = soundtrack
    if not actual_soundtrack or str(actual_soundtrack) == "auto":
        st_path, st_info = select_soundtrack()
        if st_path and st_path.exists():
            actual_soundtrack = st_path
            credit_text = f"Music provided by {st_info['name']} ({st_info['credit_source']})"
            script_en["soundtrack_credit"] = credit_text
            script_hi["soundtrack_credit"] = credit_text
            print(f"  [AUDIO] Selected soundtrack automatically: {st_path.name}")

    # Save scripts
    for lang, script in [("en", script_en)]:
        sp = output_dir / f"{slug}_{lang}_script.json"
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Scripts saved.")

    # ── 2. Shared ambient audio (same for both languages) ─────────
    body_count    = len(script_en.get("body", []))
    seg_durations = [6] + [6] * body_count + [8]
    total_secs    = sum(seg_durations)
    audio_path    = output_dir / f"{slug}_ambient"
    print(f"\n  [AUDIO] Synthesizing {total_secs}s ambient drone ({category})...")
    audio_wav = generate_ambient_audio(total_secs + 2, audio_path, sign, category)

    results = {}
    
    # ── 3. English reel ───────────────────────────────────────────
    for lang, script in [("en", script_en)]:
        lang_label = "English" if lang == "en" else "Hindi"
        print(f"\n  [{lang.upper()}] Generating {lang_label} reel...")

        frames_dir = output_dir / "frames" / f"{slug}_{lang}"
        out_video  = output_dir / f"{slug}_{lang}_reel.mp4"

        print(f"  [FRAMES] Rendering frames ({lang_label})...")
        frame_generator.generate_all_frames(script, frames_dir)

        print(f"  [VIDEO] Assembling video ({lang_label})...")
        build_video(script, frames_dir, audio_wav, out_video,
                    soundtrack_path=actual_soundtrack)

        print(f"  [DONE] {lang_label} reel -> {out_video}")
        results[lang] = out_video

    return results.get("en"), results.get("hi")


# ─── FUN GENRE PIPELINE ──────────────────────────────────────────────────────

def _generate_genre_script(genre: str, subject_label: str, extra: dict) -> dict:
    """
    Call NVIDIA API for a fun-genre script.  Falls back to built-in on any error.
    extra contains letters / months / sign_a+sign_b depending on genre.
    """
    today = datetime.now().strftime("%B %d, %Y")
    prompt = get_genre_prompt(genre, subject_label, extra, today)

    api_script = f'''
import os, json, sys, requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
api_key = os.environ.get("NVIDIA_API_KEY", "{NVIDIA_API_KEY}")
if not api_key or api_key == "YOUR_NVIDIA_API_KEY_HERE":
    print(json.dumps({{"error": "no_key"}}))
    sys.exit(0)
try:
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {{"Authorization": f"Bearer {{api_key}}", "Content-Type": "application/json"}}
    data = {{
        "model": "meta/llama-3.1-8b-instruct",
        "messages": [{{"role": "user", "content": {json.dumps(prompt)}}}],
        "temperature": 0.8,
        "max_tokens": 1200
    }}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        text = response.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            lines = [l for l in text.split("\\n") if not l.startswith("```")]
            text = "\\n".join(lines).strip()
        start = text.find("{{")
        end   = text.rfind("}}") + 1
        if start != -1 and end > start:
            text = text[start:end]
        print(json.dumps(json.loads(text), ensure_ascii=True))
    else:
        print(json.dumps({{"error": f"API {{response.status_code}}}}}}))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
'''

    print(f"  [API] Calling NVIDIA API for {genre} ({subject_label}, 40s timeout)...")
    try:
        result = subprocess.run(
            [sys.executable, "-c", api_script],
            capture_output=True, text=True, timeout=45, encoding="utf-8",
        )
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            if "error" not in data:
                # Inject mandatory metadata
                data["genre"]   = genre
                data["subject"] = subject_label
                data["sign"]    = extra.get("sign", genre.upper())
                data["lang"]    = "en"
                data["date"]    = today
                # Inject genre-specific subject info
                for k in ("letters", "months", "sign_a", "sign_b"):
                    if k in extra:
                        data[k] = extra[k]
                print(f"  [OK] Genre script generated via NVIDIA.")
                return data
            print(f"  [WARN] API error ({data.get('error')}) — using fallback.")
    except subprocess.TimeoutExpired:
        print(f"  [WARN] NVIDIA timed out — using fallback.")
    except Exception as e:
        print(f"  [WARN] {e} — using fallback.")

    fb = make_genre_fallback(genre, subject_label, extra)
    fb["date"] = today
    return fb


def generate_fun_genre_reel(
    genre: str,
    subject_slug: str,
    output_dir: Path = OUTPUT_DIR,
    soundtrack: Path = None,
) -> Path:
    """
    Generate one fun-genre reel (English only).
    Returns the path to the output .mp4.
    """
    slug_info = get_subject(genre, subject_slug)   # (slug, label, extra)
    slug, label, extra = slug_info

    date_str   = datetime.now().strftime("%Y%m%d")
    file_slug  = f"{slug.lower()}_{genre}_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n" + "="*60)
    print(f"  [{genre.upper()}]  {label}  [{datetime.now().strftime('%B %d, %Y')}]")
    print("="*60)

    # ── Script ───────────────────────────────────────────────────
    script = _generate_genre_script(genre, label, extra)

    # ── Soundtrack ───────────────────────────────────────────────
    actual_soundtrack = soundtrack
    if not actual_soundtrack or str(actual_soundtrack) == "auto":
        st_path, st_info = select_soundtrack()
        if st_path and st_path.exists():
            actual_soundtrack = st_path
            script["soundtrack_credit"] = (
                f"Music provided by {st_info['name']} ({st_info['credit_source']})"
            )
            print(f"  [AUDIO] Selected soundtrack: {st_path.name}")

    # Save script JSON
    sp = output_dir / f"{file_slug}_en_script.json"
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(script, fh, indent=2, ensure_ascii=False)
    print(f"  [OK] Script saved → {sp.name}")

    # ── Frames ───────────────────────────────────────────────────
    frames_dir = output_dir / "frames" / file_slug
    print(f"  [FRAMES] Rendering genre frames...")
    fun_genre_frame_generator.generate_all_genre_frames(script, frames_dir)

    # ── Audio ────────────────────────────────────────────────────
    # Duration: hook(6) + insights(6) + extra(6) + stats(8) = 26s + crossfades
    total_secs = 6 + 6 + 6 + 8
    audio_path = output_dir / f"{file_slug}_ambient"
    print(f"  [AUDIO] Synthesizing {total_secs}s ambient drone ({genre})...")
    audio_wav  = generate_ambient_audio(total_secs + 2, audio_path, "Leo", "manifestation")

    # ── Video ────────────────────────────────────────────────────
    out_video = output_dir / f"{file_slug}_en_reel.mp4"
    print(f"  [VIDEO] Assembling video...")
    build_video(script, frames_dir, audio_wav, out_video,
                soundtrack_path=actual_soundtrack)
    print(f"  [DONE] Genre reel → {out_video}")
    return out_video


def _process_fun_genre_subject(args):
    genre, slug, output_dir, soundtrack = args
    try:
        path = generate_fun_genre_reel(genre, slug, output_dir, soundtrack)
        return (slug, "✅", path)
    except Exception as e:
        print(f"  [ERROR] {genre}/{slug}: {e}")
        return (slug, f"❌ {e}", None)


def generate_all_fun_genre(
    genre: str,
    output_dir: Path = OUTPUT_DIR,
    soundtrack: Path = None,
    parallel: bool = False,
):
    """Generate reels for every subject in a fun genre."""
    import concurrent.futures
    subjects = get_all_subjects(genre)
    print(f"\n[START] Generating {len(subjects)} {genre.upper()} reels...")
    args_list = [(genre, slug, output_dir, soundtrack) for slug, _, _ in subjects]

    if parallel:
        print("  [MODE] Parallel execution enabled")
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            results = list(ex.map(_process_fun_genre_subject, args_list))
    else:
        results = [_process_fun_genre_subject(a) for a in args_list]

    print("\n" + "="*60)
    print("  BATCH SUMMARY — " + genre.upper())
    print("="*60)
    for slug, status, _ in results:
        print(f"  {slug:<20} {status}")


def generate_reel(sign: str = None, output_dir: Path = OUTPUT_DIR,
                  soundtrack: Path = None) -> Path:
    """
    Backward-compatible: generate a single English horoscope reel.
    """
    if sign is None:
        sign = random.choice(ZODIAC_SIGNS)

    date_str   = datetime.now().strftime("%Y%m%d")
    reel_name  = f"{sign.lower()}_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames" / reel_name
    audio_path = output_dir / f"{reel_name}_ambient"
    out_video  = output_dir / f"{reel_name}_reel.mp4"

    print(f"\n" + "="*56)
    print(f"  {sign}  [{datetime.now().strftime('%B %d, %Y')}]")
    print("="*56)

    print("\n  [API] Calling NVIDIA for script...")
    script = generate_horoscope_script(sign)
    print(f"  [OK] Hook: {script['hook'][:65]}...")

    actual_soundtrack = soundtrack
    if not actual_soundtrack or str(actual_soundtrack) == "auto":
        st_path, st_info = select_soundtrack()
        if st_path and st_path.exists():
            actual_soundtrack = st_path
            script["soundtrack_credit"] = f"Music provided by {st_info['name']} ({st_info['credit_source']})"
            print(f"  [AUDIO] Selected soundtrack automatically: {st_path.name}")

    sp = output_dir / f"{reel_name}_script.json"
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)

    print("\n  [FRAMES] Generating frames...")
    frame_generator.generate_all_frames(script, frames_dir)

    body_count    = len(script.get("body", []))
    seg_durations = [6] + [6] * body_count + [8]
    total_secs    = sum(seg_durations)
    print(f"\n  [AUDIO] Synthesizing {total_secs}s ambient drone...")
    audio_wav = generate_ambient_audio(total_secs + 2, audio_path, sign)

    print("\n  [VIDEO] Assembling with FFmpeg...")
    build_video(script, frames_dir, audio_wav, out_video,
                soundtrack_path=actual_soundtrack)

    print(f"\n  [DONE] REEL COMPLETE -> {out_video}")
    return out_video


def _process_sign_bilingual(args):
    sign, category, output_dir, soundtrack = args
    try:
        en_p, hi_p = generate_reel_bilingual(sign, category, output_dir, soundtrack)
        return (sign, "✅", en_p, hi_p)
    except Exception as e:
        print(f"  [ERROR] {sign}: {e}")
        return (sign, f"❌ {e}", None, None)

def _process_sign_horoscope(args):
    sign, output_dir, soundtrack = args
    try:
        path = generate_reel(sign, output_dir, soundtrack=soundtrack)
        return (sign, "✅", path, None)
    except Exception as e:
        print(f"  [ERROR] {sign}: {e}")
        return (sign, f"❌ {e}", None, None)

def generate_all_signs(output_dir: Path = OUTPUT_DIR, soundtrack: Path = None,
                       category: str = None, parallel: bool = False):
    import concurrent.futures
    if category and category != "horoscope":
        # Viral category — bilingual
        print(f"\n[START] Generating all 12 zodiac reels ({category.upper()}) -- EN + HI...")
        results = []
        args_list = [(sign, category, output_dir, soundtrack) for sign in ZODIAC_SIGNS]
        if parallel:
            print("  [MODE] Parallel execution enabled")
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
                results = list(executor.map(_process_sign_bilingual, args_list))
        else:
            for args in args_list:
                results.append(_process_sign_bilingual(args))
    else:
        # Classic horoscope
        print("\n[START] Generating all 12 zodiac reels (horoscope)...")
        results = []
        args_list = [(sign, output_dir, soundtrack) for sign in ZODIAC_SIGNS]
        if parallel:
            print("  [MODE] Parallel execution enabled")
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
                results = list(executor.map(_process_sign_horoscope, args_list))
        else:
            for args in args_list:
                results.append(_process_sign_horoscope(args))

    print("\n" + "="*60)
    print("  BATCH SUMMARY")
    print("="*60)
    for row in results:
        sign, status = row[0], row[1]
        print(f"  {sign:<15} {status}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🔮 Viral Horoscope Reel Generator — Bilingual + Fun Genres Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (classic sign-based):
  python Generate.py --sign Leo --category relationships
  python Generate.py --sign all --category career --parallel
  python Generate.py --sign Aries --category all
  python Generate.py --sign Leo   (classic horoscope, English only)

Examples (fun genres):
  python Generate.py --genre name_initials --subject AJ
  python Generate.py --genre name_initials --subject all
  python Generate.py --genre lucky_month   --subject MAY_JUN
  python Generate.py --genre lucky_month   --subject all
  python Generate.py --genre compatibility --subject ARI_SCO
  python Generate.py --genre compatibility --subject all --parallel
        """
    )
    parser.add_argument("--sign", choices=ZODIAC_SIGNS + ["all"], default=None,
                        help="Zodiac sign or 'all'. Random if omitted.")
    parser.add_argument("--category",
                        choices=ALL_CATEGORIES + ["all", "horoscope"],
                        default="horoscope",
                        help="Content category. 'horoscope' = classic English-only.")
    parser.add_argument("--genre",
                        choices=FUN_GENRES + ["all"],
                        default=None,
                        help="Fun genre: name_initials | lucky_month | compatibility | all")
    parser.add_argument("--subject",
                        default="all",
                        help="Subject slug within the genre, or 'all' (default: all).")
    parser.add_argument("--output", default="reels_output",
                        help="Output directory (default: reels_output/)")
    parser.add_argument("--api-key", default=None,
                        help="NVIDIA API key (or set NVIDIA_API_KEY env var)")
    parser.add_argument("--soundtrack", default="auto",
                        help="Path to a soothing soundtrack file, or 'auto' to select evenly (default: auto)")
    parser.add_argument("--parallel", action="store_true",
                        help="Generate all subjects/signs in parallel to save time")
    args = parser.parse_args()

    if args.api_key:
        NVIDIA_API_KEY = args.api_key
    if NVIDIA_API_KEY == "YOUR_NVIDIA_API_KEY_HERE":
        print("❌ Provide NVIDIA API key via --api-key or NVIDIA_API_KEY env var")
        raise SystemExit(1)

    # Resolve soundtrack
    soundtrack = "auto"
    if args.soundtrack and args.soundtrack != "auto":
        soundtrack = Path(args.soundtrack)
        if not soundtrack.exists():
            alt = Path("soundtrack") / args.soundtrack
            soundtrack = alt if alt.exists() else "auto"
            if soundtrack == "auto":
                print(f"⚠️  Soundtrack not found — falling back to auto.")

    out      = Path(args.output)
    sign_arg = args.sign
    cat_arg  = args.category
    genre_arg = args.genre

    try:
        # ── Fun genre path ──────────────────────────────────────────────────
        if genre_arg:
            genres = FUN_GENRES if genre_arg == "all" else [genre_arg]
            for g in genres:
                if args.subject == "all":
                    generate_all_fun_genre(g, out, soundtrack=soundtrack,
                                           parallel=args.parallel)
                else:
                    generate_fun_genre_reel(g, args.subject, out, soundtrack=soundtrack)

        # ── Classic sign / category path ────────────────────────────────────
        else:
            categories = ALL_CATEGORIES if cat_arg == "all" else [cat_arg]
            for cat in categories:
                if sign_arg == "all":
                    generate_all_signs(out, soundtrack=soundtrack,
                                       category=cat, parallel=args.parallel)
                elif cat == "horoscope":
                    generate_reel(sign_arg, out, soundtrack=soundtrack)
                else:
                    generate_reel_bilingual(sign_arg, cat, out, soundtrack=soundtrack)

    except Exception as e:
        print(f"\n[FATAL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)