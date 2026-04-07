#!/usr/bin/env python3
"""
Frame Generator v2 — Jyotesh AI Visual Identity
Fixes: proper Unicode zodiac symbols, readable text, JyoteshAI-style clean layout
pip install pillow requests
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap, os, math, random
from pathlib import Path

# ─── BRAND PALETTE ────────────────────────────────────────────────────────────
P = {
    "saffron":   "#FF6B00",
    "maroon":    "#7B1F3A",
    "gold":      "#F5C518",
    "ivory":     "#FDF8F0",
    "cream":     "#FFFBF2",
    "charcoal":  "#1A1A2E",
    "gray":      "#6B6B80",
    "green":     "#2D7A4F",
    "midnight":  "#0D0D1A",
}

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

WIDTH, HEIGHT = 1080, 1920

ZODIAC_EMOJIS = {
    "Aries":"♈","Taurus":"♉","Gemini":"♊","Cancer":"♋",
    "Leo":"♌","Virgo":"♍","Libra":"♎","Scorpio":"♏",
    "Sagittarius":"♐","Capricorn":"♑","Aquarius":"♒","Pisces":"♓"
}

SIGN_BG = {
    # (bg_color, text_color)
    "Aries":       ("#FDF8F0", "#7B1F3A"),
    "Taurus":      ("#FDF8F0", "#2D7A4F"),
    "Gemini":      ("#FDF8F0", "#1A1A2E"),
    "Cancer":      ("#FDF8F0", "#7B1F3A"),
    "Leo":         ("#FDF8F0", "#FF6B00"),
    "Virgo":       ("#FDF8F0", "#2D7A4F"),
    "Libra":       ("#FDF8F0", "#7B1F3A"),
    "Scorpio":     ("#1A1A2E", "#FF6B00"),
    "Sagittarius": ("#FDF8F0", "#FF6B00"),
    "Capricorn":   ("#1A1A2E", "#F5C518"),
    "Aquarius":    ("#1A1A2E", "#FF6B00"),
    "Pisces":      ("#FDF8F0", "#7B1F3A"),
}

def get_font(size, bold=False):
    """Try emoji-capable fonts first for symbol rendering."""
    candidates = [
        # Emoji-capable (needed for zodiac symbols)
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
        # Fallback
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Trebuchet MS Bold.ttf",
        "C:/Windows/Fonts/trebucbd.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

def get_text_font(size, bold=False):
    """Separate text font (not emoji)."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

def draw_gradient(draw, w, h, c1, c2, vertical=True):
    r1,g1,b1 = hex_rgb(c1)
    r2,g2,b2 = hex_rgb(c2)
    for i in range(h if vertical else w):
        t = i / (h if vertical else w)
        r,g,b = int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)
        if vertical:
            draw.line([(0,i),(w,i)], fill=(r,g,b))
        else:
            draw.line([(i,0),(i,h)], fill=(r,g,b))

def draw_mandala(draw, cx, cy, r=480, color=(123,31,58), alpha=10):
    """Subtle mandala grid — pure geometry, no emoji."""
    c = (*color, alpha)
    rings = [r*0.9, r*0.7, r*0.5, r*0.3, r*0.15]
    for ring in rings:
        draw.ellipse([cx-ring, cy-ring, cx+ring, cy+ring], outline=c, width=1)
    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg)
        x1 = cx + r*0.15*math.cos(angle)
        y1 = cy + r*0.15*math.sin(angle)
        x2 = cx + r*0.9*math.cos(angle)
        y2 = cy + r*0.9*math.sin(angle)
        draw.line([(x1,y1),(x2,y2)], fill=c, width=1)
    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg)
        pr = r * 0.55
        px = cx + pr*math.cos(angle)
        py = cy + pr*math.sin(angle)
        pr2 = r * 0.07
        draw.ellipse([px-pr2, py-pr2, px+pr2, py+pr2], outline=c, width=1)

def draw_stars(draw, w, h, count=180):
    for _ in range(count):
        x = random.randint(0, w)
        y = random.randint(0, h)
        sz = random.choice([1,1,1,2,2,3])
        alpha = random.randint(60, 180)
        col = random.choice([
            (255,255,255,alpha),
            (245,197,24,alpha),
            (253,248,240,alpha),
        ])
        draw.ellipse([x,y,x+sz,y+sz], fill=col)

