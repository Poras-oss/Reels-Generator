#!/usr/bin/env python3
"""
content_categories.py
─────────────────────
Viral content category definitions for the Reel Generator.

5 Categories:
  • relationships   — emotionally personal, longing/hope/fear
  • career          — ambition, anxiety, validation
  • current_events  — astrological framing of macro themes
  • emotional_healing — catharsis, self-love, inner wounds
  • manifestation   — law of attraction, "universe delivering"

Each category has:
  - PROMPT_TEMPLATE  : Gemini prompt (EN + HI in one call)
  - FALLBACK_EN      : English fallback script (dict)
  - FALLBACK_HI      : Hindi fallback script (dict)
  - VISUAL           : Color overrides + category icon for frames
"""

import random
from datetime import datetime

# ─── ALL CATEGORY NAMES ──────────────────────────────────────────────────────

ALL_CATEGORIES = [
    "relationships",
    "career",
    "current_events",
    "emotional_healing",
    "manifestation",
]

# ─── VISUAL CONFIGS ───────────────────────────────────────────────────────────
# Each has: accent_color, tint_color, icon, label, particle_color

CATEGORY_VISUAL = {
    "relationships": {
        "accent":        "#E63C6E",   # rose pink
        "tint":          "#4A1030",   # deep rose bg tint
        "icon":          "LOVE",
        "label":         "RELATIONSHIPS",
        "particle":      "#E63C6E",
        "badge_bg":      "#E63C6E",
        "badge_fg":      "#FFFFFF",
    },
    "career": {
        "accent":        "#1E90FF",   # electric blue
        "tint":          "#0A1628",   # deep navy bg tint
        "icon":          "CAREER",
        "label":         "CAREER & MONEY",
        "particle":      "#F5C518",
        "badge_bg":      "#1E90FF",
        "badge_fg":      "#FFFFFF",
    },
    "current_events": {
        "accent":        "#FF6B00",   # saffron (urgency)
        "tint":          "#1A1000",   # dark amber bg tint
        "icon":          "ALERT",
        "label":         "COSMIC NEWS",
        "particle":      "#FF6B00",
        "badge_bg":      "#FF6B00",
        "badge_fg":      "#1A1A2E",
    },
    "emotional_healing": {
        "accent":        "#9B59B6",   # soft purple
        "tint":          "#1A0A2E",   # deep violet bg tint
        "icon":          "HEAL",
        "label":         "HEALING",
        "particle":      "#9B59B6",
        "badge_bg":      "#9B59B6",
        "badge_fg":      "#FFFFFF",
    },
    "manifestation": {
        "accent":        "#F5C518",   # gold
        "tint":          "#0D0A00",   # almost black gold bg tint
        "icon":          "MANIFEST",
        "label":         "MANIFESTATION",
        "particle":      "#F5C518",
        "badge_bg":      "#F5C518",
        "badge_fg":      "#1A1A2E",
    },
}

# ─── GEMINI PROMPTS ───────────────────────────────────────────────────────────

def get_prompt(sign: str, category: str, today: str) -> str:
    """Return a bilingual Gemini prompt for the given sign + category."""
    base_instructions = f"""
You are a viral astrology content creator for Instagram Reels. Today is {today}.
Create content for {sign}.

Return ONLY a valid JSON object with EXACTLY this structure — no markdown, no explanation:
{{
  "en": {{
    "hook": "opening line (1-2 sentences, VERY dramatic and personal)",
    "body": ["line 1", "line 2", "line 3", "line 4", "line 5"],
    "reveal": "the big secret / main prediction (1-2 sentences)",
    "cta": "call to action",
    "lucky_number": <integer 1-9>,
    "lucky_color": "<color name>",
    "vibe_word": "<ONE WORD in CAPS>",
    {category_extra_en(category)}
  }},
  "hi": {{
    "hook": "<same hook in simple spoken Hindi — Devanagari script>",
    "body": ["<line 1 in Hindi>", "<line 2>", "<line 3>", "<line 4>", "<line 5>"],
    "reveal": "<reveal in Hindi>",
    "cta": "<cta in Hindi>",
    "lucky_number": <same integer>,
    "lucky_color": "<simple color name in Hindi>",
    "vibe_word": "<ONE short simple Hindi word in Devanagari>",
    {category_extra_hi(category)}
  }}
}}

Important Hindi writing rules:
- Use very simple spoken Hindi used in daily life and on Instagram.
- Sound like a close friend talking, not a formal writer or poet.
- Keep Hindi lines short, natural, and easy to read.
- Do NOT use very formal or Sanskrit-heavy words.
- Avoid hard words like: "स्वीकार", "परिष्कृत", "आवश्यक", "आकर्षित", "दृष्टि", "अंतर्ज्ञान", "ब्रह्मांडीय".
- Avoid difficult conjunct-heavy words and complicated spellings when a simpler everyday alternative exists.
- Prefer simple words like: "दिल", "नया", "सही", "पास", "काम", "पैसा", "फोकस", "मूड", "संकेत", "जरूरी".
- You may use light everyday Hinglish in Devanagari if it sounds more natural, like "फोकस", "मूड", "लकी", "साइन".
- Hindi must feel natural and conversational, not like a literal translation of the English text.
"""
    return base_instructions + CATEGORY_PROMPTS[category].format(sign=sign, today=today)


