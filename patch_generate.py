"""
Patch Generate.py so the Gemini API call runs in a subprocess with a hard timeout.
This prevents the import of google.generativeai from hanging the main process.
"""

path = "Generate.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

start_marker = "def _make_fallback_script(sign: str, today: str)"
if start_marker not in content:
    # First run — old function still there
    start_marker = "def generate_horoscope_script(sign: str)"

end_marker = "\n# \u2500\u2500\u2500 AMBIENT AUDIO GENERATION"

start_idx = content.find(start_marker)
end_idx   = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f"ERROR: markers not found. start={start_idx}, end={end_idx}")
    exit(1)

new_function = '''def _make_fallback_script(sign, today):
    import random
    return {
        "hook": f"The stars have a MAJOR message for {sign} today...",
        "body": [
            "Something unexpected is coming your way.",
            "The universe has been preparing you for this moment.",
            "Don\'t ignore the signs around you right now.",
            "Your energy is at an all-time high this week.",
            "Someone from your past may reach out soon.",
        ],
        "reveal": f"The cosmos say: trust your instincts, {sign}. Big changes are near.",
        "cta": f"Follow for daily {sign} updates! Drop your sign below",
        "lucky_number": random.randint(1, 9),
        "lucky_color": random.choice(["gold", "saffron", "crimson", "ivory"]),
        "vibe_word": random.choice(["POWERFUL", "TRANSFORMATIVE", "MAGICAL", "INTENSE"]),
        "sign": sign,
        "date": today,
    }


def generate_horoscope_script(sign: str) -> dict:
    """
    Generate script via Gemini API in a separate subprocess with a 30s hard timeout.
    If the subprocess hangs or fails for any reason, falls back to the built-in script.
    """
    import subprocess, json, sys, random
    from datetime import datetime
    from pathlib import Path

    today = datetime.now().strftime("%B %d, %Y")

    # Build a self-contained script that does the API call and prints JSON result
    api_script = f\'\'\'
import os, json, sys
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
    print(json.dumps({{"error": "no_key"}}))
    sys.exit(0)
try:
    from google import genai
    client = genai.Client(api_key=api_key)
    prompt = (
        "You are a viral astrology content creator for Instagram Reels.\\n"
        "Create a 25-30 second horoscope reel script for {sign} for {today}.\\n\\n"
        "Return ONLY a valid JSON object with exactly these keys:\\n"
        "{{\\n"
        \\'  \\"hook\\": \\"opening line (1-2 sentences, very dramatic)\\",\\n\\'
        \\'  \\"body\\": [\\"line 1\\", \\"line 2\\", \\"line 3\\", \\"line 4\\", \\"line 5\\"],\\n\\'
        \\'  \\"reveal\\": \\"the big secret or main prediction (1-2 sentences)\\",\\n\\'
        \\'  \\"cta\\": \\"call to action at the end\\",\\n\\'
        \\'  \\"lucky_number\\": 7,\\n\\'
        \\'  \\"lucky_color\\": \\"gold\\",\\n\\'
        \\'  \\"vibe_word\\": \\"TRANSFORMATIVE\\"\\n\\'
        "}}\\n"
    )
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    data = json.loads(text)
    print(json.dumps(data))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
\'\'\'

    print(f"  Calling Gemini API (30s timeout)...")
    try:
        result = subprocess.run(
            [sys.executable, "-c", api_script],
            capture_output=True,
            text=True,
            timeout=35,   # hard OS-level kill after 35s
        )
        stdout = result.stdout.strip()
        if stdout:
            try:
                data = json.loads(stdout)
                if "error" in data:
                    print(f"  WARNING: API returned error ({data[\'error\']}) - using fallback script.")
                    return _make_fallback_script(sign, today)
                data["sign"] = sign
                data["date"] = today
                print(f"  Script generated OK via Gemini.")
                return data
            except json.JSONDecodeError:
                pass
        if result.returncode != 0 or result.stderr:
            print(f"  WARNING: API subprocess failed - using fallback script.")
    except subprocess.TimeoutExpired:
        print(f"  WARNING: Gemini API timed out after 35s - using fallback script.")
    except Exception as e:
        print(f"  WARNING: {e} - using fallback script.")

    return _make_fallback_script(sign, today)

'''

new_content = content[:start_idx] + new_function + content[end_idx:]
with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Patch applied successfully!")

import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax check: OK")
except py_compile.PyCompileError as e:
    print(f"Syntax ERROR: {e}")
