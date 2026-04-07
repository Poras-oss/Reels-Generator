@echo off
REM  Jyotesh AI - Generate ALL 12 Zodiac Sign Reels

echo.
echo  Jyotesh AI - Daily Horoscope Reel Generator
echo  ============================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

set "SOUNDTRACK="
for %%f in (soundtrack\*.mp3 soundtrack\*.wav soundtrack\*.m4a) do (
    set "SOUNDTRACK=%%f"
    goto :found_audio
)
:found_audio

if defined SOUNDTRACK (
    echo  Using soundtrack: %SOUNDTRACK%
    echo.
    python Generate.py --sign all --soundtrack "%SOUNDTRACK%"
) else (
    echo  No soundtrack found in soundtrack\ folder - using ambient drone only
    echo.
    python Generate.py --sign all
)

echo.
echo  Done! Check the reels_output\ folder for your videos.
echo.
pause
