#!/usr/bin/env python3
"""
fun_genre_frame_generator.py
─────────────────────────────
Frame renderer for the three "fun genre" reel types:
  • name_initials  — giant letter hero badge + personality insight cards
  • lucky_month    — month name hero + seasonal energy cards
  • compatibility  — two zodiac symbols side-by-side + chemistry cards

Layout (differs from frame_generator.py):
  Slide 1 — Genre Hook   (6 s) : hero badge (letter / month / sign pair) + hook text
  Slide 2 — Insight Card (6 s) : 3 stacked insight bullets with animated reveal
  Slide 3 — Extra Info   (6 s) : genre-specific key facts (score, power period, etc.)
  Slide 4 — Stats / CTA  (8 s) : lucky number + color + vibe + CTA pill

All shared drawing utilities (fonts, gradients, particles, badges) are
imported directly from frame_generator to avoid duplication.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# ── Shared utilities from the existing frame generator ────────────────────────
from frame_generator import (
    P, WIDTH, HEIGHT, FPS,
    hex_rgb, ease_out_cubic, ease_out_back, ease_in_out_sine, lerp,
    get_text_font, get_symbol_font, smart_font, draw_text, measure_text,
    draw_gradient, draw_mandala, draw_gold_divider, draw_pill_badge,
    draw_star_ornament, draw_particles, draw_category_badge, draw_lang_badge,
    make_background, _blend_colors, alpha_paste, animated_text,
    smart_wrap, make_crossfade, _save_frames,
    ZODIAC_CHAR, SIGN_DARK,
)

from fun_genre_categories import FUN_GENRE_VISUAL, GENRE_DISPLAY

# ─── ZODIAC ELEMENT MAP (for compatibility sign colours) ─────────────────────
_ELEM_COLOR = {
    "Aries":       P["saffron"],  "Leo":         P["saffron"],  "Sagittarius": P["saffron"],
    "Taurus":      P["green"],    "Virgo":        P["green"],    "Capricorn":   P["green"],
    "Gemini":      P["gold"],     "Libra":        P["gold"],     "Aquarius":    P["gold"],
    "Cancer":      P["maroon"],   "Scorpio":       P["maroon"],  "Pisces":      P["maroon"],
}


# ─── BACKGROUND ───────────────────────────────────────────────────────────────
def _make_genre_bg(genre: str, dark: bool = False) -> Image.Image:
    cv = FUN_GENRE_VISUAL.get(genre, {})
    tint = cv.get("tint", P["charcoal"])
    img  = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")
    if dark:
        c1 = _blend_colors("#1A1A2E", tint, 0.6)
        c2 = _blend_colors("#0D0D1A", tint, 0.4)
    else:
        c1 = _blend_colors("#1A1A2E", tint, 0.45)
        c2 = _blend_colors("#0D0D1A", tint, 0.25)
    draw_gradient(draw, WIDTH, HEIGHT, c1, c2)
    # subtle mandala
    draw_mandala(draw, WIDTH // 2, HEIGHT // 2, r=500,
                 color=hex_rgb(cv.get("accent", P["saffron"])), alpha=6)
    return img


# ─── HEADER / FOOTER STRIPS ───────────────────────────────────────────────────
def _draw_header(draw, font_brand, font_badge, genre: str, t: float):
    cv       = FUN_GENRE_VISUAL.get(genre, {})
    accent   = cv.get("accent", P["saffron"])
    label    = GENRE_DISPLAY.get(genre, genre.upper())
    hdr_t    = ease_out_cubic(min(1.0, t / 0.10))
    brand_a  = int(200 * hdr_t)

    # Brand name top-centre
    draw_text(draw, (WIDTH // 2, 80), "JyoteshAI",
              font=font_brand, anchor="mm",
              fill=(*hex_rgb(accent), brand_a))

    # Thin accent underline
    if hdr_t > 0:
        draw.rectangle([WIDTH // 2 - 60, 155, WIDTH // 2 + 60, 157],
                       fill=(*hex_rgb(accent), int(180 * hdr_t)))

    # Genre badge top-right
    if hdr_t > 0:
        f_cat = smart_font(label, 28, bold=True)
        draw_category_badge(draw, f_cat, label, accent,
                            cv.get("badge_fg", "#FFFFFF"), alpha=hdr_t)


def _draw_footer(draw, font_bottom, t: float):
    strip_a = int(240 * ease_out_cubic(min(1.0, t / 0.10)))
    draw.rectangle([0, HEIGHT - 100, WIDTH, HEIGHT],
                   fill=(*hex_rgb(P["charcoal"]), strip_a))
    if strip_a > 0:
        cx = WIDTH // 2
        for sx in [cx - 180, cx + 180]:
            draw_star_ornament(draw, sx, HEIGHT - 50,
                               (*hex_rgb(P["gold"]), strip_a))
        draw_text(draw, (cx, HEIGHT - 50), "JyoteshAI",
                  font=font_bottom, anchor="mm",
                  fill=(*hex_rgb(P["gold"]), strip_a))


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — HOOK
# ═══════════════════════════════════════════════════════════════════════════════

def _draw_hero_name_initials(draw, script: dict, cx: int, t: float, cv: dict):
    """Giant letter(s) in a glowing circle, like the zodiac symbol."""
    letters  = script.get("letters", [script.get("subject", "A")])
    hero_str = " & ".join(letters)
    accent   = cv.get("accent", P["saffron"])
    hero_bg  = cv.get("hero_bg", "#2D1B4E")

    circ_t  = ease_out_back(max(0.0, min(1.0, (t - 0.08) / 0.27)))
    sym_y   = 520
    circle_r = int(220 * circ_t)

    if circle_r > 0:
        for gr in [circle_r + 80, circle_r + 50, circle_r + 20]:
            ga = int(30 * (1 - (gr - circle_r) / 80) * circ_t)
            draw.ellipse([cx - gr, sym_y - gr, cx + gr, sym_y + gr],
                         outline=(*hex_rgb(accent), ga), width=1)
        draw.ellipse([cx - circle_r, sym_y - circle_r,
                      cx + circle_r, sym_y + circle_r],
                     fill=(*hex_rgb(hero_bg), 255),
                     outline=(*hex_rgb(accent), 80), width=2)

        # Letter(s) sized to fit
        font_size = 130 if len(hero_str) <= 3 else 80
        f_hero = get_text_font(font_size, bold=True)
        sym_a  = int(240 * circ_t)
        draw_text(draw, (cx, sym_y), hero_str, font=f_hero, anchor="mm",
                  fill=(*hex_rgb(cv.get("hero_fg", accent)), sym_a))


def _draw_hero_lucky_month(draw, script: dict, cx: int, t: float, cv: dict):
    """Month name(s) in an arched pill badge."""
    months  = script.get("months", [script.get("subject", "May")])
    label   = " & ".join(m[:3].upper() for m in months)
    accent  = cv.get("accent", P["saffron"])
    hero_bg = cv.get("hero_bg", "#0F3D2A")

    circ_t   = ease_out_back(max(0.0, min(1.0, (t - 0.08) / 0.27)))
    sym_y    = 520
    circle_r = int(220 * circ_t)

    if circle_r > 0:
        for gr in [circle_r + 80, circle_r + 50, circle_r + 20]:
            ga = int(30 * (1 - (gr - circle_r) / 80) * circ_t)
            draw.ellipse([cx - gr, sym_y - gr, cx + gr, sym_y + gr],
                         outline=(*hex_rgb(accent), ga), width=1)
        draw.ellipse([cx - circle_r, sym_y - circle_r,
                      cx + circle_r, sym_y + circle_r],
                     fill=(*hex_rgb(hero_bg), 255),
                     outline=(*hex_rgb(accent), 80), width=2)

        font_size = 80 if len(label) <= 7 else 60
        f_hero = get_text_font(font_size, bold=True)
        sym_a  = int(240 * circ_t)
        draw_text(draw, (cx, sym_y), label, font=f_hero, anchor="mm",
                  fill=(*hex_rgb(cv.get("hero_fg", accent)), sym_a))


def _draw_hero_compatibility(draw, script: dict, cx: int, t: float, cv: dict):
    """Two zodiac symbols side by side with a ✦ between them."""
    sign_a  = script.get("sign_a", "Aries")
    sign_b  = script.get("sign_b", "Scorpio")
    sym_a_s = ZODIAC_CHAR.get(sign_a, "★")
    sym_b_s = ZODIAC_CHAR.get(sign_b, "★")
    accent  = cv.get("accent", P["saffron"])

    circ_t   = ease_out_back(max(0.0, min(1.0, (t - 0.08) / 0.27)))
    sym_y    = 520
    circle_r = int(200 * circ_t)
    spacing  = 320

    for offset, sym, sign in [(-spacing // 2, sym_a_s, sign_a),
                               (spacing // 2, sym_b_s, sign_b)]:
        ox = cx + offset
        col = _elem_color(sign, accent)
        if circle_r > 0:
            for gr in [circle_r + 50, circle_r + 25]:
                ga = int(20 * (1 - (gr - circle_r) / 50) * circ_t)
                draw.ellipse([ox - gr, sym_y - gr, ox + gr, sym_y + gr],
                             outline=(*hex_rgb(col), ga), width=1)
            draw.ellipse([ox - circle_r, sym_y - circle_r,
                          ox + circle_r, sym_y + circle_r],
                         fill=(*hex_rgb(_blend_colors("#1A1A2E", col, 0.25)), 255),
                         outline=(*hex_rgb(col), 80), width=2)

            f_sym = get_symbol_font(140)
            sym_alpha = int(230 * circ_t)
            draw_text(draw, (ox, sym_y), sym,
                      font=f_sym, anchor="mm",
                      fill=(*hex_rgb(col), sym_alpha))

    # ✦ between circles
    if circ_t > 0.5:
        mid_a = int(255 * (circ_t - 0.5) / 0.5)
        f_plus = get_text_font(52, bold=True)
        draw_text(draw, (cx, sym_y), "✦", font=f_plus, anchor="mm",
                  fill=(*hex_rgb(accent), mid_a))

    # Sign name pills below circles
    badge_t  = ease_out_cubic(max(0.0, min(1.0, (t - 0.35) / 0.15)))
    badge_y  = sym_y + 280
    f_name   = get_text_font(44, bold=True)
    for offset, sign in [(-spacing // 2, sign_a), (spacing // 2, sign_b)]:
        ox  = cx + offset
        col = _elem_color(sign, accent)
        bg  = (*hex_rgb(col), int(210 * badge_t))
        fg  = (*hex_rgb("#FFFFFF"), 255)
        if badge_t > 0:
            draw_pill_badge(draw, ox, badge_y + int(40*(1-badge_t)),
                            sign.upper(), f_name, bg, fg, radius=30)


def _elem_color(sign: str, fallback: str) -> str:
    return _ELEM_COLOR.get(sign, fallback)


def create_genre_hook_frames(script: dict, duration_s: int = 6) -> list:
    genre    = script.get("genre", "compatibility")
    lang     = script.get("lang", "en")
    cv       = FUN_GENRE_VISUAL.get(genre, {})
    accent   = cv.get("accent", P["saffron"])
    subject  = script.get("subject", "")

    bg     = _make_genre_bg(genre, dark=False)
    frames = []
    total  = FPS * duration_s
    cx     = WIDTH // 2

    f_brand  = get_text_font(36)
    f_hook   = get_text_font(50, bold=True)
    f_sub    = get_text_font(42, bold=True)
    f_badge  = get_text_font(30, bold=True)
    f_bottom = get_text_font(38)

    particle_col = hex_rgb(accent)

    for f in range(total):
        t   = f / max(total - 1, 1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        drw = ImageDraw.Draw(img, "RGBA")

        draw_particles(drw, t, particle_col, base_alpha=20)
        _draw_header(drw, f_brand, f_badge, genre, t)

        # ── Hero badge ──────────────────────────────────────────────────
        if genre == "name_initials":
            _draw_hero_name_initials(drw, script, cx, t, cv)
        elif genre == "lucky_month":
            _draw_hero_lucky_month(drw, script, cx, t, cv)
        else:
            _draw_hero_compatibility(drw, script, cx, t, cv)

        # ── Subject label pill below hero ────────────────────────────────
        badge_t = ease_out_cubic(max(0.0, min(1.0, (t - 0.30) / 0.15)))
        sub_y   = 870 if genre == "compatibility" else 800
        bg_pill = (*hex_rgb(accent), int(220 * badge_t))
        fg_pill = (*hex_rgb(cv.get("badge_fg", "#1A1A2E")), 255)
        if badge_t > 0:
            sub_text = script.get("subject", subject).upper()
            draw_pill_badge(drw, cx, sub_y + int(40*(1-badge_t)),
                            sub_text, f_sub, bg_pill, fg_pill, radius=40)

        # ── Gold divider ─────────────────────────────────────────────────
        div_y = sub_y + 80
        div_t = ease_out_cubic(max(0.0, min(1.0, (t - 0.42) / 0.08)))
        if div_t > 0:
            draw_gold_divider(drw, cx, div_y, alpha=int(120 * div_t),
                              color=hex_rgb(accent))

        # ── Hook text ────────────────────────────────────────────────────
        hook_s, hook_e = 0.45, 0.75
        hook_t = max(0.0, min(1.0, (t - hook_s) / (hook_e - hook_s)))
        if hook_t > 0 or t >= hook_e:
            display_t = 1.0 if t >= hook_e else hook_t
            hook_y    = div_y + 80
            lines      = smart_wrap(script.get("hook", ""), 22, 16)
            col_rgb    = hex_rgb(P["ivory"])
            for li, line in enumerate(lines):
                lf = get_text_font(50, bold=True)
                ld = li * 0.18
                lt = max(0.0, min(1.0, (display_t - ld) / max(1.0 - ld, 0.001)))
                oy = int(60 * (1 - ease_out_cubic(lt)))
                animated_text(drw, cx, hook_y + oy, line, lf, col_rgb, lt)
                hook_y += 88

        _draw_footer(drw, f_bottom, t)
        frames.append(alpha_paste(bg, img))
    return frames


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — INSIGHT CARDS
# ═══════════════════════════════════════════════════════════════════════════════

def create_genre_insight_frames(script: dict, duration_s: int = 6) -> list:
    genre    = script.get("genre", "compatibility")
    cv       = FUN_GENRE_VISUAL.get(genre, {})
    accent   = cv.get("accent", P["saffron"])
    subject  = script.get("subject", "")
    insights = script.get("insights", [])

    bg     = _make_genre_bg(genre, dark=True)
    frames = []
    total  = FPS * duration_s
    cx     = WIDTH // 2

    f_brand   = get_text_font(36)
    f_header  = get_text_font(42, bold=True)
    f_num     = get_text_font(52, bold=True)
    f_text    = get_text_font(44)
    f_bottom  = get_text_font(38)
    f_badge   = get_text_font(28, bold=True)

    particle_col = hex_rgb(accent)
    label    = GENRE_DISPLAY.get(genre, genre.upper())

    for f in range(total):
        t   = f / max(total - 1, 1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        drw = ImageDraw.Draw(img, "RGBA")

        draw_particles(drw, t, particle_col, base_alpha=18)

        # Header strip
        hdr_t  = ease_out_cubic(min(1.0, t / 0.08))
        strip_y = int(-160 * (1 - hdr_t))
        hdr_bg  = (*hex_rgb(_blend_colors("#1A1A2E", cv.get("hero_bg", accent), 0.6)), 255)
        drw.rectangle([0, strip_y, WIDTH, 160 + strip_y], fill=hdr_bg)

        brand_a = int(220 * hdr_t)
        draw_text(drw, (cx, 55 + strip_y), "JyoteshAI — " + label,
                  font=f_header, anchor="mm",
                  fill=(*hex_rgb(accent), brand_a))
        draw_text(drw, (cx, 115 + strip_y), subject.upper(),
                  font=get_text_font(32), anchor="mm",
                  fill=(*hex_rgb(P["ivory"]), int(170 * hdr_t)))

        # Stacked insight bullets
        y = 220
        show_n = min(5, len(insights))
        for i in range(show_n):
            line    = insights[i]
            delay   = 0.08 + i * 0.13
            card_t  = ease_out_cubic(max(0.0, min(1.0, (t - delay) / 0.18)))
            if t >= delay + 0.25:
                card_t = 1.0
            card_a  = int(255 * card_t)
            slide_x = int(120 * (1 - card_t))

            if card_a > 0:
                # Number circle
                num_r = 34
                nx = 80 + slide_x
                ny = y + 28
                drw.ellipse([nx - num_r, ny - num_r, nx + num_r, ny + num_r],
                            fill=(*hex_rgb(accent), card_a))
                draw_text(drw, (nx, ny), str(i + 1),
                          font=f_num, anchor="mm",
                          fill=(*hex_rgb(cv.get("badge_fg", "#1A1A2E")), card_a))

                # Card background
                card_h = max(84, len(smart_wrap(line, 26)) * 60 + 24)
                card_x = 140
                drw.rounded_rectangle(
                    [card_x + slide_x, y,
                     WIDTH - 40 + slide_x, y + card_h],
                    radius=18,
                    fill=(*hex_rgb("#FFFFFF"), min(card_a // 14, 18)),
                    outline=(*hex_rgb(accent), min(card_a // 3, 70)),
                    width=1)

                # Insight text
                wrapped = smart_wrap(line, 26)
                ty = y + 20
                for wl in wrapped:
                    lf = get_text_font(44)
                    draw_text(drw, (card_x + 20 + slide_x, ty), wl,
                              font=lf, anchor="lm",
                              fill=(*hex_rgb(P["ivory"]), card_a))
                    ty += 58
                y += card_h + 24

        _draw_footer(drw, f_bottom, t)
        frames.append(alpha_paste(bg, img))
    return frames


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — GENRE EXTRA INFO
# ═══════════════════════════════════════════════════════════════════════════════

def _extra_blocks(script: dict) -> list[tuple[str, str]]:
    """Return (label, value) pairs for genre-specific highlight blocks."""
    genre = script.get("genre", "")
    blocks = []
    if genre == "name_initials":
        if script.get("personality_trait"):
            blocks.append(("THEIR ENERGY", script["personality_trait"]))
        if script.get("lucky_pairing"):
            blocks.append(("BEST NAME MATCH", script["lucky_pairing"]))
    elif genre == "lucky_month":
        if script.get("power_period"):
            blocks.append(("POWER PERIOD", script["power_period"]))
        if script.get("cosmic_message"):
            blocks.append(("COSMIC MESSAGE", script["cosmic_message"]))
    elif genre == "compatibility":
        if script.get("compatibility_score"):
            blocks.append(("COMPATIBILITY", script["compatibility_score"]))
        if script.get("chemistry"):
            blocks.append(("CHEMISTRY", script["chemistry"]))
        if script.get("verdict"):
            blocks.append(("THE VERDICT", script["verdict"]))
    return blocks


def create_genre_extra_frames(script: dict, duration_s: int = 6) -> list:
    genre   = script.get("genre", "compatibility")
    cv      = FUN_GENRE_VISUAL.get(genre, {})
    accent  = cv.get("accent", P["saffron"])
    blocks  = _extra_blocks(script)

    if not blocks:
        return []

    bg     = _make_genre_bg(genre, dark=False)
    frames = []
    total  = FPS * duration_s
    cx     = WIDTH // 2

    f_brand  = get_text_font(36)
    f_bottom = get_text_font(38)
    f_badge  = get_text_font(28, bold=True)

    particle_col = hex_rgb(accent)

    for f in range(total):
        t   = f / max(total - 1, 1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        drw = ImageDraw.Draw(img, "RGBA")

        draw_particles(drw, t, particle_col, base_alpha=25)
        _draw_header(drw, f_brand, f_badge, genre, t)

        # Big accent top bar
        h_t   = ease_out_cubic(min(1.0, t / 0.12))
        bar_h = int(200 * h_t)
        drw.rectangle([0, 0, WIDTH, bar_h],
                      fill=(*hex_rgb(accent), int(230 * h_t)))
        if h_t > 0:
            label_text = GENRE_DISPLAY.get(genre, genre.upper())
            f_lbl = get_text_font(44, bold=True)
            draw_text(drw, (cx, 85), label_text, font=f_lbl, anchor="mm",
                      fill=(*hex_rgb(cv.get("badge_fg", "#FFFFFF")), int(255 * h_t)))
            draw_text(drw, (cx, 145), script.get("subject", "").upper(),
                      font=get_text_font(32), anchor="mm",
                      fill=(*hex_rgb("#FFFFFF"), int(180 * h_t)))

        # Extra blocks
        y = 260
        for i, (label, content) in enumerate(blocks):
            bdelay = 0.12 + i * 0.18
            block_t = ease_out_cubic(max(0.0, min(1.0, (t - bdelay) / 0.20)))
            if t >= bdelay + 0.28:
                block_t = 1.0
            block_a = int(255 * block_t)
            slide_o = int(80 * (1 - block_t))

            if block_a > 0:
                lbl_f  = get_text_font(30, bold=True)
                lw, lh = measure_text(label, lbl_f)
                px, py = 28, 14
                drw.rounded_rectangle(
                    [cx - lw//2 - px + slide_o, y - py,
                     cx + lw//2 + px + slide_o, y + lh + py],
                    radius=24,
                    fill=(*hex_rgb(accent), min(block_a, 180)))
                draw_text(drw, (cx + slide_o, y + lh // 2 + 4), label,
                          font=lbl_f, anchor="mm",
                          fill=(*hex_rgb(cv.get("badge_fg", "#FFFFFF")), block_a))
                y += lh + 44

                # Content
                c_lines = smart_wrap(content, 26)
                for li, line in enumerate(c_lines):
                    lf = get_text_font(46)
                    ld = li * 0.08
                    lt = max(0.0, min(1.0, (block_t - ld) / max(1.0 - ld, 0.001)))
                    oy = int(60 * (1 - ease_out_cubic(lt)))
                    animated_text(drw, cx + slide_o, y + oy, line, lf,
                                  hex_rgb(P["ivory"]), lt)
                    y += 70
                y += 60

                if i < len(blocks) - 1:
                    draw_gold_divider(drw, cx, y - 20, w=600,
                                      alpha=int(80 * block_t),
                                      color=hex_rgb(accent))

        _draw_footer(drw, f_bottom, t)
        frames.append(alpha_paste(bg, img))
    return frames


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — STATS / CTA
# ═══════════════════════════════════════════════════════════════════════════════

def create_genre_stats_frames(script: dict, duration_s: int = 8) -> list:
    genre   = script.get("genre", "compatibility")
    cv      = FUN_GENRE_VISUAL.get(genre, {})
    accent  = cv.get("accent", P["saffron"])
    subject = script.get("subject", "")

    bg     = _make_genre_bg(genre, dark=True)
    frames = []
    total  = FPS * duration_s
    cx     = WIDTH // 2

    f_title  = get_text_font(46, bold=True)
    f_label  = get_text_font(36)
    f_value  = get_text_font(54, bold=True)
    f_bottom = get_text_font(36)
    f_badge  = get_text_font(28, bold=True)

    lucky_num  = str(script.get("lucky_number", 7))
    lucky_col  = script.get("lucky_color", "Gold")
    vibe_word  = script.get("vibe_word", "ELECTRIC")
    cta_text   = script.get("cta", "Follow for more cosmic insights! 👇")

    title_text = "COSMIC STATS"
    stats = [
        ("Lucky Number", lucky_num),
        ("Lucky Color",  lucky_col.title()),
        ("Your Vibe",    vibe_word),
        ("Energy",       subject.upper()),
    ]

    particle_col = hex_rgb(accent)

    for f in range(total):
        t   = f / max(total - 1, 1)
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        drw = ImageDraw.Draw(img, "RGBA")

        draw_particles(drw, t, particle_col, base_alpha=30)

        # Header
        h_t = ease_out_cubic(min(1.0, t / 0.08))
        h_a = int(255 * h_t)
        draw_text(drw, (cx, 120), title_text, font=f_title, anchor="mm",
                  fill=(*hex_rgb(accent), h_a))
        draw_text(drw, (cx, 185), subject.upper(),
                  font=get_text_font(36), anchor="mm",
                  fill=(*hex_rgb(P["saffron"]), int(200 * h_t)))
        if h_t > 0:
            draw_gold_divider(drw, cx, 230, w=700, alpha=int(200 * h_t),
                              color=hex_rgb(accent))

        # Stat cards
        card_h, card_w = 160, 900
        card_x     = (WIDTH - card_w) // 2
        card_y_base = 310

        for i, (label, value) in enumerate(stats):
            cd   = 0.08 + i * 0.08
            ct   = ease_out_cubic(max(0.0, min(1.0, (t - cd) / 0.15)))
            if t >= cd + 0.15:
                ct = 1.0
            sx   = int(200 * (1 - ct))
            cy   = card_y_base + i * (card_h + 20)
            ca   = int(255 * ct)
            if ca > 0:
                drw.rounded_rectangle(
                    [card_x + sx, cy, card_x + card_w + sx, cy + card_h],
                    radius=20,
                    fill=(*hex_rgb("#FFFFFF"), min(ca // 10, 20)),
                    outline=(*hex_rgb(accent), min(ca // 4, 60)),
                    width=1)
                lf = get_text_font(36)
                vf = get_text_font(52, bold=True)
                draw_text(drw, (cx + sx, cy + 52), label,
                          font=lf, anchor="mm",
                          fill=(*hex_rgb(P["gray"]), ca // 2))
                draw_text(drw, (cx + sx, cy + 115), value,
                          font=vf, anchor="mm",
                          fill=(*hex_rgb(P["ivory"]), ca))

        # CTA pill
        cta_t = ease_out_back(max(0.0, min(1.0, (t - 0.75) / 0.13)))
        if t >= 0.88:
            cta_t = 1.0
        cta_y = card_y_base + 4 * (card_h + 20) + 80
        if cta_t > 0:
            cta_bg = (*hex_rgb(accent), int(220 * cta_t))
            cta_f  = get_text_font(36, bold=True)
            draw_pill_badge(drw, cx, cta_y,
                            cta_text[:48] + ("…" if len(cta_text) > 48 else ""),
                            cta_f, cta_bg,
                            (*hex_rgb(cv.get("badge_fg", "#1A1A2E")), 255),
                            radius=30)

        # Bottom strip
        drw.rectangle([0, HEIGHT - 100, WIDTH, HEIGHT],
                      fill=(*hex_rgb(P["maroon"]), 200))
        draw_text(drw, (cx, HEIGHT - 50), "JyoteshAI  •  Daily Vedic Astrology",
                  font=f_bottom, anchor="mm",
                  fill=(*hex_rgb(P["gold"]), 200))

        frames.append(alpha_paste(bg, img))
    return frames


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR (drop-in compatible with generate_all_frames signature)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_all_genre_frames(script: dict, frames_dir: Path) -> int:
    """
    Render all slides for a fun-genre reel and save frames to disk.
    Slide order: hook → insights → extra → stats
    Returns total frame count.
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    counter = 0

    try:
        print("  Rendering genre hook slide ...", flush=True)
        hook_frames = create_genre_hook_frames(script, duration_s=6)
        counter, last = _save_frames(hook_frames, frames_dir, counter)
        del hook_frames

        print("  Rendering insight cards slide ...", flush=True)
        ins_frames = create_genre_insight_frames(script, duration_s=6)
        fade = make_crossfade(last, ins_frames[0], n=12)
        counter, _ = _save_frames(fade, frames_dir, counter);  del fade
        counter, last = _save_frames(ins_frames, frames_dir, counter)
        del ins_frames

        extra_frames = create_genre_extra_frames(script, duration_s=6)
        if extra_frames:
            print("  Rendering genre extra slide ...", flush=True)
            fade = make_crossfade(last, extra_frames[0], n=12)
            counter, _ = _save_frames(fade, frames_dir, counter);  del fade
            counter, last = _save_frames(extra_frames, frames_dir, counter)
            del extra_frames

        print("  Rendering stats/CTA slide ...", flush=True)
        stats_frames = create_genre_stats_frames(script, duration_s=8)
        fade = make_crossfade(last, stats_frames[0], n=12)
        counter, _ = _save_frames(fade, frames_dir, counter);  del fade
        counter, _ = _save_frames(stats_frames, frames_dir, counter)
        del stats_frames

    except Exception as e:
        print(f"\n  ❌ Error during genre frame generation: {e}")
        import traceback; traceback.print_exc()
        raise

    print(f"\n  Done: {counter} frames → {frames_dir}", flush=True)
    print(f"  Duration: ~{counter/FPS:.1f}s at {FPS} fps", flush=True)
    return counter


