@echo off
REM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REM  generate_all.bat — Generate all 12 zodiac reels
REM  Usage: generate_all.bat [category]
REM  category: horoscope (default) | relationships | career |
REM            current_events | emotional_healing | manifestation | all
REM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
title JyoteshAI — Generate All Signs

SET CATEGORY=%1
IF "%CATEGORY%"=="" SET CATEGORY=horoscope

echo.
echo  JyoteshAI - Daily Reel Generator
echo  ====================================
echo  Generating ALL 12 signs  Category: %CATEGORY%
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

    python Generate.py --sign all --category %CATEGORY% --parallel

echo.
echo  Done! Check the reels_output\ folder for your videos.
echo.
pause
