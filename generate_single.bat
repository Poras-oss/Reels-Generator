@echo off
REM  Jyotesh AI - Generate ONE Zodiac Sign Reel
REM  Usage: generate_single.bat Aries

echo.
echo  Jyotesh AI - Single Sign Reel Generator
echo  ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

if "%~1"=="" (
    echo  Enter the zodiac sign to generate:
    echo  Aries, Taurus, Gemini, Cancer, Leo, Virgo,
    echo  Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces
    echo.
    set /p SIGN="  Your sign: "
) else (
    set SIGN=%~1
)

set "SOUNDTRACK="
for %%f in (soundtrack\*.mp3 soundtrack\*.wav soundtrack\*.m4a) do (
    set "SOUNDTRACK=%%f"
    goto :found_audio
)
:found_audio

if defined SOUNDTRACK (
    echo  Using soundtrack: %SOUNDTRACK%
    python Generate.py --sign %SIGN% --soundtrack "%SOUNDTRACK%"
) else (
    python Generate.py --sign %SIGN%
)

echo.
echo  Done! Check reels_output\ for your reel.
echo.
pause
