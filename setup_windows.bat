@echo off
REM  Jyotesh AI - First-Time Windows Setup
REM  Run this ONCE to set up your Python environment.

echo.
echo  Jyotesh AI - Windows Setup
echo  ==========================
echo.

cd /d "%~dp0"

REM -- Check Python --
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is NOT installed or not on PATH.
    echo  Download it from: https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install!
    pause
    exit /b 1
)
echo  [OK] Python found.

REM -- Check ffmpeg --
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo  [WARNING] FFmpeg is NOT found on PATH.
    echo  You must install it before generating videos.
    echo  See the guide: WINDOWS_SETUP_AND_WORKFLOW.md
    echo.
) else (
    echo  [OK] FFmpeg found.
)

REM -- Create virtual environment --
if not exist "venv" (
    echo.
    echo  Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

REM -- Install dependencies --
echo.
echo  Installing Python packages...
pip install -r requirements.txt

echo.
echo  ==================================
echo  Setup complete!
echo.
echo  Next steps:
echo    1. Add your Gemini API key to the .env file
echo    2. Install FFmpeg (see guide)
echo    3. Drop a soundtrack in the soundtrack\ folder
echo    4. Double-click generate_all.bat to make reels!
echo  ==================================
echo.
pause
