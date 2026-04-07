#!/usr/bin/env python3
"""
Frame Generator v3 — Jyotesh AI Visual Identity
─────────────────────────────────────────────────
Changes from v2:
  • Cross-platform font resolution (Windows + Linux)
  • Zodiac symbols drawn as TEXT glyphs (not color emoji) → no boxes
  • Smooth per-frame animation: fade-in, slide-up, scale pulse
  • Each logical "slide" expands into N sub-frames at 30 fps
  • Clean text animation: characters appear with an opacity sweep

Install:
  pip install pillow

Usage:
  python frame_generator_v3.py
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap, os, math, sys
from pathlib import Path

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

# ─── ZODIAC: plain Unicode (U+2648…U+2653) — works everywhere ────────────────
# These are ASTROLOGICAL SIGNS in the BMP, not colour emoji.
# DejaVu, Liberation, FreeSans, Arial all contain them.
ZODIAC_CHAR = {
    "Aries":"\u2648","Taurus":"\u2649","Gemini":"\u264A","Cancer":"\u264B",
    "Leo":"\u264C","Virgo":"\u264D","Libra":"\u264E","Scorpio":"\u264F",
    "Sagittarius":"\u2650","Capricorn":"\u2651","Aquarius":"\u2652","Pisces":"\u2653",
}

SIGN_DARK = {"Scorpio", "Capricorn", "Aquarius"}   # dark-bg signs

# ─── FONT RESOLUTION ──────────────────────────────────────────────────────────
def _try_fonts(candidates, size):
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_font(size, bold=False):
    """
    Text font — contains BMP zodiac glyphs on all platforms.
    Priority: platform-specific best → DejaVu → Liberation → FreeSans → fallback
    """
    if sys.platform == "win32":
        candidates = [
            r"C:\Windows\Fonts\seguisym.ttf",          # Segoe UI Symbol — best BMP zodiac on Win
            r"C:\Windows\Fonts\seguibl.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
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

# ─── EASING FUNCTIONS ─────────────────────────────────────────────────────────
def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def ease_out_back(t, overshoot=1.70158):
    s = overshoot
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2

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

# ─── STATIC BACKGROUND LAYER (rendered once per slide) ────────────────────────
def make_background(sign, is_dark):
    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")

    if is_dark:
        draw_gradient(draw, WIDTH, HEIGHT, "#1A1A2E", "#0D0D1A")
        mc = hex_rgb(P["gold"])
    else:
        draw_gradient(draw, WIDTH, HEIGHT, "#FDF8F0", "#FFFBF2")
        mc = hex_rgb(P["maroon"])

    draw_mandala(draw, WIDTH//2, HEIGHT//2, r=500, color=mc, alpha=8)
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
    chars = list(text)
    n = len(chars)
    # measure full string to centre
    bbox = font.getbbox(text)
    total_w = bbox[2] - bbox[0]
    x = cx - total_w // 2

    for i, ch in enumerate(chars):
        # each char has its own alpha based on where the reveal wave is
        char_prog = max(0.0, min(1.0, progress * n - i)) 
        alpha = int(ease_out_cubic(char_prog) * 255)
        cb = font.getbbox(ch)
        cw = cb[2] - cb[0]
        draw.text((x, y), ch, font=font, fill=(*color_rgb, alpha))
        x += cw

# ─── HOOK FRAME ANIMATION ─────────────────────────────────────────────────────
def create_hook_frames(script, duration_s=5):
    """Generate a list of (PIL.Image RGB, 1) tuples for the hook slide."""
    sign = script["sign"]
    is_dark = sign in SIGN_DARK
    tc_hex = P["maroon"] if not is_dark else P["gold"]

    bg = make_background(sign, is_dark)
    frames = []
    total = FPS * duration_s
    cx = WIDTH // 2

    for f in range(total):
        t = f / max(total - 1, 1)           # 0..1 across the full slide
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        # ── Brand header (fades in 0..0.15) ──────────────────────────────
        hdr_t = ease_out_cubic(min(1.0, t / 0.15))
        brand_col = (*hex_rgb(P["saffron"] if not is_dark else P["gold"]), int(200*hdr_t))
        draw.text((cx, 80), "JYOTESH AI",
                  font=get_font(36), anchor="mm", fill=brand_col)
        draw.text((cx, 130), script["date"],
                  font=get_font(34), anchor="mm",
                  fill=(*hex_rgb(P["gray"]), int(180*hdr_t)))
        if hdr_t > 0:
            draw.rectangle([cx-60, 155, cx+60, 157],
                           fill=(*hex_rgb(P["saffron"]), int(180*hdr_t)))

        # ── Zodiac circle (scale + fade in 0.1..0.45) ────────────────────
        circ_t = ease_out_back(max(0.0, min(1.0, (t - 0.10) / 0.35)))
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
            # Zodiac symbol — plain Unicode text glyph
            sym_a = int(240 * circ_t)
            draw.text((cx, symbol_y),
                      ZODIAC_CHAR.get(sign, "\u2605"),
                      font=get_font(220, bold=True), anchor="mm",
                      fill=(*hex_rgb(tc_hex), sym_a))

        # Slow rotation pulse on the glow (0..360° over full duration)
        pulse_angle = (t * 360) % 360
        pulse_r = 250 + 15 * math.sin(math.radians(pulse_angle * 3))
        draw.ellipse([cx-pulse_r, symbol_y-pulse_r, cx+pulse_r, symbol_y+pulse_r],
                     outline=(*hex_rgb(P["gold"]), max(0, int(40*circ_t))), width=1)

        # ── Sign name badge (slide up 0.40..0.60) ─────────────────────────
        name_y_target = symbol_y + 240 + 80
        badge_t = ease_out_cubic(max(0.0, min(1.0, (t - 0.40) / 0.20)))
        name_y = name_y_target + int(60 * (1 - badge_t))
        badge_bg = (*hex_rgb(P["saffron"] if not is_dark else P["gold"]), int(220*badge_t))
        badge_fg = (*hex_rgb(P["charcoal"]), 255)
        if badge_t > 0:
            draw_pill_badge(draw, cx, name_y, sign.upper(), get_font(72, bold=True),
                            badge_bg, badge_fg)

        # ── Gold divider (fades 0.55..0.65) ──────────────────────────────
        div_y = name_y_target + 90
        div_t = ease_out_cubic(max(0.0, min(1.0, (t - 0.55) / 0.10)))
        if div_t > 0:
            draw_gold_divider(draw, cx, div_y, alpha=int(120*div_t))

        # ── Hook text: character-by-character reveal (0.60..1.0) ─────────
        hook_t = max(0.0, min(1.0, (t - 0.60) / 0.40))
        if hook_t > 0:
            hook_y = div_y + 80
            lines = textwrap.wrap(script["hook"], width=20)
            for li, line in enumerate(lines):
                line_delay = li * 0.20
                line_t = max(0.0, min(1.0, (hook_t - line_delay) / (1.0 - line_delay + 0.001)))
                col_rgb = hex_rgb(P["charcoal"] if not is_dark else P["ivory"])
                # slide up
                offset_y = int(30 * (1 - ease_out_cubic(line_t)))
                animated_text(draw, cx, hook_y + offset_y, line,
                               get_font(60, bold=True), col_rgb, line_t)
                hook_y += 90

        # ── Bottom strip ──────────────────────────────────────────────────
        strip_a = int(240 * ease_out_cubic(min(1.0, t / 0.15)))
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["charcoal"]), strip_a))
        if strip_a > 0:
            for sx in [cx-180, cx+180]:
                draw_star_ornament(draw, sx, HEIGHT-50,
                                   (*hex_rgb(P["gold"]), strip_a))
            draw.text((cx, HEIGHT-50), "JYOTESH AI",
                      font=get_font(40), anchor="mm",
                      fill=(*hex_rgb(P["gold"]), strip_a))

        # ── Composite onto background ─────────────────────────────────────
        frames.append(alpha_paste(bg, img))

    return frames

# ─── BODY FRAME ANIMATION ─────────────────────────────────────────────────────
def create_body_frames(script, body_idx, duration_s=4):
    sign = script["sign"]
    is_dark = sign in SIGN_DARK
    body = script.get("body", [])

    bg = make_background(sign, is_dark=False)  # body always light
    frames = []
    total = FPS * duration_s
    cx = WIDTH // 2

    for f in range(total):
        t = f / max(total - 1, 1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        # ── Maroon header strip ───────────────────────────────────────────
        hdr_t = ease_out_cubic(min(1.0, t / 0.10))
        # strip slides down from above
        strip_y = int(-160 * (1 - hdr_t))
        draw.rectangle([0, strip_y, WIDTH, 160 + strip_y],
                       fill=(*hex_rgb(P["maroon"]), 255))
        draw.text((cx, 55+strip_y),
                  f"{ZODIAC_CHAR.get(sign,'')}  {sign.upper()}",
                  font=get_font(40, bold=True), anchor="mm",
                  fill=(*hex_rgb(P["gold"]), 255))
        draw.text((cx, 115+strip_y), script["date"],
                  font=get_font(32), anchor="mm",
                  fill=(255,255,255,120))

        # ── Progress dots ─────────────────────────────────────────────────
        dot_a = int(200 * ease_out_cubic(min(1.0, t / 0.20)))
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

        # ── Body text: line-by-line reveal (0.15..0.80) ───────────────────
        text_prog = max(0.0, min(1.0, (t - 0.15) / 0.65))
        text_y = 360
        if body_idx < len(body):
            lines = textwrap.wrap(body[body_idx], width=18)
            for li, line in enumerate(lines):
                line_delay = li * 0.25
                line_t = max(0.0, min(1.0,
                    (text_prog - line_delay) / max(1.0 - line_delay, 0.001)))
                offset_y = int(40 * (1 - ease_out_cubic(line_t)))
                col_rgb = hex_rgb(P["charcoal"])
                animated_text(draw, cx, text_y + offset_y, line,
                               get_font(68, bold=True), col_rgb, line_t)
                text_y += 110

        # ── Vibe accent (slides up 0.65..0.90) ───────────────────────────
        vibe_prog = ease_out_cubic(max(0.0, min(1.0, (t-0.65)/0.25)))
        vibe_y = max(text_y + 60, 900)
        vibe_a = int(160 * vibe_prog)
        draw.line([(cx-200, vibe_y),(cx+200, vibe_y)],
                  fill=(*hex_rgb(P["maroon"]), vibe_a//4), width=1)
        draw.text((cx, vibe_y+40), "TODAY'S ENERGY",
                  font=get_font(40), anchor="mm",
                  fill=(*hex_rgb(P["gray"]), vibe_a))
        draw.text((cx, vibe_y+120), script.get("vibe_word", "POWERFUL"),
                  font=get_font(64, bold=True), anchor="mm",
                  fill=(*hex_rgb(P["saffron"]), vibe_a))

        # ── Bottom strip ──────────────────────────────────────────────────
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["charcoal"]), 240))
        draw.text((cx, HEIGHT-50), "JYOTESH AI",
                  font=get_font(40), anchor="mm",
                  fill=(*hex_rgb(P["gold"]), 220))

        frames.append(alpha_paste(bg, img))

    return frames

# ─── STATS FRAME ANIMATION ────────────────────────────────────────────────────
def create_stats_frames(script, duration_s=13):
    sign = script["sign"]
    bg = make_background(sign, is_dark=True)
    frames = []
    total = FPS * duration_s
    cx = WIDTH // 2

    stats = [
        ("\u2736  Lucky Number", str(script.get("lucky_number", 7))),
        ("\u2736  Power Color",  script.get("lucky_color", "Gold").title()),
        ("\u2736  Today's Vibe", script.get("vibe_word", "POWERFUL")),
        ("\u2736  Sign",         sign),
    ]

    for f in range(total):
        t = f / max(total - 1, 1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        # ── Header ───────────────────────────────────────────────────────
        h_t = ease_out_cubic(min(1.0, t / 0.10))
        h_a = int(255 * h_t)
        draw.text((cx, 120), "TODAY'S COSMIC NUMBERS",
                  font=get_font(46, bold=True), anchor="mm",
                  fill=(*hex_rgb(P["gold"]), h_a))
        draw.text((cx, 185), f"{sign.upper()}  {ZODIAC_CHAR.get(sign,'')}",
                  font=get_font(38), anchor="mm",
                  fill=(*hex_rgb(P["saffron"]), int(200*h_t)))
        if h_t > 0:
            draw_gold_divider(draw, cx, 230, w=700, alpha=int(200*h_t))

        # ── Stat cards (staggered slide-in from right) ────────────────────
        card_h = 160; card_w = 900
        card_x = (WIDTH - card_w) // 2
        card_y_base = 310

        for i, (label, value) in enumerate(stats):
            card_delay = 0.10 + i * 0.12
            card_t = ease_out_cubic(max(0.0, min(1.0, (t - card_delay) / 0.20)))
            slide_x = int(200 * (1 - card_t))   # slides from right
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
                draw.text((cx + slide_x, card_y+52), label,
                          font=get_font(36), anchor="mm",
                          fill=(*hex_rgb(P["gray"]), card_a//2))
                draw.text((cx + slide_x, card_y+115), value,
                          font=get_font(52, bold=True), anchor="mm",
                          fill=(*hex_rgb(P["ivory"]), card_a))

        # ── Reveal text (0.70..0.85) ──────────────────────────────────────
        rev_y_start = card_y_base + 4 * (card_h + 20) + 40
        rev_prog = max(0.0, min(1.0, (t - 0.70) / 0.15))
        if rev_prog > 0:
            draw_gold_divider(draw, cx, rev_y_start, w=700,
                              alpha=int(200*rev_prog))
            rev_y = rev_y_start + 60
            lines = textwrap.wrap(script.get("reveal",""), width=22)
            for li, line in enumerate(lines):
                line_delay = li * 0.15
                line_t = max(0.0, min(1.0,
                    (rev_prog - line_delay) / max(1.0-line_delay, 0.001)))
                offset_y = int(30*(1-ease_out_cubic(line_t)))
                animated_text(draw, cx, rev_y+offset_y, line,
                               get_font(50, bold=True),
                               hex_rgb(P["ivory"]), line_t)
                rev_y += 80

        # ── CTA pill (0.88..1.0) ──────────────────────────────────────────
        cta_t = ease_out_back(max(0.0, min(1.0, (t - 0.88) / 0.12)))
        cta_y = max(rev_y_start + 250, HEIGHT - 300)
        if cta_t > 0:
            cta_bg = (*hex_rgb(P["saffron"]), int(220*cta_t))
            draw_pill_badge(draw, cx, cta_y, "FOLLOW FOR DAILY UPDATES",
                            get_font(40, bold=True), cta_bg,
                            (*hex_rgb(P["charcoal"]), 255))

        # ── Bottom strip ──────────────────────────────────────────────────
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["maroon"]), 200))
        draw.text((cx, HEIGHT-50), "JYOTESH AI  •  Daily Vedic Astrology",
                  font=get_font(36), anchor="mm",
                  fill=(*hex_rgb(P["gold"]), 200))

        frames.append(alpha_paste(bg, img))

    return frames

# ─── TRANSITION: cross-dissolve between last frame of A and first of B ────────
def make_crossfade(frame_a, frame_b, n=10):
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
def generate_all_frames(script, frames_dir: Path):
    frames_dir.mkdir(parents=True, exist_ok=True)
    all_frames = []

    print("  Rendering hook slide …")
    hook_frames = create_hook_frames(script, duration_s=5)
    all_frames.extend(hook_frames)

    for i in range(len(script.get("body", []))):
        print(f"  Rendering body slide {i+1} …")
        body_frames = create_body_frames(script, i, duration_s=4)
        # cross-dissolve 10 frames between slides
        fade = make_crossfade(all_frames[-1], body_frames[0], n=10)
        all_frames.extend(fade)
        all_frames.extend(body_frames)

    print("  Rendering stats slide …")
    stats_frames = create_stats_frames(script, duration_s=13)
    fade = make_crossfade(all_frames[-1], stats_frames[0], n=10)
    all_frames.extend(fade)
    all_frames.extend(stats_frames)

    # Save
    for i, frame in enumerate(all_frames):
        path = frames_dir / f"frame_{i:05d}.jpg"
        frame.save(path, quality=94, optimize=True)

    print(f"\n  ✓ {len(all_frames)} frames saved to {frames_dir}")
    print(f"  Total duration: ~{len(all_frames)/FPS:.1f}s at {FPS} fps")
    print()
    print("  To encode to video (ffmpeg):")
    print(f"    ffmpeg -r {FPS} -i \"{frames_dir}/frame_%05d.jpg\" \\")
    print(f"           -vcodec libx264 -crf 18 -pix_fmt yuv420p output.mp4")
    return all_frames


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