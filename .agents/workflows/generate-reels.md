---
description: How to generate and post daily horoscope reels on Windows
---

# Daily Horoscope Reel Workflow

## One-Time Setup (first time only)

1. Install Python from https://www.python.org/downloads/ — check "Add to PATH"
2. Install FFmpeg: `winget install Gyan.FFmpeg` or download from https://www.gyan.dev/ffmpeg/builds/
3. Double-click `setup_windows.bat` to create venv and install packages
4. Add your Gemini API key to the `.env` file
5. Drop a soothing soundtrack (mp3/wav) into the `soundtrack/` folder

## Daily Generation

// turbo
6. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

// turbo
7. Generate all 12 zodiac reels:
   ```powershell
   python Generate.py --sign all
   ```
   Or with your custom soundtrack:
   ```powershell
   python Generate.py --sign all --soundtrack soundtrack\your_track.mp3
   ```
   Or just double-click `generate_all.bat`

8. Wait ~15-25 minutes. Output appears in `reels_output/` folder.

## Posting to Instagram

9. Transfer videos from `reels_output/` to your phone (WhatsApp, OneDrive, USB)

10. Post 3-4 reels per day, spread across these time slots (IST):
    - Morning: 7:30 – 9:00 AM
    - Lunch: 12:30 – 2:00 PM
    - Evening: 5:30 – 7:00 PM
    - Night: 9:00 – 10:30 PM

11. Follow this 3-day rotation so every sign is covered:
    - Day 1: Aries, Taurus, Gemini, Cancer
    - Day 2: Leo, Virgo, Libra, Scorpio
    - Day 3: Sagittarius, Capricorn, Aquarius, Pisces

12. For captions, open the `_script.json` file next to each video — copy the "hook", "lucky_number", "lucky_color", and "vibe_word" values.

## Generate a Single Sign

// turbo
13. To generate just one sign:
    ```powershell
    python Generate.py --sign Aries
    ```
    Or double-click `generate_single.bat` and type the sign name.
