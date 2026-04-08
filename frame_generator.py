#!/usr/bin/env python3
"""
Frame Generator v4 — Jyotesh AI Visual Identity
─────────────────────────────────────────────────
Changes from v3:
  • SPLIT font system: text font (Segoe UI / Arial) vs symbol font (Segoe UI Symbol)
    → no more boxes for zodiac glyphs OR garbled text
  • Aggressive font caching via lru_cache — 10× fewer font loads
  • Better timing: hook 6s, body 6s, stats 8s — readable pacing
  • Wider text wrapping (24-28 chars) for fewer, cleaner lines
  • Hold phase at end of each slide — text stays visible 30-40% of duration
  • Smoother, slower text reveal animations
  • Subtle floating particle effects and shimmer for premium feel
  • Fully Windows-compatible; also works on macOS / Linux

Install:
  pip install pillow

Usage:
  python frame_generator.py
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap, os, math, sys, random
from pathlib import Path
from functools import lru_cache

# ─── BRAND PALETTE ────────────────────────────────────────────────────────────
P = {
    "saffron":  "#FF6B00",
    "maroon":   "#7B1F3A",
    "gold":     "#F5C518",
    "ivory":    "#FDF8F0",
    "cream":    "#FFFBF2",
    "charcoal": "#1A1A2E",
    "gray":     "#6B6B80",
    "green":    "#2D7A4F",
    "midnight": "#0D0D1A",
}

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

WIDTH, HEIGHT = 1080, 1920
FPS = 30

# ─── ZODIAC: plain Unicode (U+2648…U+2653) ───────────────────────────────────
ZODIAC_CHAR = {
    "Aries":"♈","Taurus":"♉","Gemini":"♊","Cancer":"♋",
    "Leo":"♌","Virgo":"♍","Libra":"♎","Scorpio":"♏",
    "Sagittarius":"♐","Capricorn":"♑","Aquarius":"♒","Pisces":"♓",
}

SIGN_DARK = {"Scorpio", "Capricorn", "Aquarius"}   # dark-bg signs

# ─── FONT RESOLUTION — SPLIT: text vs symbol ─────────────────────────────────

def _try_fonts(candidates, size):
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


@lru_cache(maxsize=64)
def get_text_font(size, bold=False):
    """
    Font for readable Latin text (headers, body, labels).
    Uses Segoe UI on Windows, system fonts elsewhere.
    """
    if sys.platform == "win32":
        candidates = [
            r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    else:  # Linux
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        ]
    return _try_fonts(candidates, size)


@lru_cache(maxsize=32)
def get_symbol_font(size):
    """
    Font for zodiac glyphs (♈♉♊ etc.) and decorative Unicode symbols.
    Uses Segoe UI Symbol on Windows — the only font guaranteed to have them.
    """
    if sys.platform == "win32":
        candidates = [
            r"C:\Windows\Fonts\seguisym.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Apple Symbols.ttf",
        ]
    else:  # Linux
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    return _try_fonts(candidates, size)


# Backward compat alias — old code that calls get_font() still works
def get_font(size, bold=False):
    return get_text_font(size, bold)

# ─── EASING FUNCTIONS ─────────────────────────────────────────────────────────
def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def ease_out_back(t, overshoot=1.70158):
    s = overshoot
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2

def ease_out_expo(t):
    return 1 if t == 1 else 1 - 2 ** (-10 * t)

def lerp(a, b, t):
    return a + (b - a) * t

def alpha_lerp(start_a, end_a, t):
    return int(lerp(start_a, end_a, t))

# ─── DRAWING PRIMITIVES ───────────────────────────────────────────────────────
def draw_gradient(draw, w, h, c1, c2):
    r1,g1,b1 = hex_rgb(c1)
    r2,g2,b2 = hex_rgb(c2)
    for i in range(h):
        t = i / h
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(0, i), (w, i)], fill=(r, g, b))

def draw_mandala(draw, cx, cy, r=480, color=(123,31,58), alpha=10):
    c = (*color, alpha)
    for ring_r in [r*0.9, r*0.7, r*0.5, r*0.3, r*0.15]:
        draw.ellipse([cx-ring_r, cy-ring_r, cx+ring_r, cy+ring_r], outline=c, width=1)
    for deg in range(0, 360, 30):
        angle = math.radians(deg)
        x1 = cx + r*0.15*math.cos(angle); y1 = cy + r*0.15*math.sin(angle)
        x2 = cx + r*0.9 *math.cos(angle); y2 = cy + r*0.9 *math.sin(angle)
        draw.line([(x1,y1),(x2,y2)], fill=c, width=1)
    for deg in range(0, 360, 30):
        angle = math.radians(deg)
        pr = r * 0.55
        px = cx + pr*math.cos(angle); py = cy + pr*math.sin(angle)
        pr2 = r * 0.07
        draw.ellipse([px-pr2, py-pr2, px+pr2, py+pr2], outline=c, width=1)

def draw_gold_divider(draw, cx, y, w=800, alpha=120):
    gold = (*hex_rgb(P["gold"]), alpha)
    draw.line([(cx-w//2, y), (cx+w//2, y)], fill=gold, width=2)
    d = 12
    draw.polygon([(cx,y-d),(cx+d,y),(cx,y+d),(cx-d,y)], fill=(*hex_rgb(P["gold"]),160))

def draw_pill_badge(draw, cx, cy, text, font, bg, fg):
    bbox = font.getbbox(text)
    tw = bbox[2]-bbox[0]; th = bbox[3]-bbox[1]
    px, py = 40, 20
    draw.rounded_rectangle([cx-tw//2-px, cy-th//2-py, cx+tw//2+px, cy+th//2+py],
                            radius=40, fill=bg)
    draw.text((cx, cy), text, font=font, anchor="mm", fill=fg)

def draw_star_ornament(draw, sx, sy, col):
    d=10
    draw.polygon([(sx,sy-d),(sx+d*0.6,sy-d*0.2),(sx+d,sy+d*0.4),
                  (sx+d*0.3,sy+d),(sx-d*0.3,sy+d),(sx-d,sy+d*0.4),
                  (sx-d*0.6,sy-d*0.2)], fill=col)

# ─── FLOATING PARTICLES (premium shimmer) ─────────────────────────────────────
def _generate_particles(n=18, seed=42):
    """Pre-generate particle positions for consistent across frames."""
    rng = random.Random(seed)
    particles = []
    for _ in range(n):
        particles.append({
            "x": rng.uniform(40, WIDTH - 40),
            "y": rng.uniform(100, HEIGHT - 150),
            "r": rng.uniform(1.5, 4.0),
            "speed": rng.uniform(0.3, 1.2),
            "phase": rng.uniform(0, math.pi * 2),
            "drift_x": rng.uniform(-0.4, 0.4),
        })
    return particles

_PARTICLES = _generate_particles()

def draw_particles(draw, t, color_rgb, base_alpha=40):
    """Draw subtle floating particles that drift and pulse."""
    for p in _PARTICLES:
        # slow vertical drift + gentle sine wave on x
        py = (p["y"] - p["speed"] * t * 300) % (HEIGHT - 200) + 100
        px = p["x"] + math.sin(t * 2 + p["phase"]) * 20 * p["drift_x"]
        # pulse alpha
        alpha = int(base_alpha * (0.5 + 0.5 * math.sin(t * 3 + p["phase"])))
        alpha = max(0, min(255, alpha))
        r = p["r"]
        draw.ellipse([px-r, py-r, px+r, py+r],
                     fill=(*color_rgb, alpha))


# ─── STATIC BACKGROUND LAYER (rendered once per slide) ────────────────────────
def make_background(sign, is_dark):
    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")

    if is_dark:
        draw_gradient(draw, WIDTH, HEIGHT, "#1A1A2E", "#0D0D1A")
    else:
        draw_gradient(draw, WIDTH, HEIGHT, "#FDF8F0", "#FFFBF2")

    return img

# ─── COMPOSITE: alpha-paste an RGBA layer onto an RGB base ────────────────────
def alpha_paste(base_rgb, overlay_rgba):
    """Paste an RGBA overlay onto an RGB base and return RGB."""
    base = base_rgb.convert("RGBA")
    base.alpha_composite(overlay_rgba)
    return base.convert("RGB")

# ─── TEXT WITH ANIMATED FADE-IN ───────────────────────────────────────────────
def animated_text(draw, cx, y, text, font, color_rgb, progress):
    """
    Draw text that fades in from left-to-right character by character.
    progress: 0.0 (invisible) → 1.0 (fully visible)
    """
    if progress <= 0:
        return

    # When fully revealed, draw entire string at full opacity — no per-char fade
    if progress >= 1.0:
        draw.text((cx, y), text, font=font, anchor="mt", fill=(*color_rgb, 255))
        return

    chars = list(text)
    n = len(chars)
    # measure full string to centre
    bbox = font.getbbox(text)
    total_w = bbox[2] - bbox[0]
    x = cx - total_w // 2

    for i, ch in enumerate(chars):
        # each char has its own alpha based on where the reveal wave is
        char_prog = max(0.0, min(1.0, progress * (n + 4) / max(n, 1) - i / max(n, 1)))
        alpha = int(ease_out_cubic(min(1.0, char_prog)) * 255)
        cb = font.getbbox(ch)
        cw = cb[2] - cb[0]
        if alpha > 0:
            draw.text((x, y), ch, font=font, fill=(*color_rgb, alpha))
        x += cw

# ─── HOOK FRAME ANIMATION ─────────────────────────────────────────────────────
def create_hook_frames(script, duration_s=6):
    """Generate a list of PIL.Image RGB for the hook slide."""
    sign = script["sign"]
    is_dark = sign in SIGN_DARK
    tc_hex = P["maroon"] if not is_dark else P["gold"]

    bg = make_background(sign, is_dark)
    frames = []
    total = FPS * duration_s
    cx = WIDTH // 2

    # Pre-load fonts (cached, but let's be explicit)
    f_brand = get_text_font(36)
    f_date  = get_text_font(34)
    f_sym   = get_symbol_font(200)
    f_name  = get_text_font(68, bold=True)
    f_hook  = get_text_font(56, bold=True)
    f_bottom = get_text_font(40)

    particle_col = hex_rgb(P["gold"] if is_dark else P["saffron"])

    for f in range(total):
        t = f / max(total - 1, 1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        # ── Floating particles ────────────────────────────────────────
        draw_particles(draw, t, particle_col, base_alpha=25 if is_dark else 15)

        # ── Brand header (fades in 0..0.10) ──────────────────────────
        hdr_t = ease_out_cubic(min(1.0, t / 0.10))
        brand_col = (*hex_rgb(P["saffron"] if not is_dark else P["gold"]), int(200*hdr_t))
        draw.text((cx, 80), "JyoteshAI",
                  font=f_brand, anchor="mm", fill=brand_col)
        draw.text((cx, 130), script["date"],
                  font=f_date, anchor="mm",
                  fill=(*hex_rgb(P["gray"]), int(180*hdr_t)))
        if hdr_t > 0:
            draw.rectangle([cx-60, 155, cx+60, 157],
                           fill=(*hex_rgb(P["saffron"]), int(180*hdr_t)))

        # ── Zodiac circle (scale + fade in 0.08..0.35) ────────────────
        circ_t = ease_out_back(max(0.0, min(1.0, (t - 0.08) / 0.27)))
        symbol_y = 520
        circle_r = int(240 * circ_t)

        if circle_r > 0:
            # glow rings
            for gr in [circle_r+80, circle_r+50, circle_r+20]:
                ga = int(30 * (1-(gr-circle_r)/80) * circ_t)
                draw.ellipse([cx-gr, symbol_y-gr, cx+gr, symbol_y+gr],
                             outline=(*hex_rgb(P["saffron"]), ga), width=1)
            circle_fill = (*hex_rgb(P["maroon"] if is_dark else "#F0E8DC"), 255)
            draw.ellipse([cx-circle_r, symbol_y-circle_r, cx+circle_r, symbol_y+circle_r],
                         fill=circle_fill,
                         outline=(*hex_rgb(P["maroon"]), 80), width=2)
            # Zodiac symbol — using SYMBOL font
            sym_a = int(240 * circ_t)
            draw.text((cx, symbol_y),
                      ZODIAC_CHAR.get(sign, "\u2605"),
                      font=f_sym, anchor="mm",
                      fill=(*hex_rgb(tc_hex), sym_a))

        # (pulsing glow ring removed for cleaner look)

        # ── Sign name badge (slide up 0.30..0.45) ─────────────────────
        name_y_target = symbol_y + 240 + 80
        badge_t = ease_out_cubic(max(0.0, min(1.0, (t - 0.30) / 0.15)))
        name_y = name_y_target + int(60 * (1 - badge_t))
        badge_bg = (*hex_rgb(P["saffron"] if not is_dark else P["gold"]), int(220*badge_t))
        badge_fg = (*hex_rgb(P["charcoal"]), 255)
        if badge_t > 0:
            draw_pill_badge(draw, cx, name_y, sign.upper(), f_name,
                            badge_bg, badge_fg)

        # ── Gold divider (fades 0.42..0.50) ──────────────────────────
        div_y = name_y_target + 90
        div_t = ease_out_cubic(max(0.0, min(1.0, (t - 0.42) / 0.08)))
        if div_t > 0:
            draw_gold_divider(draw, cx, div_y, alpha=int(120*div_t))

        # ── Hook text: line-by-line reveal (0.45..0.75) then HOLD ─────
        hook_anim_start = 0.45
        hook_anim_end = 0.75
        hook_t = max(0.0, min(1.0, (t - hook_anim_start) / (hook_anim_end - hook_anim_start)))

        if hook_t > 0 or t >= hook_anim_end:
            # After hook_anim_end, text stays at full visibility (hold phase)
            display_t = 1.0 if t >= hook_anim_end else hook_t
            hook_y = div_y + 80
            lines = textwrap.wrap(script["hook"], width=24)
            for li, line in enumerate(lines):
                line_delay = li * 0.18
                line_t = max(0.0, min(1.0, (display_t - line_delay) / max(1.0 - line_delay, 0.001)))
                col_rgb = hex_rgb(P["charcoal"] if not is_dark else P["ivory"])
                offset_y = int(25 * (1 - ease_out_cubic(line_t)))
                animated_text(draw, cx, hook_y + offset_y, line,
                               f_hook, col_rgb, line_t)
                hook_y += 85

        # ── Bottom strip ──────────────────────────────────────────────
        strip_a = int(240 * ease_out_cubic(min(1.0, t / 0.10)))
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["charcoal"]), strip_a))
        if strip_a > 0:
            for sx in [cx-180, cx+180]:
                draw_star_ornament(draw, sx, HEIGHT-50,
                                   (*hex_rgb(P["gold"]), strip_a))
            draw.text((cx, HEIGHT-50), "JyoteshAI",
                      font=f_bottom, anchor="mm",
                      fill=(*hex_rgb(P["gold"]), strip_a))

        # ── Composite onto background ─────────────────────────────────
        frames.append(alpha_paste(bg, img))

    return frames

# ─── BODY FRAME ANIMATION ─────────────────────────────────────────────────────
def create_body_frames(script, body_idx, duration_s=6):
    sign = script["sign"]
    is_dark = sign in SIGN_DARK
    body = script.get("body", [])

    bg = make_background(sign, is_dark=False)  # body always light
    frames = []
    total = FPS * duration_s
    cx = WIDTH // 2

    # Pre-load fonts (cached)
    f_header = get_text_font(40, bold=True)
    f_date   = get_text_font(32)
    f_body   = get_text_font(60, bold=True)
    f_vibe_l = get_text_font(38)
    f_vibe_v = get_text_font(58, bold=True)
    f_bottom = get_text_font(40)
    f_sym    = get_symbol_font(40)

    particle_col = hex_rgb(P["saffron"])

    for f in range(total):
        t = f / max(total - 1, 1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        # ── Floating particles ────────────────────────────────────────
        draw_particles(draw, t, particle_col, base_alpha=12)

        # ── Maroon header strip ───────────────────────────────────────
        hdr_t = ease_out_cubic(min(1.0, t / 0.08))
        strip_y = int(-160 * (1 - hdr_t))
        draw.rectangle([0, strip_y, WIDTH, 160 + strip_y],
                       fill=(*hex_rgb(P["maroon"]), 255))

        # Sign name with symbol — draw symbol separately with symbol font
        sign_label = sign.upper()
        zodiac_sym = ZODIAC_CHAR.get(sign, '')
        # Draw: "♌  LEO" — symbol with symbol font, text with text font
        header_text = f"{sign_label}"
        # Measure to center the combined text
        sym_bbox = f_sym.getbbox(zodiac_sym)
        sym_w = sym_bbox[2] - sym_bbox[0] if zodiac_sym else 0
        hdr_bbox = f_header.getbbox(header_text)
        hdr_w = hdr_bbox[2] - hdr_bbox[0]
        gap = 20
        combined_w = sym_w + gap + hdr_w
        start_x = cx - combined_w // 2

        if zodiac_sym:
            draw.text((start_x, 55+strip_y), zodiac_sym,
                      font=f_sym, anchor="lm",
                      fill=(*hex_rgb(P["gold"]), 255))
        draw.text((start_x + sym_w + gap, 55+strip_y), header_text,
                  font=f_header, anchor="lm",
                  fill=(*hex_rgb(P["gold"]), 255))

        draw.text((cx, 115+strip_y), script["date"],
                  font=f_date, anchor="mm",
                  fill=(255,255,255,120))

        # ── Progress dots ─────────────────────────────────────────────
        dot_a = int(200 * ease_out_cubic(min(1.0, t / 0.15)))
        dot_y = 240
        total_dots = len(body)
        dot_spacing = 40
        start_x = cx - (total_dots * dot_spacing) // 2
        for i in range(total_dots):
            dx = start_x + i * dot_spacing + 20
            if i == body_idx:
                draw.rounded_rectangle([dx-20, dot_y-8, dx+20, dot_y+8], 8,
                                       fill=(*hex_rgb(P["saffron"]), dot_a))
            else:
                draw.ellipse([dx-8, dot_y-8, dx+8, dot_y+8],
                             fill=(*hex_rgb(P["gray"]), dot_a//3))

        # ── Body text: line-by-line reveal (0.10..0.55) then HOLD ─────
        anim_start = 0.10
        anim_end = 0.55
        text_prog = max(0.0, min(1.0, (t - anim_start) / (anim_end - anim_start)))
        # After anim_end, hold at full visibility
        if t >= anim_end:
            text_prog = 1.0

        text_y = 340
        if body_idx < len(body):
            lines = textwrap.wrap(body[body_idx], width=26)
            n_lines = len(lines)
            for li, line in enumerate(lines):
                line_delay = li * 0.15
                line_t = max(0.0, min(1.0,
                    (text_prog - line_delay) / max(1.0 - line_delay, 0.001)))
                offset_y = int(30 * (1 - ease_out_cubic(line_t)))
                col_rgb = hex_rgb(P["charcoal"])
                animated_text(draw, cx, text_y + offset_y, line,
                               f_body, col_rgb, line_t)
                text_y += 100

        # ── Vibe accent (slides up 0.55..0.75, then holds) ────────────
        vibe_anim_t = max(0.0, min(1.0, (t - 0.55) / 0.20))
        if t >= 0.75:
            vibe_anim_t = 1.0
        vibe_prog = ease_out_cubic(vibe_anim_t)
        vibe_y = max(text_y + 60, 900)
        vibe_a = int(160 * vibe_prog)
        if vibe_a > 0:
            draw.line([(cx-200, vibe_y),(cx+200, vibe_y)],
                      fill=(*hex_rgb(P["maroon"]), vibe_a//4), width=1)
            draw.text((cx, vibe_y+40), "TODAY'S ENERGY",
                      font=f_vibe_l, anchor="mm",
                      fill=(*hex_rgb(P["gray"]), vibe_a))
            draw.text((cx, vibe_y+110), script.get("vibe_word", "POWERFUL"),
                      font=f_vibe_v, anchor="mm",
                      fill=(*hex_rgb(P["saffron"]), vibe_a))

        # ── Bottom strip ──────────────────────────────────────────────
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["charcoal"]), 240))
        draw.text((cx, HEIGHT-50), "JyoteshAI",
                  font=f_bottom, anchor="mm",
                  fill=(*hex_rgb(P["gold"]), 220))

        frames.append(alpha_paste(bg, img))

    return frames

# ─── STATS FRAME ANIMATION ────────────────────────────────────────────────────
def create_stats_frames(script, duration_s=8):
    sign = script["sign"]
    bg = make_background(sign, is_dark=True)
    frames = []
    total = FPS * duration_s
    cx = WIDTH // 2

    # Pre-load fonts (cached)
    f_title  = get_text_font(46, bold=True)
    f_sign   = get_text_font(38)
    f_label  = get_text_font(36)
    f_value  = get_text_font(52, bold=True)
    f_reveal = get_text_font(48, bold=True)
    f_cta    = get_text_font(40, bold=True)
    f_bottom = get_text_font(36)
    f_sym    = get_symbol_font(38)

    # Use text labels instead of Unicode symbols that may render as boxes
    stats = [
        ("Lucky Number", str(script.get("lucky_number", 7))),
        ("Power Color",  script.get("lucky_color", "Gold").title()),
        ("Today's Vibe", script.get("vibe_word", "POWERFUL")),
        ("Sign",         sign),
    ]

    particle_col = hex_rgb(P["gold"])

    for f in range(total):
        t = f / max(total - 1, 1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        # ── Floating particles ────────────────────────────────────────
        draw_particles(draw, t, particle_col, base_alpha=30)

        # ── Header ───────────────────────────────────────────────────
        h_t = ease_out_cubic(min(1.0, t / 0.08))
        h_a = int(255 * h_t)
        draw.text((cx, 120), "TODAY'S COSMIC NUMBERS",
                  font=f_title, anchor="mm",
                  fill=(*hex_rgb(P["gold"]), h_a))

        # Sign name + zodiac symbol (drawn separately)
        sign_text = sign.upper()
        zodiac_sym = ZODIAC_CHAR.get(sign, '')
        sign_a = int(200 * h_t)
        # Draw combined: "SIGN  ♌" — text with text font, symbol with symbol font
        txt_bbox = f_sign.getbbox(sign_text)
        txt_w = txt_bbox[2] - txt_bbox[0]
        sym_bbox = f_sym.getbbox(zodiac_sym) if zodiac_sym else (0,0,0,0)
        sym_w = sym_bbox[2] - sym_bbox[0] if zodiac_sym else 0
        gap = 16
        total_w = txt_w + gap + sym_w
        sx = cx - total_w // 2
        draw.text((sx, 185), sign_text,
                  font=f_sign, anchor="lm",
                  fill=(*hex_rgb(P["saffron"]), sign_a))
        if zodiac_sym:
            draw.text((sx + txt_w + gap, 185), zodiac_sym,
                      font=f_sym, anchor="lm",
                      fill=(*hex_rgb(P["saffron"]), sign_a))

        if h_t > 0:
            draw_gold_divider(draw, cx, 230, w=700, alpha=int(200*h_t))

        # ── Stat cards (staggered slide-in, 0.08..0.50, then hold) ────
        card_h = 160; card_w = 900
        card_x = (WIDTH - card_w) // 2
        card_y_base = 310

        for i, (label, value) in enumerate(stats):
            card_delay = 0.08 + i * 0.08
            card_anim_end = card_delay + 0.15
            card_t = ease_out_cubic(max(0.0, min(1.0, (t - card_delay) / 0.15)))
            if t >= card_anim_end:
                card_t = 1.0
            slide_x = int(200 * (1 - card_t))
            card_y = card_y_base + i * (card_h + 20)
            card_a = int(255 * card_t)

            if card_a > 0:
                # card bg
                draw.rounded_rectangle(
                    [card_x + slide_x, card_y,
                     card_x + card_w + slide_x, card_y + card_h],
                    radius=20,
                    fill=(*hex_rgb("#FFFFFF"), min(card_a//10, 20)),
                    outline=(*hex_rgb(P["gold"]), min(card_a//4, 50)),
                    width=1)
                # Use ✦ symbol with symbol font, label with text font
                star_sym = "\u2726"
                star_text = f"  {label}"
                # Draw star with symbol font
                draw.text((cx + slide_x - 100, card_y+52), star_sym,
                          font=f_sym, anchor="mm",
                          fill=(*hex_rgb(P["gold"]), card_a//2))
                draw.text((cx + slide_x + 10, card_y+52), label,
                          font=f_label, anchor="mm",
                          fill=(*hex_rgb(P["gray"]), card_a//2))
                draw.text((cx + slide_x, card_y+115), value,
                          font=f_value, anchor="mm",
                          fill=(*hex_rgb(P["ivory"]), card_a))

        # ── Reveal text (0.50..0.70, then hold) ───────────────────────
        rev_y_start = card_y_base + 4 * (card_h + 20) + 40
        rev_anim_end = 0.70
        rev_prog = max(0.0, min(1.0, (t - 0.50) / 0.20))
        if t >= rev_anim_end:
            rev_prog = 1.0

        if rev_prog > 0:
            draw_gold_divider(draw, cx, rev_y_start, w=700,
                              alpha=int(200*rev_prog))
            rev_y = rev_y_start + 60
            lines = textwrap.wrap(script.get("reveal",""), width=28)
            for li, line in enumerate(lines):
                line_delay = li * 0.12
                line_t = max(0.0, min(1.0,
                    (rev_prog - line_delay) / max(1.0-line_delay, 0.001)))
                offset_y = int(25*(1-ease_out_cubic(line_t)))
                animated_text(draw, cx, rev_y+offset_y, line,
                               f_reveal,
                               hex_rgb(P["ivory"]), line_t)
                rev_y += 75

        # ── CTA pill (0.75..0.88, then hold) ──────────────────────────
        cta_anim_end = 0.88
        cta_t = ease_out_back(max(0.0, min(1.0, (t - 0.75) / 0.13)))
        if t >= cta_anim_end:
            cta_t = 1.0
        cta_y = max(rev_y_start + 250, HEIGHT - 300)
        if cta_t > 0:
            cta_bg = (*hex_rgb(P["saffron"]), int(220*cta_t))
            draw_pill_badge(draw, cx, cta_y, "FOLLOW FOR DAILY UPDATES",
                            f_cta, cta_bg,
                            (*hex_rgb(P["charcoal"]), 255))

        # ── Bottom strip ──────────────────────────────────────────────
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["maroon"]), 200))
        draw.text((cx, HEIGHT-50), "JyoteshAI  \u2022  Daily Vedic Astrology",
                  font=f_bottom, anchor="mm",
                  fill=(*hex_rgb(P["gold"]), 200))

        frames.append(alpha_paste(bg, img))

    return frames

# ─── TRANSITION: cross-dissolve between last frame of A and first of B ────────
def make_crossfade(frame_a, frame_b, n=12):
    """Return n frames cross-dissolving from frame_a → frame_b."""
    result = []
    for i in range(n):
        t = i / max(n - 1, 1)
        alpha = int(255 * ease_in_out_sine(t))
        blend = Image.new("RGB", (WIDTH, HEIGHT))
        blend.paste(frame_a)
        overlay = frame_b.copy().convert("RGBA")
        overlay.putalpha(alpha)
        blend.paste(frame_b, mask=overlay.split()[3])
        result.append(blend)
    return result

# ─── MAIN GENERATOR ───────────────────────────────────────────────────────────
def _save_frames(frames, frames_dir, counter):
    """Save a batch of frames to disk and return the new counter + last frame."""
    last = None
    for frame in frames:
        path = frames_dir / f"frame_{counter:05d}.jpg"
        frame.save(path, quality=94, optimize=True)
        last = frame
        counter += 1
    return counter, last


def generate_all_frames(script, frames_dir: Path):
    """
    Render all slides and save frames incrementally to avoid OOM.
    Returns the total frame count (not the images themselves).
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    counter = 0

    try:
        print("  Rendering hook slide ...")
        hook_frames = create_hook_frames(script, duration_s=6)
        counter, last_frame = _save_frames(hook_frames, frames_dir, counter)
        del hook_frames  # free memory immediately

        for i in range(len(script.get("body", []))):
            print(f"  Rendering body slide {i+1} ...")
            body_frames = create_body_frames(script, i, duration_s=6)
            # cross-dissolve 12 frames between slides
            fade = make_crossfade(last_frame, body_frames[0], n=12)
            counter, _ = _save_frames(fade, frames_dir, counter)
            del fade
            counter, last_frame = _save_frames(body_frames, frames_dir, counter)
            del body_frames

        print("  Rendering stats slide ...")
        stats_frames = create_stats_frames(script, duration_s=8)
        fade = make_crossfade(last_frame, stats_frames[0], n=12)
        counter, _ = _save_frames(fade, frames_dir, counter)
        del fade
        counter, last_frame = _save_frames(stats_frames, frames_dir, counter)
        del stats_frames

    except Exception as e:
        print(f"\n  ❌ Error during frame generation: {e}")
        import traceback
        traceback.print_exc()
        raise

    print(f"\n  Done: {counter} frames saved to {frames_dir}")
    print(f"  Total duration: ~{counter/FPS:.1f}s at {FPS} fps")
    return counter


# ─── DEMO ENTRY POINT ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo_script = {
        "sign":         "Leo",
        "date":         "7 April 2025",
        "hook":         "Your fire is unstoppable today",
        "body": [
            "The Sun energises your 10th house of fame and career",
            "Bold moves pay off — speak your truth in meetings",
            "Love life glows: a warm conversation opens new doors",
        ],
        "vibe_word":    "RADIANT",
        "lucky_number": 1,
        "lucky_color":  "Gold",
        "reveal":       "Destiny favours the brave today",
    }

    out = Path("jyotesh_frames_leo")
    generate_all_frames(demo_script, out)