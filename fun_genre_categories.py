#!/usr/bin/env python3
"""
fun_genre_categories.py
───────────────────────
Three new "fun genre" content types that go beyond per-sign horoscopes.

Genres
──────
  name_initials  — "People whose name starts with A…"
                   Batched: subjects are LETTER GROUPS sharing a cosmic trait
                   e.g. ("A & J", "ABJ") — fire-starter letters
  lucky_month    — "If your birth month is May…"
                   Batched: related months grouped by seasonal energy
                   e.g. ("March & April", "MAR_APR")
  compatibility  — "Aries + Scorpio — what the cosmos really say…"
                   Subjects: 66 curated zodiac pairs

Each script schema:
  genre, subject, sign (slug for filename), hook, insights[], cta,
  vibe_word, + genre-specific extra keys
"""

import random
from datetime import datetime

# ─── ALL GENRES ───────────────────────────────────────────────────────────────

FUN_GENRES = ["name_initials", "lucky_month", "compatibility"]

# ─── SUBJECT LISTS ────────────────────────────────────────────────────────────

# name_initials — grouped because letters sharing energy generate better content
# (batched by numerological / phonetic vibe)
NAME_INITIAL_GROUPS = [
    # (display_label, slug, letters_list)
    ("A & J",  "AJ",  ["A", "J"]),      # 1 — pioneering, independent
    ("B & K",  "BK",  ["B", "K"]),      # 2 — diplomatic, emotional
    ("C & L",  "CL",  ["C", "L"]),      # 3 — expressive, social
    ("D & M",  "DM",  ["D", "M"]),      # 4 — hardworking, grounded
    ("E & N",  "EN",  ["E", "N"]),      # 5 — freedom-loving, restless
    ("F & O",  "FO",  ["F", "O"]),      # 6 — nurturing, responsible
    ("G & P",  "GP",  ["G", "P"]),      # 7 — introspective, wise
    ("H & Q",  "HQ",  ["H", "Q"]),      # 8 — ambitious, powerful
    ("I & R",  "IR",  ["I", "R"]),      # 9 — compassionate, old-soul
    ("S & T",  "ST",  ["S", "T"]),      # strong-willed, intense
    ("U & V",  "UV",  ["U", "V"]),      # visionary, unique
    ("W & X",  "WX",  ["W", "X"]),      # unconventional, wild-card
    ("Y & Z",  "YZ",  ["Y", "Z"]),      # rare, deep thinkers
]

# lucky_month — grouped by real astrological season / elemental energy
LUCKY_MONTH_GROUPS = [
    # (display_label, slug, months_list)
    ("January & February", "JAN_FEB", ["January", "February"]),   # Capricorn/Aquarius — discipline & vision
    ("March & April",      "MAR_APR", ["March", "April"]),         # Pisces/Aries — endings into new beginnings
    ("May & June",         "MAY_JUN", ["May", "June"]),            # Taurus/Gemini — earth meets air, stability & spark
    ("July & August",      "JUL_AUG", ["July", "August"]),         # Cancer/Leo — feeling & shining
    ("September & October","SEP_OCT", ["September", "October"]),   # Virgo/Libra — refinement & balance
    ("November & December","NOV_DEC", ["November", "December"]),   # Scorpio/Sagittarius — depth & expansion
]

# compatibility — all 66 unique zodiac pairs
_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

def _all_compatibility_pairs():
    pairs = []
    for i, a in enumerate(_SIGNS):
        for b in _SIGNS[i+1:]:
            label   = f"{a} & {b}"
            slug    = f"{a[:3].upper()}_{b[:3].upper()}"
            pairs.append((label, slug, a, b))
    return pairs

COMPATIBILITY_PAIRS = _all_compatibility_pairs()   # 66 entries

# ─── VISUAL CONFIGS ───────────────────────────────────────────────────────────

FUN_GENRE_VISUAL = {
    "name_initials": {
        "accent":    "#C084FC",   # violet-purple  — mystical personality energy
        "tint":      "#1A0830",   # deep violet bg
        "label":     "NAME ENERGY",
        "badge_bg":  "#C084FC",
        "badge_fg":  "#1A1A2E",
        "particle":  "#C084FC",
        "hero_bg":   "#2D1B4E",   # hero letter circle bg
        "hero_fg":   "#C084FC",
    },
    "lucky_month": {
        "accent":    "#34D399",   # emerald green  — seasonal growth
        "tint":      "#062010",
        "label":     "BIRTH MONTH",
        "badge_bg":  "#34D399",
        "badge_fg":  "#0D1F16",
        "particle":  "#34D399",
        "hero_bg":   "#0F3D2A",
        "hero_fg":   "#34D399",
    },
    "compatibility": {
        "accent":    "#FB923C",   # warm orange    — the heat of two energies colliding
        "tint":      "#200800",
        "label":     "COMPATIBILITY",
        "badge_bg":  "#FB923C",
        "badge_fg":  "#1A0A00",
        "particle":  "#FB923C",
        "hero_bg":   "#3D1500",
        "hero_fg":   "#FB923C",
    },
}

