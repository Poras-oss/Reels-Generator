# 🔮 Jyotesh AI — Windows Setup & Daily Workflow Guide

> **This guide is for running the reel generator 100% locally on your Windows PC.**
> No cloud, no server, no cron jobs. Just double-click and post.

---

## 📋 Table of Contents

1. [What You Need to Download](#1--what-you-need-to-download)
2. [One-Time Setup](#2--one-time-setup)
3. [Your Soundtrack](#3--your-soundtrack)
4. [Daily Workflow — Step by Step](#4--daily-workflow--step-by-step)
5. [Posting Schedule & Strategy](#5--posting-schedule--strategy)
6. [Command Reference](#6--command-reference)
7. [Folder Structure](#7--folder-structure)
8. [Troubleshooting](#8--troubleshooting)

---

## 1. 📥 What You Need to Download

| # | Software | Download Link | Why You Need It |
|---|----------|---------------|-----------------|
| 1 | **Python 3.10+** | [python.org/downloads](https://www.python.org/downloads/) | Runs the generator script |
| 2 | **FFmpeg** | [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) | Assembles frames + audio into MP4 video |
| 3 | **Gemini API Key** | [aistudio.google.com/apikey](https://aistudio.google.com/app/apikey) | AI generates the horoscope script text |

### Installing Python
1. Download the installer from the link above
2. **⚠️ IMPORTANT:** Check the box **"Add Python to PATH"** at the bottom of the installer
3. Click "Install Now"
4. Verify: Open Command Prompt and type `python --version`

### Installing FFmpeg (the easy way)
1. Go to [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
2. Download **"ffmpeg-release-essentials.zip"** (under "Release builds")
3. Extract the zip — you'll get a folder like `ffmpeg-7.x-essentials_build`
4. Inside it, find the `bin` folder (contains `ffmpeg.exe`)
5. **Add to PATH:**
   - Press `Win + S`, search for **"Environment Variables"**
   - Click **"Edit the system environment variables"**
   - Click **"Environment Variables..."** button
   - Under **"User variables"**, select `Path` → click **Edit**
   - Click **New** → paste the full path to the `bin` folder
     (e.g., `C:\Users\YourName\Downloads\ffmpeg-7.1-essentials_build\bin`)
   - Click OK → OK → OK
6. **Verify:** Open a NEW Command Prompt and type `ffmpeg -version`

> **Alternative (simpler):** If you have `winget`, just run:
> ```
> winget install Gyan.FFmpeg
> ```

---

## 2. 🛠️ One-Time Setup

### Option A: Double-Click Setup (Easiest)
1. Double-click **`setup_windows.bat`**
2. It will create a virtual environment and install all Python packages
3. Done!

### Option B: Manual Setup
Open PowerShell in the project folder and run:
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Set Your Gemini API Key
Your `.env` file already exists. Make sure it has your key:
```
GEMINI_API_KEY=your_actual_key_here
```
Get a free key at: [aistudio.google.com/apikey](https://aistudio.google.com/app/apikey)

---

## 3. 🎵 Your Soundtrack

The `soundtrack/` folder is ready for you. Just drop in any calm, soothing audio file.

**Supported formats:** `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`

**Where to download free soothing music:**

| Source | Link | License |
|--------|------|---------|
| Pixabay Music | [pixabay.com/music](https://pixabay.com/music/) | Free, no attribution needed |
| Freesound | [freesound.org](https://freesound.org/) | Creative Commons |
| Incompetech | [incompetech.com](https://incompetech.com/) | Free with attribution |

**Search terms:** "meditation ambient", "sitar calm", "lo-fi spiritual", "vedic chant background", "singing bowl ambient"

**How it works:**
- Drop your `.mp3` or `.wav` file into the `soundtrack/` folder
- The script automatically picks it up and mixes it under the ambient drone
- The drone plays at 70% volume, your soundtrack at 35% — so it's truly *background*
- If no file is found, it just uses the generated ambient drone (still sounds great)

---

## 4. 📅 Daily Workflow — Step by Step

### The Quick Version (2 minutes)

```
1. Double-click  generate_all.bat     → makes 12 reels
2. Open          reels_output/        → find your MP4 files
3. Upload to     Instagram manually   → post 3-4 per day
```

### The Detailed Version

#### Morning Routine (do this once a day)

**Step 1 — Generate Reels** (~15-25 minutes for all 12)
- Double-click **`generate_all.bat`**
- OR open PowerShell and run:
  ```powershell
  .\venv\Scripts\Activate.ps1
  python Generate.py --sign all
  ```
- Wait for it to finish. You'll see a summary of all 12 reels.

**Step 2 — Review Output**
- Open `reels_output/` folder
- You'll find files like:
  ```
  aries_20260408_reel.mp4
  taurus_20260408_reel.mp4
  gemini_20260408_reel.mp4
  ...etc...
  ```
- Each video is ~1-2 MB, Instagram-ready (1080x1920, 9:16)

**Step 3 — Transfer to Phone**
- **Quick:** Use WhatsApp Web — send videos to "Saved Messages" or your own group
- **Quick:** Use Telegram — send to "Saved Messages"
- **OneDrive:** Your project is already on OneDrive! Access from phone
- **USB Cable:** Drag and drop to phone

**Step 4 — Post to Instagram**
- Open Instagram → Tap `+` → Select **Reel**
- Select your video → Add caption (see [Posting Schedule](#5--posting-schedule--strategy) below)
- Post!

#### Want Just One Sign?
```powershell
# Double-click generate_single.bat and type the sign name
# OR run directly:
python Generate.py --sign Leo
python Generate.py --sign Scorpio --soundtrack soundtrack\calm.mp3
```

---

## 5. 📊 Posting Schedule & Strategy

### ❌ DON'T: Post All 12 at Once
Instagram's algorithm will flag you as spam. Followers get annoyed seeing 12 notifications.

### ✅ DO: Spread Them Across the Day

#### Recommended: 3-4 Reels Per Day (Rotation)

| Day | Morning (8 AM) | Afternoon (1 PM) | Evening (6 PM) | Night (9 PM) |
|-----|----------------|-------------------|-----------------|---------------|
| **Mon** | ♈ Aries | ♉ Taurus | ♊ Gemini | ♋ Cancer |
| **Tue** | ♌ Leo | ♍ Virgo | ♎ Libra | ♏ Scorpio |
| **Wed** | ♐ Sagittarius | ♑ Capricorn | ♒ Aquarius | ♓ Pisces |
| **Thu** | ♈ Aries | ♉ Taurus | ♊ Gemini | ♋ Cancer |
| **Fri** | ♌ Leo | ♍ Virgo | ♎ Libra | ♏ Scorpio |
| **Sat** | ♐ Sagittarius | ♑ Capricorn | ♒ Aquarius | ♓ Pisces |
| **Sun** | 🌟 Weekly Wrap | 🔥 Fire Signs | 🌍 Earth Signs | 💧 Water+Air |

> **Every sign gets covered every 3 days.** On Sunday, you can do combined "element" posts.

### Best Posting Times (IST — India)

| Time Slot | IST | Why It Works |
|-----------|-----|--------------|
| Morning | 7:30 – 9:00 AM | People check phones first thing |
| Lunch | 12:30 – 2:00 PM | Lunch-break scrolling |
| Evening | 5:30 – 7:00 PM | Post-work relaxation |
| Night | 9:00 – 10:30 PM | Peak Instagram usage in India |

### Caption Template
```
🔮 {Sign} Daily Horoscope — {Date}

{Paste the "hook" from the script JSON}

✨ Lucky Number: {number}
🎨 Power Color: {color}
⚡ Today's Vibe: {vibe_word}

👇 Drop your sign in the comments!
💫 Follow @jyoteshai for daily cosmic updates

#Horoscope #Astrology #{Sign} #DailyHoroscope
#ZodiacSigns #Jyotish #VedicAstrology
#Aries #Taurus #Gemini #Cancer #Leo #Virgo
#Libra #Scorpio #Sagittarius #Capricorn #Aquarius #Pisces
```

> **Tip:** The script saves a `_script.json` file for each reel — open it to copy the hook text and lucky numbers for your caption!

---

## 6. 💻 Command Reference

All commands should be run from the project folder in PowerShell/CMD.

| What | Command |
|------|---------|
| **Setup (first time)** | Double-click `setup_windows.bat` |
| **Generate all 12** | Double-click `generate_all.bat` |
| **Generate one sign** | `python Generate.py --sign Aries` |
| **Generate random** | `python Generate.py` |
| **With soundtrack** | `python Generate.py --sign Leo --soundtrack soundtrack\calm.mp3` |
| **All signs + soundtrack** | `python Generate.py --sign all --soundtrack soundtrack\music.mp3` |
| **Custom output folder** | `python Generate.py --sign all --output my_reels` |

---

## 7. 📁 Folder Structure

```
Reels Generator/
├── .env                          ← Your Gemini API key (keep secret!)
├── Generate.py                   ← Main script — generates everything
├── frame_generator.py            ← Creates animated video frames
├── requirements.txt              ← Python dependencies
│
├── setup_windows.bat             ← Run ONCE to set up
├── generate_all.bat              ← Double-click → all 12 reels
├── generate_single.bat           ← Double-click → one reel (asks for sign)
│
├── soundtrack/                   ← DROP YOUR MUSIC HERE
│   └── README.txt                ← Instructions for soundtrack
│
├── reels_output/                 ← YOUR GENERATED VIDEOS APPEAR HERE
│   ├── aries_20260408_reel.mp4
│   ├── aries_20260408_script.json
│   ├── aries_20260408_ambient.wav
│   └── frames/                   ← Individual frame images (OK to delete)
│
└── WINDOWS_SETUP_AND_WORKFLOW.md ← This file!
```

---

## 8. 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `python is not recognized` | Reinstall Python and check "Add to PATH" |
| `ffmpeg is not recognized` | Add ffmpeg `bin` folder to your system PATH (see Section 1) |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside the venv |
| `GEMINI_API_KEY` error | Check your `.env` file has the correct key |
| Video has no sound | Make sure `scipy` is installed: `pip install scipy` |
| Frames take too long | Normal! 12 signs × ~800 frames each. Let it run. |
| Soundtrack not picked up | Make sure the file is directly in `soundtrack/` (not a subfolder) |
| `venv\Scripts\Activate.ps1 cannot be loaded` | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |

---

## ✅ Quick-Start Checklist

- [ ] Python installed and on PATH
- [ ] FFmpeg installed and on PATH
- [ ] Ran `setup_windows.bat` once
- [ ] Gemini API key saved in `.env`
- [ ] (Optional) Soothing soundtrack dropped in `soundtrack/` folder
- [ ] Double-click `generate_all.bat` and wait
- [ ] Upload reels from `reels_output/` to Instagram
