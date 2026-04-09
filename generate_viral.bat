@echo off
REM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REM  generate_viral.bat — Viral Category Reel Generator
REM  Usage: generate_viral.bat [sign] [category] [soundtrack]
REM
REM  sign:     Aries | Taurus | ... | Pisces | all
REM  category: relationships | career | current_events |
REM            emotional_healing | manifestation | all
REM  Examples:
REM    generate_viral.bat Leo relationships
REM    generate_viral.bat Scorpio all
REM    generate_viral.bat all career
REM    generate_viral.bat all all
REM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
title Viral Reel Generator — JyoteshAI

SET SIGN=%1
SET CATEGORY=%2
SET SOUNDTRACK=%3

IF "%SIGN%"=="" SET SIGN=all
IF "%CATEGORY%"=="" SET CATEGORY=all

echo.
echo  ╔════════════════════════════════════════════════════════╗
echo  ║        VIRAL REEL GENERATOR — JyoteshAI               ║
echo  ║  Categories: relationships, career, current_events     ║
echo  ║              emotional_healing, manifestation          ║
echo  ║  Languages : English + Hindi (two reels per sign)      ║
echo  ╚════════════════════════════════════════════════════════╝
echo.
echo  Sign     : %SIGN%
echo  Category : %CATEGORY%
IF NOT "%SOUNDTRACK%"=="" echo  Soundtrack: %SOUNDTRACK%
echo.

IF "%SIGN%"=="all" IF "%CATEGORY%"=="all" (
    echo  WARNING: Generating ALL signs x ALL categories = 120 reels total.
    echo  This will take a long time. Press Ctrl+C to abort.
    echo.
    pause
)

REM Activate venv if present
IF EXIST venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Build command
SET CMD=python Generate.py --sign %SIGN% --category %CATEGORY%
IF NOT "%SOUNDTRACK%"=="" SET CMD=%CMD% --soundtrack %SOUNDTRACK%

echo  Running: %CMD%
echo.
%CMD%

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERROR] Generation failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo  ✅ Done! Reels saved to reels_output\
echo.
pause
