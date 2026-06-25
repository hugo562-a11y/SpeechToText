# 🎤 語音轉文字工具 (Speech-to-Text Tool)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

將影片或音檔中的語音自動轉換為文字，支援多種輸出格式與模型選擇。基於 **OpenAI Whisper**（faster-whisper）實現，離線執行，無需網路連線（首次下載模型除外）。

> **English**: A GUI tool that transcribes speech from audio/video files into text. Powered by faster-whisper, runs offline.

---

## ✨ 功能特色 / Features

- **支援多種格式** — MP3, WAV, M4A, FLAC, MP4, MKV, AVI, MOV 等常見影音格式
- **多種輸出格式** — TXT, SRT, VTT, JSON, TSV
- **模型自由選擇** — tiny / base / small / medium / large-v3（速度與準確度自訂）
- **多語言支援** — 自動偵測或手動指定（中文、英文、日文、韓文等）
- **翻譯模式** — 直接將語音翻譯為英文（translate mode）
- **GPU 加速** — 支援 NVIDIA CUDA，大幅提升轉換速度
- **離線執行** — 模型下載後完全離線執行
- **友善 UI** — 直覺的圖形介面，無需指令操作

---

## 📥 下載 / Download

### 方法一：直接執行 EXE（免安裝）

從 [Releases](https://github.com/hugo562-a11y/SpeechToText/releases) 下載最新版本的 `SpeechToText.zip`，解壓縮後執行 `SpeechToText.exe` 即可。

> 注意：首次執行會自動下載語音模型（約 1~10GB，依模型大小而異），請耐心等待。

### 方法二：Python 原始碼執行

```bash
# 1. 複製倉庫
git clone https://github.com/hugo562-a11y/SpeechToText.git
cd SpeechToText

# 2. 安裝相依套件
pip install -r requirements.txt

# 3. 執行程式
python audio_to_text_tool.py
```

> 需要 Python 3.10+ 及 [FFmpeg](https://ffmpeg.org/download.html)（若系統未安裝，程式會自動下載）。

---

## 🖥️ 使用說明 / Usage

![主介面](screenshots/main_window.png)

1. **選擇檔案** — 點擊「瀏覽」選擇影片或音檔
2. **輸出位置** — 選擇轉換後的文字檔案儲存位置（預設為桌面）
3. **調整選項** — 選擇模型大小、語言、任務類型、輸出格式
4. **開始轉換** — 點擊「開始轉換」，等待完成

### 選項說明 / Options

| 選項 | 說明 | 建議 |
|------|------|------|
| **模型大小** | tiny / base / small / medium / large-v3 | tiny 最快，large-v3 最準確 |
| **語言** | auto / zh / en / ja / ko 等 | auto 自動偵測 |
| **任務類型** | transcribe (轉錄) / translate (翻譯為英文) | 一般使用 transcribe |
| **輸出格式** | txt / srt / vtt / json / tsv | srt 適合字幕 |
| **GPU 加速** | 使用 NVIDIA CUDA | 有 NVIDIA 顯卡可啟用 |

---

## 🧱 從原始碼打包 / Build from Source

```bash
pip install pyinstaller
pyinstaller --onedir --name "SpeechToText" --noconsole audio_to_text_tool.py
```

輸出在 `dist/SpeechToText/` 目錄。

---

## 📁 專案結構 / Project Structure

```
SpeechToText/
├── audio_to_text_tool.py    # 主程式
├── requirements.txt         # Python 相依套件
├── .gitignore               # Git 忽略規則
├── LICENSE                  # MIT 授權條款
├── README.md                # 本文件
└── screenshots/             # 截圖
```

---

## 🛠️ 技術架構 / Tech Stack

- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** — 語音辨識引擎（基於 OpenAI Whisper，使用 CTranslate2）
- **PyTorch** — 深度學習框架
- **Tkinter** — GUI 圖形介面
- **PyInstaller** — 打包為獨立 EXE

---

## 📄 授權 / License

本專案採用 MIT 授權條款 — 詳見 [LICENSE](LICENSE) 檔案。

---

## 🙏 致謝 / Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper)
- [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds)
