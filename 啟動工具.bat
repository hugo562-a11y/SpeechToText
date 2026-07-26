@echo off
cd /d "%~dp0"
echo Starting Speech-to-Text Tool with Python 3.10...
echo If Python 3.10 is not installed, download it from https://python.org
echo.
py -3.10 audio_to_text_tool.py
if errorlevel 1 (
    echo.
    echo Error: Please install Python 3.10 and run: py -3.10 -m pip install -r requirements.txt
    pause
)