def draw_rounded_rect(draw, x0, y0, x1, y1, radius, fill=None, outline=None, width=2):
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def draw_gold_divider(draw, cx, y, w=800):
    gold = (*hex_rgb(P["gold"]), 120)
    draw.line([(cx-w//2, y), (cx+w//2, y)], fill=gold, width=2)
    d = 12
    draw.polygon([(cx,y-d),(cx+d,y),(cx,y+d),(cx-d,y)], fill=(*hex_rgb(P["gold"]),160))

def draw_pill_badge(draw, cx, cy, text, font, bg, fg):
    bbox = font.getbbox(text)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    px, py = 40, 20
    draw_rounded_rect(draw, cx-tw//2-px, cy-th//2-py,
                      cx+tw//2+px, cy+th//2+py, 40, fill=bg)
    draw.text((cx, cy), text, font=font, anchor="mm", fill=fg)


def create_hook_frame(script):
    sign = script["sign"]
    bg, tc = SIGN_BG.get(sign, ("#FDF8F0","#1A1A2E"))
    is_dark = bg == "#1A1A2E"

    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")

    # Gradient: ivory → cream (or charcoal → midnight for dark signs)
    if is_dark:
        draw_gradient(draw, WIDTH, HEIGHT, "#1A1A2E", "#0D0D1A")
    else:
        draw_gradient(draw, WIDTH, HEIGHT, "#FDF8F0", "#FFFBF2")

    # Mandala watermark
    mc = hex_rgb(P["maroon"]) if not is_dark else hex_rgb(P["saffron"])
    draw_mandala(draw, WIDTH//2, HEIGHT//2, r=500, color=mc, alpha=8)

    if is_dark:
        draw_stars(draw, WIDTH, HEIGHT, 200)

    cx = WIDTH // 2

    # ─ Brand header ─
    brand_font = get_text_font(36)
    brand_color = hex_rgb(P["saffron"]) + (200,) if not is_dark else hex_rgb(P["gold"]) + (200,)
    draw.text((cx, 80), "JYOTESH AI", font=brand_font, anchor="mm", fill=brand_color)

    date_font = get_text_font(34)
    date_color = hex_rgb(P["gray"]) + (200,)
    draw.text((cx, 130), script["date"], font=date_font, anchor="mm", fill=date_color)

    # ─ Thin saffron line ─
    draw.rectangle([cx-60, 155, cx+60, 157], fill=(*hex_rgb(P["saffron"]), 180))

    # ─ Zodiac symbol circle ─
    symbol_y = 520
    circle_r = 240
    # Outer glow rings
    for r in [circle_r+80, circle_r+50, circle_r+20]:
        a = int(30 * (1 - (r-circle_r)/80))
        draw.ellipse([cx-r, symbol_y-r, cx+r, symbol_y+r],
                     outline=(*hex_rgb(P["saffron"]), a), width=1)
    # Main circle (ivory on light, maroon-tinted on dark)
    if is_dark:
        circle_fill = (*hex_rgb(P["maroon"]), 180)
    else:
        circle_fill = (*hex_rgb("#F0E8DC"), 255)
    draw.ellipse([cx-circle_r, symbol_y-circle_r, cx+circle_r, symbol_y+circle_r],
                 fill=circle_fill,
                 outline=(*hex_rgb(P["maroon"]), 80), width=2)

    # Zodiac Unicode symbol — needs emoji/noto font for correct glyph
    emoji_font = get_font(220)
    symbol = ZODIAC_EMOJIS.get(sign, "★")
    sym_color = hex_rgb(tc) + (240,)
    draw.text((cx, symbol_y), symbol, font=emoji_font, anchor="mm", fill=sym_color)

    # ─ Sign name badge ─
    name_y = symbol_y + circle_r + 80
    name_font = get_text_font(72, bold=True)
    badge_bg = (*hex_rgb(P["saffron"]), 220) if not is_dark else (*hex_rgb(P["gold"]), 220)
    badge_fg = hex_rgb(P["charcoal"]) + (255,)
    draw_pill_badge(draw, cx, name_y, sign.upper(), name_font, badge_bg, badge_fg)

    # ─ Gold divider ─
    div_y = name_y + 90
    draw_gold_divider(draw, cx, div_y)

    # ─ Hook text ─
    hook_y = div_y + 80
    hook_font = get_text_font(60, bold=True)
    hook_color = hex_rgb(P["charcoal"]) + (255,) if not is_dark else hex_rgb(P["ivory"]) + (255,)
    lines = textwrap.wrap(script["hook"], width=20)
    for line in lines:
        draw.text((cx, hook_y), line, font=hook_font, anchor="mm", fill=hook_color)
        hook_y += 90

    # ─ Bottom branding strip ─
    strip_h = 100
    draw.rectangle([0, HEIGHT-strip_h, WIDTH, HEIGHT],
                   fill=(*hex_rgb(P["charcoal"]), 240))
    # SVG-style star ornaments (no emoji — custom drawn)
    star_col = (*hex_rgb(P["gold"]), 180)
    for sx in [cx-180, cx+180]:
        draw.polygon([(sx,HEIGHT-55),(sx+8,HEIGHT-40),(sx+24,HEIGHT-38),
                      (sx+12,HEIGHT-28),(sx+16,HEIGHT-14),(sx,HEIGHT-22),
                      (sx-16,HEIGHT-14),(sx-12,HEIGHT-28),(sx-24,HEIGHT-38),(sx-8,HEIGHT-40)],
                     fill=star_col)
    brand_b_font = get_text_font(40)
    draw.text((cx, HEIGHT-50), "JYOTESH AI", font=brand_b_font, anchor="mm",
              fill=(*hex_rgb(P["gold"]), 220))

    return img.convert("RGB")


def create_body_frame(script, body_idx):
    sign = script["sign"]
    body = script.get("body", [])
    is_dark = SIGN_BG.get(sign, ("#FDF8F0",""))[0] == "#1A1A2E"

    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")

    draw_gradient(draw, WIDTH, HEIGHT, "#FFFBF2", "#FDF8F0")
    mc = hex_rgb(P["maroon"])
    draw_mandala(draw, WIDTH//2, HEIGHT//2, r=500, color=mc, alpha=6)

    cx = WIDTH // 2

    # ─ Maroon header strip ─
    draw.rectangle([0, 0, WIDTH, 160], fill=(*hex_rgb(P["maroon"]), 255))
    sign_font = get_text_font(40, bold=True)
    draw.text((cx, 55), f"{ZODIAC_EMOJIS.get(sign,'')}  {sign.upper()}", font=sign_font,
              anchor="mm", fill=(*hex_rgb(P["gold"]), 255))
    draw.text((cx, 115), script["date"], font=get_text_font(32),
              anchor="mm", fill=(255,255,255,120))

    # ─ Progress dots ─
    dot_y = 240
    total = len(body)
    dot_spacing = 40
    start_x = cx - (total * dot_spacing) // 2
    for i in range(total):
        dx = start_x + i * dot_spacing + 20
        if i == body_idx:
            draw.rounded_rectangle([dx-20, dot_y-8, dx+20, dot_y+8], 8,
                                   fill=(*hex_rgb(P["saffron"]), 255))
        else:
            draw.ellipse([dx-8, dot_y-8, dx+8, dot_y+8],
                         fill=(*hex_rgb(P["gray"]), 80))

    # ─ Body text ─
    text_y = 360
    if body_idx < len(body):
        body_font = get_text_font(68, bold=True)
        lines = textwrap.wrap(body[body_idx], width=18)
        for line in lines:
            draw.text((cx, text_y), line, font=body_font, anchor="mm",
                      fill=(*hex_rgb(P["charcoal"]), 255))
            text_y += 110

    # ─ Vibe word accent ─
    vibe_y = max(text_y + 60, 900)
    draw.line([(cx-200, vibe_y), (cx+200, vibe_y)], fill=(*hex_rgb(P["maroon"]), 40), width=1)
    vibe_y += 40
    vf = get_text_font(40)
    draw.text((cx, vibe_y), "TODAY'S ENERGY", font=vf, anchor="mm",
              fill=(*hex_rgb(P["gray"]), 160))
    vf2 = get_text_font(64, bold=True)
    draw.text((cx, vibe_y+80), script.get("vibe_word","POWERFUL"),
              font=vf2, anchor="mm", fill=(*hex_rgb(P["saffron"]), 255))

    # ─ Bottom strip ─
    draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT], fill=(*hex_rgb(P["charcoal"]), 240))
    draw.text((cx, HEIGHT-50), "JYOTESH AI", font=get_text_font(40),
              anchor="mm", fill=(*hex_rgb(P["gold"]), 220))

    return img.convert("RGB")


def create_stats_frame(script):
    sign = script["sign"]
    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")

    draw_gradient(draw, WIDTH, HEIGHT, "#1A1A2E", "#0D0D1A")
    draw_stars(draw, WIDTH, HEIGHT, 250)
    draw_mandala(draw, WIDTH//2, HEIGHT//2, r=500, color=hex_rgb(P["gold"]), alpha=6)

    cx = WIDTH // 2

    # Header
    header_font = get_text_font(46, bold=True)
    draw.text((cx, 120), "TODAY'S COSMIC NUMBERS", font=header_font,
              anchor="mm", fill=(*hex_rgb(P["gold"]), 255))

    sign_f = get_text_font(38)
    draw.text((cx, 185), f"{sign.upper()}  {ZODIAC_EMOJIS.get(sign,'')}",
              font=sign_f, anchor="mm", fill=(*hex_rgb(P["saffron"]), 200))

    draw_gold_divider(draw, cx, 230, w=700)

    # Stat cards
    stats = [
        ("✦  Lucky Number", str(script.get("lucky_number", 7))),
        ("✦  Power Color", script.get("lucky_color", "Gold").title()),
        ("✦  Today's Vibe", script.get("vibe_word", "POWERFUL")),
        ("✦  Sign", sign),
    ]

    card_y = 310
    card_h = 160
    card_w = 900
    card_x = (WIDTH - card_w) // 2

    for label, value in stats:
        draw_rounded_rect(draw, card_x, card_y, card_x+card_w, card_y+card_h,
                          20, fill=(*hex_rgb("#FFFFFF"), 6),
                          outline=(*hex_rgb(P["gold"]), 30), width=1)
        lf = get_text_font(36)
        vf = get_text_font(52, bold=True)
        draw.text((cx, card_y+52), label, font=lf, anchor="mm",
                  fill=(*hex_rgb(P["gray"]), 180))
        draw.text((cx, card_y+115), value, font=vf, anchor="mm",
                  fill=(*hex_rgb(P["ivory"]), 255))
        card_y += card_h + 20

    # Reveal text
    rev_y = card_y + 40
    draw_gold_divider(draw, cx, rev_y, w=700)
    rev_font = get_text_font(50, bold=True)
    lines = textwrap.wrap(script.get("reveal",""), width=22)
    rev_y += 60
    for line in lines:
        draw.text((cx, rev_y), line, font=rev_font, anchor="mm",
                  fill=(*hex_rgb(P["ivory"]), 240))
        rev_y += 80

    # CTA
    cta_y = max(rev_y + 60, HEIGHT - 300)
    cta_bg = (*hex_rgb(P["saffron"]), 220)
    draw_pill_badge(draw, cx, cta_y, "FOLLOW FOR DAILY UPDATES", get_text_font(40, bold=True),
                    cta_bg, hex_rgb(P["charcoal"])+(255,))

    # Bottom
    draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT], fill=(*hex_rgb(P["maroon"]), 200))
    draw.text((cx, HEIGHT-50), "JYOTESH AI  •  Daily Vedic Astrology",
              font=get_text_font(36), anchor="mm",
              fill=(*hex_rgb(P["gold"]), 200))

    return img.convert("RGB")


def generate_all_frames(script, output_dir="reels_output"):
    out = Path(output_dir) / script["sign"].lower()
    out.mkdir(parents=True, exist_ok=True)

    frames = []

    # Hook frame
    f0 = out / "frame_00_hook.jpg"
    create_hook_frame(script).save(f0, quality=96)
    frames.append(f0)
    print(f"  ✓ Hook frame: {f0}")

    # Body frames
    for i in range(len(script.get("body", []))):
        fi = out / f"frame_{i+1:02d}_body.jpg"
        create_body_frame(script, i).save(fi, quality=96)
        frames.append(fi)
        print(f"  ✓ Body frame {i+1}: {fi}")

    # Stats frame
    fs = out / f"frame_{len(frames):02d}_stats.jpg"
    create_stats_frame(script).save(fs, quality=96)
    frames.append(fs)
    print(f"  ✓ Stats frame: {fs}")

    return frames


# ─── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_script = {
        "sign": "Libra",
        "date": "April 07, 2026",
        "hook": "The stars have a MAJOR message for Libra today",
        "body": [
            "Venus is rewriting your love story.",
            "An unexpected door is about to open.",
            "Trust the timing of the universe.",
            "Your energy attracts abundance now.",
            "Someone is watching your rise.",
        ],
        "reveal": "The cosmos say: trust your instincts, Libra. Big changes are near.",
        "cta": "Follow for daily Libra updates! Drop your sign below",
        "lucky_number": 7,
        "lucky_color": "deep gold",
        "vibe_word": "TRANSFORMATIVE",
    }
    print("\n🔮 Generating Jyotesh AI frames for:", test_script["sign"])
    frames = generate_all_frames(test_script, "test_output")
    print(f"\n✅ {len(frames)} frames saved to test_output/{test_script['sign'].lower()}/")