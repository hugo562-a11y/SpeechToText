@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在啟動語音轉文字工具...
echo 若跳出 Python 安裝視窗請先安裝 Python，或手動執行：
echo   pip install -r requirements.txt
echo   python audio_to_text_tool.py
echo.
python audio_to_text_tool.py
if errorlevel 1 (
    echo.
    echo 發生錯誤，請確認已安裝 Python 3.10+
    pause
)
