@echo off
REM One command: generate reels for all signs and create same-name JSON queue files.

title Reel Publish Queue Generator

set CATEGORY=%1
if "%CATEGORY%"=="" set CATEGORY=horoscope

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

echo.
echo  Reel Publish Queue Generator
echo  ============================
echo  Category: %CATEGORY%
echo.

if defined SOUNDTRACK (
    echo  Using soundtrack: %SOUNDTRACK%
    python generate_publish_queue.py --sign all --category %CATEGORY% --soundtrack "%SOUNDTRACK%"
) else (
    python generate_publish_queue.py --sign all --category %CATEGORY%
)

echo.
echo  Done. Commit and push the publish_queue\ folder.
echo.
pause