# ─── PROMPT TEMPLATES ─────────────────────────────────────────────────────────

def get_genre_prompt(genre: str, subject_label: str, extra: dict, today: str) -> str:
    """Build NVIDIA API prompt for a given genre + subject."""
    if genre == "name_initials":
        return _prompt_name_initials(subject_label, extra["letters"], today)
    if genre == "lucky_month":
        return _prompt_lucky_month(subject_label, extra["months"], today)
    if genre == "compatibility":
        return _prompt_compatibility(subject_label, extra["sign_a"], extra["sign_b"], today)
    raise ValueError(f"Unknown genre: {genre}")


def _prompt_name_initials(label: str, letters: list, today: str) -> str:
    letters_str = " and ".join(letters)
    return f"""
You are a viral astrology and numerology content creator for Instagram Reels. Today is {today}.

Create shareable, emotionally resonant content for people whose name starts with {letters_str}.
These letters share the same numerological vibration and cosmic energy.

Return ONLY a valid JSON object with EXACTLY this structure — no markdown, no explanation:
{{
  "hook": "2-sentence DRAMATIC opening for people whose name starts with {label}. Make it feel like a personal whisper.",
  "insights": [
    "powerful personality truth about {letters_str} name people",
    "their hidden strength or superpower",
    "a cosmic warning or challenge they face",
    "what the universe is saying to them RIGHT NOW",
    "their love/relationship dynamic in one sentence"
  ],
  "personality_trait": "their defining trait in 1 punchy sentence",
  "lucky_pairing": "the letter initial they match best with (name compatibility hint)",
  "lucky_number": <integer 1-9>,
  "lucky_color": "<one vivid color>",
  "vibe_word": "<ONE word in ALL CAPS that captures their energy>",
  "cta": "call to action — ask viewer to share with their {label} friend"
}}
"""


def _prompt_lucky_month(label: str, months: list, today: str) -> str:
    months_str = " and ".join(months)
    signs_hint = {
        "January": "Capricorn/Aquarius",  "February": "Aquarius/Pisces",
        "March":   "Pisces/Aries",        "April":    "Aries/Taurus",
        "May":     "Taurus/Gemini",       "June":     "Gemini/Cancer",
        "July":    "Cancer/Leo",          "August":   "Leo/Virgo",
        "September":"Virgo/Libra",        "October":  "Libra/Scorpio",
        "November": "Scorpio/Sagittarius","December": "Sagittarius/Capricorn",
    }
    sign_hint = " / ".join(signs_hint.get(m, "") for m in months if m in signs_hint)
    return f"""
You are a viral astrology content creator for Instagram Reels. Today is {today}.

Create shareable content for people born in {months_str} ({sign_hint} energy).
These birth months share the same seasonal and astrological vibration.

Return ONLY a valid JSON object with EXACTLY this structure — no markdown, no explanation:
{{
  "hook": "2-sentence DRAMATIC opening for people born in {label}. Ultra personal.",
  "insights": [
    "core personality truth about {months_str} babies",
    "their unique gift or superpower",
    "the challenge they always face",
    "what 2025/2026 holds specifically for this birth month",
    "their relationship / love pattern"
  ],
  "power_period": "their BEST upcoming date range this year (e.g. 'April 20 – May 10')",
  "cosmic_message": "a one-sentence cosmic message just for them right now",
  "lucky_number": <integer 1-9>,
  "lucky_color": "<one vivid color>",
  "vibe_word": "<ONE word in ALL CAPS that captures their birth energy>",
  "cta": "ask viewer to tag their {months_str} person or drop their birth month below"
}}
"""


def _prompt_compatibility(label: str, sign_a: str, sign_b: str, today: str) -> str:
    return f"""
You are a viral astrology compatibility expert creating Instagram Reels. Today is {today}.

Create explosive, shareable compatibility content for {sign_a} + {sign_b}.
This should feel like inside gossip — like you KNOW these two signs personally.

Return ONLY a valid JSON object with EXACTLY this structure — no markdown, no explanation:
{{
  "hook": "2-sentence DRAMATIC opening about {sign_a} and {sign_b} together. Pure drama.",
  "insights": [
    "what happens when {sign_a} and {sign_b} first meet",
    "their biggest relationship strength",
    "their most explosive conflict point",
    "how they act in love vs. friendship",
    "the unspoken thing between them"
  ],
  "compatibility_score": "<X/10>",
  "chemistry": "one dramatic sentence about their physical/emotional chemistry",
  "verdict": "final verdict — are they soulmates, situationships, or disasters?",
  "lucky_number": <integer 1-9>,
  "lucky_color": "<a color that represents their union>",
  "vibe_word": "<ONE word in ALL CAPS describing their combined energy>",
  "cta": "ask viewer to tag their {sign_a} or {sign_b} person"
}}
"""