def category_extra_en(category: str) -> str:
    extras = {
        "relationships":     '"compatibility_tip": "<1 sentence compatibility insight>", "warning": "<relationship red flag>"',
        "career":            '"power_move": "<1 bold career action to take today>", "avoid": "<what to avoid>"',
        "current_events":    '"cosmic_headline": "<punchy astrological headline>", "action_now": "<what to do right now>"',
        "emotional_healing": '"wound_theme": "<the emotional wound being addressed>", "affirmation": "<a 1-sentence healing affirmation>"',
        "manifestation":     '"manifestation_code": "<a number or symbol>", "ritual": "<a simple manifestation ritual>"',
    }
    return extras.get(category, '"extra": ""')


def category_extra_hi(category: str) -> str:
    extras = {
        "relationships":     '"compatibility_tip": "<Hindi>", "warning": "<Hindi>"',
        "career":            '"power_move": "<Hindi>", "avoid": "<Hindi>"',
        "current_events":    '"cosmic_headline": "<Hindi>", "action_now": "<Hindi>"',
        "emotional_healing": '"wound_theme": "<Hindi>", "affirmation": "<Hindi>"',
        "manifestation":     '"manifestation_code": "<number/symbol>", "ritual": "<Hindi>"',
    }
    return extras.get(category, '"extra": ""')


CATEGORY_PROMPTS = {

    "relationships": """
Category: RELATIONSHIPS & LOVE
Make this feel DEEPLY personal — like you're reading their diary.
Touch these themes: unresolved feelings, who's thinking about them,
a love opportunity they're missing, a person from the past returning.
Use emotionally charged language. Make them feel seen and understood.
The hook must feel like a secret being whispered to them specifically.
Sign: {sign}. If in a relationship, speak to deepening bonds.
Include whether someone specific is thinking about {sign} right now.
""",

    "career": """
Category: CAREER, MONEY & AMBITION
Make this feel like insider knowledge — like you know EXACTLY why
their boss doesn't notice them, or why their side hustle is stuck.
Touch these themes: financial breakthrough incoming, promotion energy,
hidden enemies at work, the one move that changes everything.
Be specific about timeline (this week, within 30 days, etc.).
The {sign} person should feel like this was made exactly for them.
Include a "power move" — one bold action they can take TODAY.
Sign: {sign}.
""",

    "current_events": """
Category: CURRENT EVENTS & COSMIC TIMING
Frame current global themes (economy uncertainty, major life changes,
tech disruptions, relationship dynamics in 2025) through an astrological lens.
Connect Saturn's position, Mercury retrograde (if relevant for {today}),
and current planetary energy to what {sign} is experiencing RIGHT NOW.
Make it feel URGENT — like the timing is cosmic and not coincidental.
The headline should feel like breaking news from the stars.
Sign: {sign}. Make the cosmic timing feel directly relevant to their daily life.
""",

    "emotional_healing": """
Category: EMOTIONAL HEALING & INNER WORK
This should make them cry (in a good way). Touch their deepest wounds.
Address themes like: childhood trauma effects on adult relationships,
patterns they can't break, grief they haven't processed,
the moment they stopped trusting themselves — and why NOW is different.
Make them feel SEEN, VALIDATED, and HOPEFUL.
The reveal should feel like a breakthrough realization.
Use gentle but powerful language. This is deeply personal.
Sign: {sign}. Address the specific emotional wound common to this sign.
""",

    "manifestation": """
Category: MANIFESTATION & LAW OF ATTRACTION
Make this feel like cosmic confirmation — that what they've been
dreaming about is ALREADY on its way.
Touch these themes: their specific desire being close to manifesting,
why it has been delayed (and why the delay was necessary),
the one belief blocking them, a ritual to unblock it NOW.
Reference 11:11, angel numbers, or specific manifestation codes.
Create a sense of magical urgency — the universe is RESPONDING.
Sign: {sign}. Make them feel like the stars are sending them a direct sign.
""",
}


# ─── FALLBACK SCRIPTS ─────────────────────────────────────────────────────────