# ─── DEMO ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    genre = sys.argv[1] if len(sys.argv) > 1 else "compatibility"

    if genre == "name_initials":
        demo = {
            "genre": "name_initials", "subject": "A & J", "lang": "en",
            "letters": ["A", "J"],
            "hook": "If your name starts with A or J — the universe has been holding a secret about you...",
            "insights": [
                "A and J names carry one of the most powerful numerological vibrations.",
                "You were built for pressure — you become your best self under fire.",
                "Your biggest challenge? You trust too fast or not at all.",
                "Right now the cosmos is clearing blocks you've held since 2022.",
                "In love, you give everything — but rarely ask for what you need.",
            ],
            "personality_trait": "Natural leaders who never admit defeat.",
            "lucky_pairing": "Names starting with S or R",
            "lucky_number": 1,
            "lucky_color": "violet",
            "vibe_word": "UNSTOPPABLE",
            "cta": "Tag your A or J friend — they need to see this 👇",
        }
    elif genre == "lucky_month":
        demo = {
            "genre": "lucky_month", "subject": "May & June", "lang": "en",
            "months": ["May", "June"],
            "hook": "If you were born in May or June, the stars have been quietly watching over you...",
            "insights": [
                "May and June babies carry a rare blend of earth and air energy.",
                "Your greatest superpower is your ability to adapt without losing yourself.",
                "The challenge you keep facing is staying grounded when everything shifts.",
                "2026 is the year your hidden talents finally get seen by the right people.",
                "You love deeply but often settle for less than you deserve.",
            ],
            "power_period": "April 20 – June 21",
            "cosmic_message": "Stop dimming your light to make others comfortable.",
            "lucky_number": 3,
            "lucky_color": "emerald",
            "vibe_word": "BLOOMING",
            "cta": "Tag your May or June person — do they feel this? 👇",
        }
    else:  # compatibility
        demo = {
            "genre": "compatibility", "subject": "Aries & Scorpio", "lang": "en",
            "sign_a": "Aries", "sign_b": "Scorpio",
            "hook": "Aries and Scorpio together? The cosmos have strong opinions about this one...",
            "insights": [
                "When Aries and Scorpio meet, the attraction is instant and undeniable.",
                "Aries brings the spark — Scorpio brings the depth that makes it real.",
                "Their biggest battle? Control. Both want it. Neither surrenders it.",
                "As lovers they're magnetic. As enemies? Devastating.",
                "There's always one conversation they never fully finish.",
            ],
            "compatibility_score": "8/10",
            "chemistry": "Explosive, consuming, impossible to walk away from.",
            "verdict": "A bond that changes both of them forever — for better or worse.",
            "lucky_number": 8,
            "lucky_color": "deep red",
            "vibe_word": "INTENSE",
            "cta": "Tag your Aries or Scorpio — do they agree? 👇",
        }

    generate_all_genre_frames(demo, Path(f"demo_frames_{genre}"))
    print(f"\n✅ Demo complete — check 'demo_frames_{genre}/'")