# ─── FALLBACK SCRIPTS ─────────────────────────────────────────────────────────

def make_genre_fallback(genre: str, subject_label: str, extra: dict) -> dict:
    """Offline fallback script for any genre + subject."""
    n  = random.randint(1, 9)
    col = random.choice(["gold", "violet", "emerald", "amber", "rose"])
    vibe = random.choice(["MAGNETIC", "POWERFUL", "ELECTRIC", "RARE", "COSMIC"])
    base = {
        "genre":       genre,
        "subject":     subject_label,
        "lang":        "en",
        "lucky_number": n,
        "lucky_color":  col,
        "vibe_word":    vibe,
        "date":        datetime.now().strftime("%B %d, %Y"),
    }
    base.update(extra)   # inject sign_a/sign_b, letters, months etc.

    if genre == "name_initials":
        letters = extra.get("letters", [subject_label])
        letters_str = " & ".join(letters)
        base.update({
            "hook": f"If your name starts with {letters_str}, the universe has been waiting to tell you something...",
            "insights": [
                f"{letters_str} names carry an energy most people can't handle.",
                "You were built for pressure — and you thrive when others crumble.",
                "Your biggest challenge? Trusting your own instincts.",
                "Right now the cosmos is clearing the path ahead of you.",
                "You love fiercely, but rarely let anyone fully in.",
            ],
            "personality_trait": f"Natural intensity wrapped in a calm exterior.",
            "lucky_pairing": f"Names starting with {'S' if letters[0] < 'M' else 'A'}",
            "cta": f"Tag your {letters_str} friend — they NEED to see this! 👇",
        })
    elif genre == "lucky_month":
        months = extra.get("months", [subject_label])
        months_str = " & ".join(months)
        base.update({
            "hook": f"If you were born in {months_str}, this message was written for you...",
            "insights": [
                f"{months_str} babies carry an ancient wisdom in their bones.",
                "Your emotional depth is your greatest superpower.",
                "The challenge you keep facing? It's actually your greatest teacher.",
                "2025 is shifting something major in your personal timeline.",
                "You love with your whole heart — and that is both your gift and your wound.",
            ],
            "power_period": "May 1 – June 15",
            "cosmic_message": "The universe is asking you to stop playing small.",
            "cta": f"Tag your {months_str} person — do they know this? 👇",
        })
    elif genre == "compatibility":
        sign_a = extra.get("sign_a", "Aries")
        sign_b = extra.get("sign_b", "Scorpio")
        base.update({
            "hook": f"{sign_a} and {sign_b} together? The stars have a LOT to say about this...",
            "insights": [
                f"When {sign_a} and {sign_b} meet, the chemistry is undeniable.",
                f"{sign_a} brings the spark — {sign_b} brings the depth.",
                "Their biggest argument? Control — and who gets to have it.",
                "In love they're magnetic. As friends they're unstoppable.",
                "There's always one conversation they never fully finish.",
            ],
            "compatibility_score": f"{random.randint(6, 9)}/10",
            "chemistry": f"Intense, consuming, impossible to ignore.",
            "verdict": f"A relationship that changes both of them forever.",
            "cta": f"Tag your {sign_a} or {sign_b} — do they agree? 👇",
        })

    return base


# ─── SUBJECT REGISTRY ─────────────────────────────────────────────────────────
# Maps slug → (display_label, extra_dict) for each genre

def get_all_subjects(genre: str) -> list[tuple]:
    """
    Returns list of (slug, display_label, extra_dict) for every subject in a genre.
    extra_dict contains the genre-specific fields passed to prompts and fallbacks.
    """
    if genre == "name_initials":
        return [
            (slug, label, {"letters": letters, "sign": f"INITIAL_{slug}"})
            for label, slug, letters in NAME_INITIAL_GROUPS
        ]
    if genre == "lucky_month":
        return [
            (slug, label, {"months": months, "sign": f"MONTH_{slug}"})
            for label, slug, months in LUCKY_MONTH_GROUPS
        ]
    if genre == "compatibility":
        return [
            (slug, label, {"sign_a": sign_a, "sign_b": sign_b, "sign": f"COMPAT_{slug}"})
            for label, slug, sign_a, sign_b in COMPATIBILITY_PAIRS
        ]
    raise ValueError(f"Unknown genre: {genre}")


def get_subject(genre: str, slug: str) -> tuple:
    """Return (slug, display_label, extra_dict) for a specific subject slug."""
    for s in get_all_subjects(genre):
        if s[0].lower() == slug.lower():
            return s
    raise ValueError(f"Subject '{slug}' not found in genre '{genre}'")


# ─── DISPLAY NAMES ────────────────────────────────────────────────────────────

GENRE_DISPLAY = {
    "name_initials":  "NAME ENERGY",
    "lucky_month":    "BIRTH MONTH",
    "compatibility":  "COMPATIBILITY",
}