def make_fallback(sign: str, category: str, lang: str) -> dict:
    today = datetime.now().strftime("%B %d, %Y")
    n = random.randint(1, 9)
    col_en = random.choice(["gold", "amber", "crimson", "violet", "emerald"])
    col_hi = {"gold": "सुनहरा", "amber": "पीला", "crimson": "लाल", "violet": "बैंगनी", "emerald": "हरा"}.get(col_en, "सुनहरा")
    vibe_en = random.choice(["TRANSFORMATIVE", "POWERFUL", "MAGNETIC", "INTENSE", "ELECTRIC"])
    vibe_hi = {"TRANSFORMATIVE": "नया", "POWERFUL": "दमदार",
               "MAGNETIC": "खास", "INTENSE": "तेज", "ELECTRIC": "जोरदार"}.get(vibe_en, "दमदार")

    if lang == "en":
        base = {
            "hook":         f"The stars just revealed something urgent for {sign}...",
            "body":         [
                "Something unexpected is shifting in your energy right now.",
                "The universe has been preparing you for this exact moment.",
                "Don't ignore the signs appearing in your daily life.",
                "Your intuition is stronger than you realize.",
                "A major change is already in motion.",
            ],
            "reveal":       f"Trust the process, {sign}. What you've been waiting for is closer than you think.",
            "cta":          f"Follow for daily {sign} updates! Drop your sign below 👇",
            "lucky_number": n,
            "lucky_color":  col_en,
            "vibe_word":    vibe_en,
            "sign":         sign,
            "date":         today,
            "category":     category,
            "lang":         "en",
        }
        extras = _fallback_extras_en(sign, category)
    else:  # Hindi
        base = {
            "hook":         f"आज {sign} के लिए एक खास इशारा है...",
            "body":         [
                "आज कुछ बड़ा बदल सकता है।",
                "दिल जो कह रहा है, उसे सुनो।",
                "एक मौका चुपचाप पास आ रहा है।",
                "सही लोग अब आपके करीब आ सकते हैं।",
                "जल्दबाज़ी नहीं, साफ सोच रखो।",
            ],
            "reveal":       f"भरोसा रखो, {sign}. जिस बात का इंतज़ार था, उसका समय अब पास है।",
            "cta":          f"रोज के {sign} अपडेट के लिए फॉलो करें 👇",
            "lucky_number": n,
            "lucky_color":  col_hi,
            "vibe_word":    vibe_hi,
            "sign":         sign,
            "date":         today,
            "category":     category,
            "lang":         "hi",
        }
        extras = _fallback_extras_hi(sign, category)

    base.update(extras)
    return base


def _fallback_extras_en(sign, category):
    extras_map = {
        "relationships":     {"compatibility_tip": "An unexpected connection is forming.", "warning": "Don't ignore your gut feeling about someone new."},
        "career":            {"power_move": "Reach out to one person who can open a door for you today.", "avoid": "Avoid making major financial decisions before Friday."},
        "current_events":    {"cosmic_headline": f"BREAKING: Cosmic shift puts {sign} at the center of change.", "action_now": "Write down your top three priorities — the universe is listening."},
        "emotional_healing": {"wound_theme": "Old patterns are ready to be released.", "affirmation": "I release what no longer serves my highest good."},
        "manifestation":     {"manifestation_code": "1111", "ritual": "Write your desire on paper, hold it to your heart, and release it to the universe."},
    }
    return extras_map.get(category, {})


def _fallback_extras_hi(sign, category):
    extras_map = {
        "relationships":     {"compatibility_tip": "किसी शांत इंसान से बात जम सकती है।", "warning": "पुरानी बात पर फिर मत अटकना।"},
        "career":            {"power_move": "आज एक साफ मैसेज या कॉल कर दो।", "avoid": "गुस्से में जवाब मत देना।"},
        "current_events":    {"cosmic_headline": f"आज का इशारा: {sign} के लिए बदलने वाला दिन।", "action_now": "एक काम चुनो और उसी पर फोकस रखो।"},
        "emotional_healing": {"wound_theme": "पुरानी चोट अब छोड़नी है।", "affirmation": "मैं खुद को पहले रखता/रखती हूँ।"},
        "manifestation":     {"manifestation_code": "1111", "ritual": "अपनी इच्छा लिखो, 11 बार पढ़ो, फिर छोड़ दो।"},
    }
    return extras_map.get(category, {})


# ─── CATEGORY DISPLAY NAMES ───────────────────────────────────────────────────

CATEGORY_DISPLAY = {
    "relationships":     "RELATIONSHIPS",
    "career":            "CAREER",
    "current_events":    "COSMIC NEWS",
    "emotional_healing": "HEALING",
    "manifestation":     "MANIFESTATION",
}

CATEGORY_DISPLAY_HI = {
    "relationships":     "लव",
    "career":            "काम",
    "current_events":    "आज की खबर",
    "emotional_healing": "दिल की बात",
    "manifestation":     "मनचाहा",
}
