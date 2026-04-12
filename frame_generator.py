#!/usr/bin/env python3
"""
Frame Generator v5 — Viral Categories + Bilingual Edition
──────────────────────────────────────────────────────────
New in v5:
  • Hindi / Devanagari font support (Nirmala UI on Windows)
  • Per-category visual accents: color tinting, category badge on hook
  • Language tag badge in hook frame (EN | HI)
  • Category-specific body slide accents
  • Wider text wrap for Hindi (Devanagari is narrower per char)
  • Emotional content slide for extra fields (compatibility, power_move, etc.)
  • 5+1 slides: hook → body×N → emotional_extra → stats
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap, os, math, sys, random
from pathlib import Path
from functools import lru_cache

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

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
    # New category accents
    "rose":     "#E63C6E",
    "blue":     "#1E90FF",
    "purple":   "#9B59B6",
}

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

WIDTH, HEIGHT = 1080, 1920
FPS = 30

# ─── ZODIAC ───────────────────────────────────────────────────────────────────
ZODIAC_CHAR = {
    "Aries":"♈","Taurus":"♉","Gemini":"♊","Cancer":"♋",
    "Leo":"♌","Virgo":"♍","Libra":"♎","Scorpio":"♏",
    "Sagittarius":"♐","Capricorn":"♑","Aquarius":"♒","Pisces":"♓",
}
SIGN_DARK = {"Scorpio", "Capricorn", "Aquarius"}

# ─── CATEGORY VISUAL CONFIGS ──────────────────────────────────────────────────
try:
    from content_categories import CATEGORY_VISUAL, CATEGORY_DISPLAY, CATEGORY_DISPLAY_HI
    _HAS_CATEGORIES = True
except ImportError:
    _HAS_CATEGORIES = False
    CATEGORY_VISUAL = {}
    CATEGORY_DISPLAY = {}
    CATEGORY_DISPLAY_HI = {}

def get_category_visual(category: str) -> dict:
    if not category or category == "horoscope" or not _HAS_CATEGORIES:
        return {
            "accent":   P["saffron"],
            "tint":     P["charcoal"],
            "label":    "HOROSCOPE",
            "particle": P["gold"],
            "badge_bg": P["saffron"],
            "badge_fg": "#1A1A2E",
        }
    return CATEGORY_VISUAL.get(category, {
        "accent":   P["saffron"],
        "tint":     P["charcoal"],
        "label":    category.upper(),
        "particle": P["gold"],
        "badge_bg": P["saffron"],
        "badge_fg": "#1A1A2E",
    })

# ─── FONT RESOLUTION ──────────────────────────────────────────────────────────

def _try_fonts(candidates, size, bold=False):
    for p in candidates:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, size)
                try:
                    font._codex_path = p
                    font._codex_bold = bool(bold)
                except Exception:
                    pass
                return font
            except Exception:
                continue
    font = ImageFont.load_default()
    try:
        font._codex_path = ""
        font._codex_bold = bool(bold)
    except Exception:
        pass
    return font


@lru_cache(maxsize=64)
def get_text_font(size, bold=False):
    if sys.platform == "win32":
        candidates = [
            r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arialbd.ttf"  if bold else r"C:\Windows\Fonts\arial.ttf",
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        ]
    return _try_fonts(candidates, size, bold=bold)


@lru_cache(maxsize=32)
def get_symbol_font(size):
    if sys.platform == "win32":
        candidates = [
            r"C:\Windows\Fonts\seguisym.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Apple Symbols.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    return _try_fonts(candidates, size, bold=False)


@lru_cache(maxsize=32)
def get_hindi_font(size, bold=False):
    """
    Devanagari font for Hindi text rendering.
    Nirmala UI is pre-installed on Windows 10/11 and looks beautiful.
    Falls back to NotoSansDevanagari or any available Unicode font.
    """
    if sys.platform == "win32":
        candidates = [
            r"C:\Windows\Fonts\Nirmala.ttc",
            r"C:\Windows\Fonts\NirmalaB.ttf" if bold else r"C:\Windows\Fonts\Nirmala.ttf",
            r"C:\Windows\Fonts\nirmala.ttf",
            r"C:\Windows\Fonts\NotoSansDevanagari-Bold.ttf" if bold
            else r"C:\Windows\Fonts\NotoSansDevanagari-Regular.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",   # last resort
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts/Supplemental/Devanagari MT.ttf",
            "/Library/Fonts/NotoSansDevanagari-Regular.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    font = _try_fonts(candidates, size, bold=bold)
    return font


def _is_devanagari(text: str) -> bool:
    """Check if the text contains Devanagari characters."""
    return any('\u0900' <= ch <= '\u097F' for ch in text)


def smart_font(text: str, size: int, bold: bool = False):
    """Pick the right font: Hindi for Devanagari, Latin for everything else."""
    if _is_devanagari(text):
        return get_hindi_font(size, bold)
    return get_text_font(size, bold)


def get_font(size, bold=False):  # backward compat
    return get_text_font(size, bold)


def _font_path(font) -> str:
    return getattr(font, "_codex_path", getattr(font, "path", "")) or ""


def _font_is_bold(font) -> bool:
    if hasattr(font, "_codex_bold"):
        return bool(font._codex_bold)
    path = _font_path(font).lower()
    return any(token in path for token in ("bold", "bd", "uib"))


def _font_face_name(font) -> str:
    path = _font_path(font).lower()
    if "nirmala" in path:
        return "Nirmala UI"
    if "seguisym" in path:
        return "Segoe UI Symbol"
    if "segoeui" in path:
        return "Segoe UI"
    if "arial" in path:
        return "Arial"
    return "Nirmala UI"


def _normalize_fill(fill):
    if fill is None:
        return (255, 255, 255, 255)
    if isinstance(fill, str):
        return (*hex_rgb(fill), 255)
    if len(fill) == 3:
        return (fill[0], fill[1], fill[2], 255)
    return tuple(fill)


@lru_cache(maxsize=512)
def _render_text_mask_windows(text: str, font_name: str, font_size: int, bold: bool):
    if not text:
        return Image.new("RGBA", (1, 1), (255, 255, 255, 0))

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BITMAPINFOHEADER),
            ("bmiColors", wintypes.DWORD * 3),
        ]

    gdi32 = ctypes.windll.gdi32
    user32 = ctypes.windll.user32

    estimate = max(font_size, font_size * max(len(text), 1))
    width = min(max(estimate + 96, 256), WIDTH * 2)
    height = max(font_size * 3, 160)
    padding = max(24, font_size // 2)

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    bits = ctypes.c_void_p()
    hdc = gdi32.CreateCompatibleDC(0)
    hbitmap = gdi32.CreateDIBSection(hdc, ctypes.byref(bmi), 0, ctypes.byref(bits), 0, 0)
    old_bitmap = gdi32.SelectObject(hdc, hbitmap)
    hfont = gdi32.CreateFontW(
        -font_size, 0, 0, 0,
        700 if bold else 400,
        0, 0, 0,
        1, 0, 0, 5, 0,
        font_name,
    )
    old_font = gdi32.SelectObject(hdc, hfont)
    gdi32.SetBkMode(hdc, 1)
    gdi32.SetTextColor(hdc, 0x00FFFFFF)
    user32.DrawTextW(hdc, text, len(text), ctypes.byref(wintypes.RECT(padding, padding, width - padding, height - padding)), 0)

    try:
        raw = ctypes.string_at(bits, width * height * 4)
        rgba = Image.frombuffer("RGBA", (width, height), raw, "raw", "BGRA", 0, 1)
        alpha = rgba.convert("L")
        rendered = Image.new("RGBA", rgba.size, (255, 255, 255, 0))
        rendered.putalpha(alpha)
        bbox = rendered.getbbox()
        if not bbox:
            return Image.new("RGBA", (1, 1), (255, 255, 255, 0))
        return rendered.crop(bbox)
    finally:
        gdi32.SelectObject(hdc, old_font)
        gdi32.SelectObject(hdc, old_bitmap)
        gdi32.DeleteObject(hfont)
        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(hdc)


def measure_text(text: str, font) -> tuple[int, int]:
    if sys.platform == "win32" and _is_devanagari(text):
        mask = _render_text_mask_windows(text, _font_face_name(font), getattr(font, "size", 32), _font_is_bold(font))
        return mask.size
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_text(draw, xy, text, font, anchor=None, fill=None):
    if not (sys.platform == "win32" and _is_devanagari(text)):
        draw.text(xy, text, font=font, anchor=anchor, fill=fill)
        return

    fill_rgba = _normalize_fill(fill)
    mask = _render_text_mask_windows(text, _font_face_name(font), getattr(font, "size", 32), _font_is_bold(font))
    alpha = mask.getchannel("A")
    if fill_rgba[3] != 255:
        alpha = alpha.point(lambda p: p * fill_rgba[3] // 255)
    colored = Image.new("RGBA", mask.size, (*fill_rgba[:3], 0))
    colored.putalpha(alpha)

    x, y = xy
    w, h = mask.size
    anchor = anchor or "la"
    if len(anchor) == 2:
        if anchor[0] == "m":
            x -= w // 2
        elif anchor[0] == "r":
            x -= w
        if anchor[1] == "m":
            y -= h // 2
        elif anchor[1] in ("b", "d"):
            y -= h
    draw._image.alpha_composite(colored, (int(x), int(y)))


# ─── EASING ───────────────────────────────────────────────────────────────────
def ease_out_cubic(t):   return 1 - (1 - t) ** 3
def ease_in_out_sine(t): return -(math.cos(math.pi * t) - 1) / 2
def ease_out_back(t, s=1.70158): return 1 + (s+1)*(t-1)**3 + s*(t-1)**2
def ease_out_expo(t):    return 1 if t == 1 else 1 - 2**(-10*t)
def lerp(a, b, t):       return a + (b - a) * t
def alpha_lerp(a, b, t): return int(lerp(a, b, t))

# ─── DRAWING PRIMITIVES ───────────────────────────────────────────────────────
def draw_gradient(draw, w, h, c1, c2):
    r1,g1,b1 = hex_rgb(c1); r2,g2,b2 = hex_rgb(c2)
    for i in range(h):
        t = i / h
        draw.line([(0, i), (w, i)], fill=(
            int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)
        ))

def draw_mandala(draw, cx, cy, r=480, color=(123,31,58), alpha=10):
    c = (*color, alpha)
    for rr in [r*0.9, r*0.7, r*0.5, r*0.3, r*0.15]:
        draw.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], outline=c, width=1)
    for deg in range(0, 360, 30):
        angle = math.radians(deg)
        x1=cx+r*0.15*math.cos(angle); y1=cy+r*0.15*math.sin(angle)
        x2=cx+r*0.9*math.cos(angle);  y2=cy+r*0.9*math.sin(angle)
        draw.line([(x1,y1),(x2,y2)], fill=c, width=1)

def draw_gold_divider(draw, cx, y, w=800, alpha=120, color=None):
    col = color or hex_rgb(P["gold"])
    draw.line([(cx-w//2, y), (cx+w//2, y)], fill=(*col, alpha), width=2)
    d = 12
    draw.polygon([(cx,y-d),(cx+d,y),(cx,y+d),(cx-d,y)], fill=(*col, 160))

def draw_pill_badge(draw, cx, cy, text, font, bg, fg, radius=40):
    tw, th = measure_text(text, font)
    px, py = 40, 20
    draw.rounded_rectangle([cx-tw//2-px, cy-th//2-py, cx+tw//2+px, cy+th//2+py],
                            radius=radius, fill=bg)
    draw_text(draw, (cx, cy), text, font=font, anchor="mm", fill=fg)

def draw_star_ornament(draw, sx, sy, col):
    d=10
    draw.polygon([(sx,sy-d),(sx+d*0.6,sy-d*0.2),(sx+d,sy+d*0.4),
                  (sx+d*0.3,sy+d),(sx-d*0.3,sy+d),(sx-d,sy+d*0.4),
                  (sx-d*0.6,sy-d*0.2)], fill=col)

def _generate_particles(n=18, seed=42):
    rng = random.Random(seed)
    return [{
        "x": rng.uniform(40, WIDTH-40), "y": rng.uniform(100, HEIGHT-150),
        "r": rng.uniform(1.5, 4.0), "speed": rng.uniform(0.3, 1.2),
        "phase": rng.uniform(0, math.pi*2), "drift_x": rng.uniform(-0.4, 0.4),
    } for _ in range(n)]

_PARTICLES = _generate_particles()

def draw_particles(draw, t, color_rgb, base_alpha=40):
    for p in _PARTICLES:
        py = (p["y"] - p["speed"]*t*300) % (HEIGHT-200) + 100
        px = p["x"] + math.sin(t*2+p["phase"])*20*p["drift_x"]
        alpha = int(base_alpha*(0.5+0.5*math.sin(t*3+p["phase"])))
        alpha = max(0, min(255, alpha))
        r = p["r"]
        draw.ellipse([px-r, py-r, px+r, py+r], fill=(*color_rgb, alpha))

def draw_category_badge(draw, font, label: str, accent_hex: str, badge_fg_hex: str, alpha: float = 1.0):
    """Small category label pill in top-right corner of the frame."""
    if not label or alpha <= 0:
        return
    badge_x = WIDTH - 20
    badge_y = 90
    bg = (*hex_rgb(accent_hex), int(210 * alpha))
    fg = (*hex_rgb(badge_fg_hex), int(255 * alpha))
    tw, th = measure_text(label, font)
    px, py = 24, 14
    draw.rounded_rectangle(
        [badge_x - tw - 2*px, badge_y - th//2 - py,
         badge_x,             badge_y + th//2 + py],
        radius=20, fill=bg
    )
    draw_text(draw, (badge_x - tw//2 - px, badge_y), label,
              font=font, anchor="mm", fill=fg)

def draw_lang_badge(draw, font, lang: str, alpha: float = 1.0):
    """Language indicator badge (EN / HI) in top-left area."""
    if alpha <= 0:
        return
    label   = "EN" if lang != "hi" else "HI"
    bg_hex  = P["green"] if lang == "hi" else P["saffron"]
    fg_hex  = "#FFFFFF" if lang == "hi" else "#1A1A2E"
    badge_x = 20
    badge_y = 90
    bg = (*hex_rgb(bg_hex), int(200 * alpha))
    fg = (*hex_rgb(fg_hex), int(255 * alpha))
    tw, th = measure_text(label, font)
    px, py = 20, 12
    draw.rounded_rectangle(
        [badge_x, badge_y - th//2 - py,
         badge_x + tw + 2*px, badge_y + th//2 + py],
        radius=18, fill=bg
    )
    draw_text(draw, (badge_x + tw//2 + px, badge_y), label,
              font=font, anchor="mm", fill=fg)

def make_background(sign, is_dark, category=None):
    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")

    cv = get_category_visual(category)
    tint_hex = cv.get("tint", None)

    if is_dark:
        c1, c2 = "#1A1A2E", "#0D0D1A"
    else:
        c1, c2 = "#FDF8F0", "#FFFBF2"

    # For viral categories, add a subtle tint overlay
    if tint_hex and category and category != "horoscope":
        if is_dark:
            c1 = _blend_colors("#1A1A2E", tint_hex, 0.35)
            c2 = _blend_colors("#0D0D1A", tint_hex, 0.20)
        else:
            c1 = _blend_colors("#FDF8F0", tint_hex, 0.08)
            c2 = _blend_colors("#FFFBF2", tint_hex, 0.05)

    draw_gradient(draw, WIDTH, HEIGHT, c1, c2)
    return img


def _blend_colors(hex1: str, hex2: str, t: float) -> str:
    r1,g1,b1 = hex_rgb(hex1)
    r2,g2,b2 = hex_rgb(hex2)
    r = int(r1 + (r2-r1)*t)
    g = int(g1 + (g2-g1)*t)
    b = int(b1 + (b2-b1)*t)
    return f"#{r:02x}{g:02x}{b:02x}"

def alpha_paste(base_rgb, overlay_rgba):
    base = base_rgb.convert("RGBA")
    base.alpha_composite(overlay_rgba)
    return base.convert("RGB")

def animated_text(draw, cx, y, text, font, color_rgb, progress):
    if progress <= 0:
        return
    if progress >= 1.0:
        draw_text(draw, (cx, y), text, font=font, anchor="mt", fill=(*color_rgb, 255))
        return

    alpha = int(ease_out_cubic(progress) * 255)
    draw_text(draw, (cx, y), text, font=font, anchor="mt", fill=(*color_rgb, alpha))

def smart_wrap(text: str, width_en=24, width_hi=18) -> list:
    """Wrap with appropriate width for the script language."""
    if _is_devanagari(text):
        return textwrap.wrap(text, width=width_hi)
    return textwrap.wrap(text, width=width_en)


# ─── HOOK FRAME ───────────────────────────────────────────────────────────────
def create_hook_frames(script, duration_s=6):
    sign     = script["sign"]
    category = script.get("category", "horoscope")
    lang     = script.get("lang", "en")
    is_dark  = sign in SIGN_DARK
    tc_hex   = P["maroon"] if not is_dark else P["gold"]
    cv       = get_category_visual(category)
    accent_hex = cv.get("accent", P["saffron"])

    bg     = make_background(sign, is_dark, category)
    frames = []
    total  = FPS * duration_s
    cx     = WIDTH // 2

    f_brand   = get_text_font(36)
    f_date    = get_text_font(34)
    f_sym     = get_symbol_font(200)
    f_name    = get_text_font(68, bold=True)
    f_hook    = smart_font(script.get("hook",""), 52, bold=True)
    f_bottom  = get_text_font(38)
    f_badge   = get_text_font(30, bold=True)

    particle_col = hex_rgb(accent_hex if category != "horoscope" else (P["gold"] if is_dark else P["saffron"]))
    cat_label    = CATEGORY_DISPLAY.get(category, category.upper()) if lang == "en" else CATEGORY_DISPLAY_HI.get(category, category.upper())

    for f in range(total):
        t = f / max(total-1, 1)
        img  = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        # Particles
        draw_particles(draw, t, particle_col, base_alpha=25 if is_dark else 15)

        # Language badge (top-left)
        lang_t = ease_out_cubic(min(1.0, t/0.10))
        draw_lang_badge(draw, f_badge, lang, alpha=lang_t)

        # Category badge (top-right)
        if cat_label and category != "horoscope":
            f_cat = smart_font(cat_label, 28, bold=True)
            draw_category_badge(draw, f_cat, cat_label,
                                accent_hex, cv.get("badge_fg","#FFFFFF"),
                                alpha=lang_t)

        # Brand header
        hdr_t = ease_out_cubic(min(1.0, t/0.10))
        brand_col = (*hex_rgb(P["saffron"] if not is_dark else P["gold"]), int(200*hdr_t))
        draw_text(draw, (cx, 80), "JyoteshAI",
                  font=f_brand, anchor="mm", fill=brand_col)
        # Date removed per user request
        if hdr_t > 0:
            draw.rectangle([cx-60, 155, cx+60, 157],
                           fill=(*hex_rgb(accent_hex), int(180*hdr_t)))

        # Zodiac circle
        circ_t   = ease_out_back(max(0.0, min(1.0, (t-0.08)/0.27)))
        symbol_y = 520
        circle_r = int(240*circ_t)
        if circle_r > 0:
            for gr in [circle_r+80, circle_r+50, circle_r+20]:
                ga = int(30*(1-(gr-circle_r)/80)*circ_t)
                draw.ellipse([cx-gr, symbol_y-gr, cx+gr, symbol_y+gr],
                             outline=(*hex_rgb(accent_hex), ga), width=1)
            circle_fill = (*hex_rgb(P["maroon"] if is_dark else "#F0E8DC"), 255)
            draw.ellipse([cx-circle_r, symbol_y-circle_r, cx+circle_r, symbol_y+circle_r],
                         fill=circle_fill,
                         outline=(*hex_rgb(P["maroon"]), 80), width=2)
            sym_a = int(240*circ_t)
            draw_text(draw, (cx, symbol_y), ZODIAC_CHAR.get(sign, "★"),
                      font=f_sym, anchor="mm",
                      fill=(*hex_rgb(tc_hex), sym_a))

        # Sign name badge
        name_y_target = symbol_y + 324
        badge_t = ease_out_cubic(max(0.0, min(1.0, (t-0.30)/0.15)))
        name_y  = name_y_target + int(60*(1-badge_t))
        badge_bg = (*hex_rgb(accent_hex), int(220*badge_t))
        badge_fg = (*hex_rgb(cv.get("badge_fg","#1A1A2E")), 255)
        if badge_t > 0:
            draw_pill_badge(draw, cx, name_y, sign.upper(), f_name, badge_bg, badge_fg)

        # Gold divider (uses accent color)
        div_y = name_y_target + 90
        div_t = ease_out_cubic(max(0.0, min(1.0, (t-0.42)/0.08)))
        if div_t > 0:
            draw_gold_divider(draw, cx, div_y, alpha=int(120*div_t),
                              color=hex_rgb(accent_hex))

        # Hook text
        hook_anim_start = 0.45
        hook_anim_end   = 0.75
        hook_t = max(0.0, min(1.0, (t-hook_anim_start)/(hook_anim_end-hook_anim_start)))
        if hook_t > 0 or t >= hook_anim_end:
            display_t = 1.0 if t >= hook_anim_end else hook_t
            hook_y    = div_y + 80
            lines     = smart_wrap(script.get("hook",""), 22, 16)
            col_rgb   = hex_rgb(P["charcoal"] if not is_dark else P["ivory"])
            for li, line in enumerate(lines):
                lf = smart_font(line, 52, bold=True)
                line_delay = li*0.18
                line_t = max(0.0, min(1.0, (display_t-line_delay)/max(1.0-line_delay,0.001)))
                offset_y = int(60*(1-ease_out_cubic(line_t)))
                animated_text(draw, cx, hook_y+offset_y, line, lf, col_rgb, line_t)
                hook_y += 90

        # Bottom strip
        strip_a = int(240*ease_out_cubic(min(1.0, t/0.10)))
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["charcoal"]), strip_a))
        if strip_a > 0:
            for sx in [cx-180, cx+180]:
                draw_star_ornament(draw, sx, HEIGHT-50, (*hex_rgb(P["gold"]), strip_a))
            draw_text(draw, (cx, HEIGHT-50), "JyoteshAI",
                      font=f_bottom, anchor="mm",
                      fill=(*hex_rgb(P["gold"]), strip_a))

        frames.append(alpha_paste(bg, img))
    return frames


# ─── BODY FRAME ───────────────────────────────────────────────────────────────
def create_body_frames(script, body_idx, duration_s=6):
    sign     = script["sign"]
    category = script.get("category", "horoscope")
    lang     = script.get("lang", "en")
    is_dark  = sign in SIGN_DARK
    body     = script.get("body", [])
    cv       = get_category_visual(category)
    accent_hex = cv.get("accent", P["saffron"])

    bg     = make_background(sign, is_dark=False, category=category)
    frames = []
    total  = FPS * duration_s
    cx     = WIDTH // 2

    f_header  = get_text_font(40, bold=True)
    f_date    = get_text_font(32)
    f_vibe_v  = get_text_font(58, bold=True)
    f_bottom  = get_text_font(40)
    f_sym     = get_symbol_font(40)
    f_badge   = get_text_font(28, bold=True)

    particle_col = hex_rgb(accent_hex)

    for f in range(total):
        t = f / max(total-1, 1)
        img  = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        draw_particles(draw, t, particle_col, base_alpha=12)

        # Header strip (uses accent color tint)
        hdr_t   = ease_out_cubic(min(1.0, t/0.08))
        strip_y = int(-160*(1-hdr_t))
        header_bg = (*hex_rgb(_blend_colors(P["maroon"], accent_hex, 0.4)), 255)
        draw.rectangle([0, strip_y, WIDTH, 160+strip_y], fill=header_bg)

        sign_label = sign.upper()
        zodiac_sym = ZODIAC_CHAR.get(sign, '')
        sym_bbox   = f_sym.getbbox(zodiac_sym)
        sym_w      = (sym_bbox[2]-sym_bbox[0]) if zodiac_sym else 0
        hdr_bbox   = f_header.getbbox(sign_label)
        hdr_w      = hdr_bbox[2]-hdr_bbox[0]
        comb_w     = sym_w + 20 + hdr_w
        start_x    = cx - comb_w//2
        if zodiac_sym:
            draw_text(draw, (start_x, 55+strip_y), zodiac_sym, font=f_sym, anchor="lm",
                      fill=(*hex_rgb(P["gold"]), 255))
        draw_text(draw, (start_x+sym_w+20, 55+strip_y), sign_label, font=f_header, anchor="lm",
                  fill=(*hex_rgb(P["gold"]), 255))
        # Date removed per user request

        # Language badge (body slides — small, top right)
        lang_t = ease_out_cubic(min(1.0, t/0.10))
        draw_lang_badge(draw, f_badge, lang, alpha=lang_t*0.85)

        # Progress dots
        dot_a = int(200*ease_out_cubic(min(1.0, t/0.15)))
        dot_y = 240
        n_dots = len(body)
        dot_spacing = 40
        sx = cx - (n_dots*dot_spacing)//2
        for i in range(n_dots):
            dx = sx + i*dot_spacing + 20
            if i == body_idx:
                draw.rounded_rectangle([dx-20, dot_y-8, dx+20, dot_y+8], 8,
                                       fill=(*hex_rgb(accent_hex), dot_a))
            else:
                draw.ellipse([dx-8, dot_y-8, dx+8, dot_y+8],
                             fill=(*hex_rgb(P["gray"]), dot_a//3))

        # Body text
        anim_start = 0.10; anim_end = 0.55
        text_prog = max(0.0, min(1.0, (t-anim_start)/(anim_end-anim_start)))
        if t >= anim_end:
            text_prog = 1.0

        text_y = 340
        if body_idx < len(body):
            line_text = body[body_idx]
            f_body    = smart_font(line_text, 58, bold=True)
            lines     = smart_wrap(line_text, 24, 18)
            for li, line in enumerate(lines):
                lf = smart_font(line, 58, bold=True)
                line_delay = li*0.15
                line_t = max(0.0, min(1.0, (text_prog-line_delay)/max(1.0-line_delay,0.001)))
                offset_y = int(60*(1-ease_out_cubic(line_t)))
                animated_text(draw, cx, text_y+offset_y, line, lf, hex_rgb(P["charcoal"]), line_t)
                text_y += 100

        # Vibe accent
        vibe_anim_t = max(0.0, min(1.0, (t-0.55)/0.20))
        if t >= 0.75: vibe_anim_t = 1.0
        vibe_prog = ease_out_cubic(vibe_anim_t)
        vibe_y = max(text_y+60, 900)
        vibe_a = int(160*vibe_prog)
        if vibe_a > 0:
            draw.line([(cx-200, vibe_y),(cx+200, vibe_y)],
                      fill=(*hex_rgb(accent_hex), vibe_a//4), width=1)
            vibe_label = "TODAY'S ENERGY" if lang == "en" else "आज का मूड"
            vibe_label_font = smart_font(vibe_label, 38)
            draw_text(draw, (cx, vibe_y+40), vibe_label,
                      font=vibe_label_font, anchor="mm",
                      fill=(*hex_rgb(P["gray"]), vibe_a))
            vibe_text   = script.get("vibe_word", "POWERFUL")
            vibe_font   = smart_font(vibe_text, 58, bold=True)
            draw_text(draw, (cx, vibe_y+110), vibe_text, font=vibe_font, anchor="mm",
                      fill=(*hex_rgb(accent_hex), vibe_a))

        # Bottom strip
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["charcoal"]), 240))
        draw_text(draw, (cx, HEIGHT-50), "JyoteshAI", font=f_bottom, anchor="mm",
                  fill=(*hex_rgb(P["gold"]), 220))

        frames.append(alpha_paste(bg, img))
    return frames


# ─── EMOTIONAL EXTRA FRAME (category-specific insight) ───────────────────────
def create_extra_frames(script, duration_s=6):
    """
    Slide unique to each viral category: shows the category-specific extra field.
    e.g., compatibility_tip + warning for relationships
          power_move + avoid for career, etc.
    """
    sign     = script["sign"]
    category = script.get("category", "horoscope")
    lang     = script.get("lang", "en")
    cv       = get_category_visual(category)
    accent_hex = cv.get("accent", P["saffron"])

    # Determine what to show per category
    extra_content = _get_extra_content(script, category, lang)
    if not extra_content:
        return []  # No extra slide for horoscope

    bg     = make_background(sign, is_dark=True, category=category)
    frames = []
    total  = FPS * duration_s
    cx     = WIDTH // 2

    f_label  = get_text_font(34, bold=True)
    f_bottom = get_text_font(36)
    f_badge  = get_text_font(28, bold=True)

    particle_col = hex_rgb(accent_hex)

    for f in range(total):
        t = f / max(total-1, 1)
        img  = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        draw_particles(draw, t, particle_col, base_alpha=30)

        # Language badge
        lang_ba = ease_out_cubic(min(1.0, t/0.10))
        draw_lang_badge(draw, f_badge, lang, alpha=lang_ba)

        # Big accent bar at top
        h_t = ease_out_cubic(min(1.0, t/0.12))
        bar_h = int(200*h_t)
        draw.rectangle([0, 0, WIDTH, bar_h],
                       fill=(*hex_rgb(accent_hex), int(230*h_t)))

        # Category display title
        cat_disp = CATEGORY_DISPLAY.get(category, category.upper()) if lang == "en" else CATEGORY_DISPLAY_HI.get(category, category.upper())
        if h_t > 0:
            cat_title_font = smart_font(cat_disp, 44, bold=True)
            draw_text(draw, (cx, 85), cat_disp,
                      font=cat_title_font, anchor="mm",
                      fill=(*hex_rgb(cv.get("badge_fg","#FFFFFF")), int(255*h_t)))
            draw_text(draw, (cx, 140), sign.upper(),
                      font=get_text_font(32), anchor="mm",
                      fill=(*hex_rgb("#FFFFFF"), int(180*h_t)))

        # Content blocks
        y = 260
        for i, (label, content) in enumerate(extra_content):
            block_delay = 0.12 + i*0.15
            block_t = ease_out_cubic(max(0.0, min(1.0, (t-block_delay)/0.20)))
            if t >= block_delay + 0.25:
                block_t = 1.0
            block_a = int(255*block_t)

            if block_a > 0:
                # Label tag
                lbl_font = smart_font(label, 30, bold=True)
                lbl_w, lbl_h = measure_text(label, lbl_font)
                pad_x, pad_y = 28, 14
                slide_off = int(80*(1-block_t))
                draw.rounded_rectangle(
                    [cx-lbl_w//2-pad_x+slide_off, y-pad_y,
                     cx+lbl_w//2+pad_x+slide_off, y+lbl_h+pad_y],
                    radius=24,
                    fill=(*hex_rgb(accent_hex), min(block_a, 180)))
                draw_text(draw, (cx+slide_off, y+14), label, font=lbl_font, anchor="mm",
                          fill=(*hex_rgb(cv.get("badge_fg","#FFFFFF")), block_a))
                y += lbl_h + 40

                # Content text
                c_font = smart_font(content, 46, bold=False)
                c_lines = smart_wrap(content, 26, 20)
                for li, line in enumerate(c_lines):
                    lf = smart_font(line, 46, bold=False)
                    line_delay = li*0.08
                    lt = max(0.0, min(1.0, (block_t-line_delay)/max(1.0-line_delay,0.001)))
                    offset_y = int(60*(1-ease_out_cubic(lt)))
                    animated_text(draw, cx+slide_off, y+offset_y, line, lf,
                                  hex_rgb(P["ivory"]), lt)
                    y += 70
                y += 60  # gap between blocks

                # Divider
                if i < len(extra_content)-1:
                    div_a = int(80*block_t)
                    draw_gold_divider(draw, cx, y-20, w=600, alpha=div_a,
                                      color=hex_rgb(accent_hex))

        # Bottom strip
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["charcoal"]), 230))
        draw_text(draw, (cx, HEIGHT-50), "JyoteshAI", font=f_bottom, anchor="mm",
                  fill=(*hex_rgb(P["gold"]), 200))

        frames.append(alpha_paste(bg, img))
    return frames


def _get_extra_content(script: dict, category: str, lang: str) -> list:
    """Return list of (label, content) tuples for the extra slide per category."""
    if not category or category == "horoscope":
        return []

    field_map = {
        "relationships": [
            ("COMPATIBILITY TIP" if lang == "en" else "किससे बात जमेगी",  "compatibility_tip"),
            ("RED FLAG"          if lang == "en" else "ध्यान रखें",        "warning"),
        ],
        "career": [
            ("YOUR POWER MOVE" if lang == "en" else "आज क्या करें", "power_move"),
            ("AVOID THIS"      if lang == "en" else "इससे बचो",     "avoid"),
        ],
        "current_events": [
            ("COSMIC HEADLINE" if lang == "en" else "आज का इशारा", "cosmic_headline"),
            ("ACT NOW"         if lang == "en" else "अभी क्या करें", "action_now"),
        ],
        "emotional_healing": [
            ("THE WOUND"     if lang == "en" else "दिल का दर्द", "wound_theme"),
            ("AFFIRMATION"   if lang == "en" else "आज की लाइन", "affirmation"),
        ],
        "manifestation": [
            ("YOUR CODE"  if lang == "en" else "आपका नंबर", "manifestation_code"),
            ("THE RITUAL" if lang == "en" else "आज की आदत", "ritual"),
        ],
    }
    pairs = field_map.get(category, [])
    result = []
    for label, key in pairs:
        val = script.get(key, "")
        if val:
            result.append((label, str(val)))
    return result


# ─── STATS FRAME ──────────────────────────────────────────────────────────────
def create_stats_frames(script, duration_s=8):
    sign     = script["sign"]
    category = script.get("category", "horoscope")
    lang     = script.get("lang", "en")
    cv       = get_category_visual(category)
    accent_hex = cv.get("accent", P["saffron"])

    bg     = make_background(sign, is_dark=True, category=category)
    frames = []
    total  = FPS * duration_s
    cx     = WIDTH // 2

    f_title  = get_text_font(46, bold=True)
    f_sign   = get_text_font(38)
    f_label  = get_text_font(36)
    f_value  = get_text_font(52, bold=True)
    f_bottom = get_text_font(36)
    f_sym    = get_symbol_font(38)
    f_badge  = get_text_font(28, bold=True)

    lucky_num = str(script.get("lucky_number", 7))
    lucky_col = script.get("lucky_color", "Gold")
    vibe_word = script.get("vibe_word", "POWERFUL")
    reveal    = script.get("reveal", "")
    cta_text  = (script.get("cta", "Follow for daily updates!"))

    title_text = "TODAY'S COSMIC NUMBERS" if lang == "en" else "आज के शुभ नंबर"
    lucky_n_lbl = "Lucky Number" if lang == "en" else "लकी नंबर"
    power_c_lbl = "Power Color"  if lang == "en" else "लकी रंग"
    vibe_lbl    = "Today's Vibe" if lang == "en" else "आज का मूड"
    sign_lbl    = "Sign"         if lang == "en" else "साइन"

    stats = [
        (lucky_n_lbl, lucky_num),
        (power_c_lbl, lucky_col.title()),
        (vibe_lbl,    vibe_word),
        (sign_lbl,    sign),
    ]

    particle_col = hex_rgb(accent_hex)

    for f in range(total):
        t = f / max(total-1, 1)
        img  = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(img, "RGBA")

        draw_particles(draw, t, particle_col, base_alpha=30)

        # Lang badge
        lang_ba = ease_out_cubic(min(1.0, t/0.08))
        draw_lang_badge(draw, f_badge, lang, alpha=lang_ba)

        # Header
        h_t = ease_out_cubic(min(1.0, t/0.08))
        h_a = int(255*h_t)
        title_f = smart_font(title_text, 46, bold=True)
        draw_text(draw, (cx, 120), title_text, font=title_f, anchor="mm",
                  fill=(*hex_rgb(accent_hex), h_a))

        sign_text = sign.upper()
        zodiac_sym = ZODIAC_CHAR.get(sign, '')
        sign_a = int(200*h_t)
        txt_bbox = f_sign.getbbox(sign_text)
        txt_w    = txt_bbox[2]-txt_bbox[0]
        sym_bbox = f_sym.getbbox(zodiac_sym) if zodiac_sym else (0,0,0,0)
        sym_w    = (sym_bbox[2]-sym_bbox[0]) if zodiac_sym else 0
        total_w  = txt_w + 16 + sym_w
        sx       = cx - total_w//2
        draw_text(draw, (sx, 185), sign_text, font=f_sign, anchor="lm",
                  fill=(*hex_rgb(P["saffron"]), sign_a))
        if zodiac_sym:
            draw_text(draw, (sx+txt_w+16, 185), zodiac_sym, font=f_sym, anchor="lm",
                      fill=(*hex_rgb(P["saffron"]), sign_a))
        if h_t > 0:
            draw_gold_divider(draw, cx, 230, w=700, alpha=int(200*h_t),
                              color=hex_rgb(accent_hex))

        # Stat cards
        card_h = 160; card_w = 900
        card_x = (WIDTH-card_w)//2
        card_y_base = 310

        for i, (label, value) in enumerate(stats):
            card_delay   = 0.08 + i*0.08
            card_anim_end = card_delay + 0.15
            card_t = ease_out_cubic(max(0.0, min(1.0, (t-card_delay)/0.15)))
            if t >= card_anim_end: card_t = 1.0
            slide_x = int(200*(1-card_t))
            card_y  = card_y_base + i*(card_h+20)
            card_a  = int(255*card_t)
            if card_a > 0:
                draw.rounded_rectangle(
                    [card_x+slide_x, card_y, card_x+card_w+slide_x, card_y+card_h],
                    radius=20,
                    fill=(*hex_rgb("#FFFFFF"), min(card_a//10, 20)),
                    outline=(*hex_rgb(accent_hex), min(card_a//4, 60)),
                    width=1)
                lbl_f = smart_font(label, 36)
                val_f = smart_font(value, 52, bold=True)
                draw_text(draw, (cx+slide_x, card_y+52), label, font=lbl_f, anchor="mm",
                          fill=(*hex_rgb(P["gray"]), card_a//2))
                draw_text(draw, (cx+slide_x, card_y+115), value, font=val_f, anchor="mm",
                          fill=(*hex_rgb(P["ivory"]), card_a))

        # Reveal text
        rev_y_start = card_y_base + 4*(card_h+20) + 40
        rev_anim_end = 0.70
        rev_prog = max(0.0, min(1.0, (t-0.50)/0.20))
        if t >= rev_anim_end: rev_prog = 1.0
        if rev_prog > 0 and reveal:
            draw_gold_divider(draw, cx, rev_y_start, w=700, alpha=int(200*rev_prog),
                              color=hex_rgb(accent_hex))
            rev_y = rev_y_start + 60
            lines = smart_wrap(reveal, 28, 20)
            for li, line in enumerate(lines):
                lf = smart_font(line, 48, bold=True)
                line_delay = li*0.12
                lt = max(0.0, min(1.0, (rev_prog-line_delay)/max(1.0-line_delay,0.001)))
                offset_y = int(60*(1-ease_out_cubic(lt)))
                animated_text(draw, cx, rev_y+offset_y, line, lf, hex_rgb(P["ivory"]), lt)
                rev_y += 75
        else:
            rev_y = rev_y_start + 60

        # CTA pill
        cta_anim_end = 0.88
        cta_t = ease_out_back(max(0.0, min(1.0, (t-0.75)/0.13)))
        if t >= cta_anim_end: cta_t = 1.0
        cta_y = max(rev_y_start+250, HEIGHT-300)
        if cta_t > 0:
            cta_bg = (*hex_rgb(accent_hex), int(220*cta_t))
            cta_f  = smart_font(cta_text, 36, bold=True)
            draw_pill_badge(draw, cx, cta_y,
                            cta_text[:45] + ("…" if len(cta_text) > 45 else ""),
                            cta_f, cta_bg,
                            (*hex_rgb(cv.get("badge_fg","#1A1A2E")), 255),
                            radius=30)

        # Bottom strip
        draw.rectangle([0, HEIGHT-100, WIDTH, HEIGHT],
                       fill=(*hex_rgb(P["maroon"]), 200))
        draw_text(draw, (cx, HEIGHT-50), "JyoteshAI  \u2022  Daily Vedic Astrology",
                  font=f_bottom, anchor="mm",
                  fill=(*hex_rgb(P["gold"]), 200))

        frames.append(alpha_paste(bg, img))
    return frames


# ─── TRANSITION ───────────────────────────────────────────────────────────────
def make_crossfade(frame_a, frame_b, n=12):
    result = []
    for i in range(n):
        t = i / max(n-1, 1)
        alpha = int(255*ease_in_out_sine(t))
        blend = Image.new("RGB", (WIDTH, HEIGHT))
        blend.paste(frame_a)
        overlay = frame_b.copy().convert("RGBA")
        overlay.putalpha(alpha)
        blend.paste(frame_b, mask=overlay.split()[3])
        result.append(blend)
    return result


# ─── FRAME SAVING ─────────────────────────────────────────────────────────────
def _save_frames(frames, frames_dir, counter):
    last = None
    for frame in frames:
        path = frames_dir / f"frame_{counter:05d}.jpg"
        frame.save(path, quality=94, optimize=True)
        last = frame
        counter += 1
    return counter, last


# ─── MAIN GENERATOR ───────────────────────────────────────────────────────────
def generate_all_frames(script, frames_dir: Path):
    """
    Render all slides and save frames to disk.
    Slide order: hook → body×N → extra (category-specific) → stats
    Returns frame count.
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    counter  = 0
    category = script.get("category", "horoscope")

    try:
        print("  Rendering hook slide ...", flush=True)
        hook_frames = create_hook_frames(script, duration_s=6)
        counter, last_frame = _save_frames(hook_frames, frames_dir, counter)
        del hook_frames

        body = script.get("body", [])
        for i in range(len(body)):
            print(f"  Rendering body slide {i+1} ...", flush=True)
            body_frames = create_body_frames(script, i, duration_s=6)
            fade = make_crossfade(last_frame, body_frames[0], n=12)
            counter, _ = _save_frames(fade, frames_dir, counter); del fade
            counter, last_frame = _save_frames(body_frames, frames_dir, counter)
            del body_frames

        # Extra slide (relationships, career, etc.)
        if category != "horoscope":
            print("  Rendering extra insight slide ...", flush=True)
            extra_frames = create_extra_frames(script, duration_s=6)
            if extra_frames:
                fade = make_crossfade(last_frame, extra_frames[0], n=12)
                counter, _ = _save_frames(fade, frames_dir, counter); del fade
                counter, last_frame = _save_frames(extra_frames, frames_dir, counter)
                del extra_frames

        print("  Rendering stats slide ...", flush=True)
        stats_frames = create_stats_frames(script, duration_s=8)
        fade = make_crossfade(last_frame, stats_frames[0], n=12)
        counter, _ = _save_frames(fade, frames_dir, counter); del fade
        counter, _ = _save_frames(stats_frames, frames_dir, counter)
        del stats_frames

    except Exception as e:
        print(f"\n  ❌ Error during frame generation: {e}")
        import traceback; traceback.print_exc()
        raise

    print(f"\n  Done: {counter} frames → {frames_dir}", flush=True)
    print(f"  Duration: ~{counter/FPS:.1f}s at {FPS} fps", flush=True)
    return counter


# ─── DEMO ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo = {
        "sign":          "Leo",
        "date":          "8 April 2026",
        "category":      "relationships",
        "lang":          "en",
        "hook":          "Someone you lost sleep over is thinking about you RIGHT NOW...",
        "body": [
            "The stars have positioned Venus directly in your love sector.",
            "An unresolved connection is about to resurface this week.",
            "Don't ignore the dreams — they're messages from the cosmos.",
            "Your heart knows what your mind is still processing.",
            "A conversation you've been avoiding could change everything.",
        ],
        "vibe_word":          "MAGNETIC",
        "lucky_number":       8,
        "lucky_color":        "Rose Gold",
        "reveal":             "The person you think about before sleeping? They feel it too.",
        "cta":                "Follow for daily love updates! Drop your sign below 👇",
        "compatibility_tip":  "A fire sign connection is heating up around you.",
        "warning":            "Don't mistake familiar comfort for genuine love.",
    }
    generate_all_frames(demo, Path("demo_frames_leo_relationships"))
