@echo off
REM One command: generate reels for all signs and create same-name JSON queue files.

title Reel Publish Queue Generator

set CATEGORY=%1
if "%CATEGORY%"=="" set CATEGORY=horoscope

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

    python generate_publish_queue.py --sign all --category %CATEGORY% --parallel

echo.
echo  Done. Commit and push the publish_queue\ folder.
echo.
pause
