@echo off
cd /d "%~dp0"
echo Starting Speech-to-Text Tool...
echo If Python is not installed, download it from https://python.org
echo.
python audio_to_text_tool.py
if errorlevel 1 (
    echo.
    echo Error: Please install Python 3.10+ and run: pip install -r requirements.txt
    pause
)
