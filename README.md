# 語音轉文字工具

![Python](https://img.shields.io/badge/Python-3.10-blue)
![License](https://img.shields.io/badge/License-MIT-green)

把影片或音檔的聲音轉成文字。選檔案 → 選輸出位置 → 開始轉換，就這樣。

支援 MP3/WAV/MP4/MKV/AVI 等常見影音格式，輸出可選 txt/srt/vtt/json/tsv。

## 安裝

```bash
git clone https://github.com/hugo562-a11y/SpeechToText.git
cd SpeechToText
py -3.10 -m pip install -r requirements.txt
py -3.10 audio_to_text_tool.py
```

> 首次執行會自動下載語音模型（約 1~10GB），下載一次之後離線可用。

## 使用

打開程式 → 選檔案 → 選輸出資料夾 → 按「開始轉換」。

選項就四個：**模型大小**（越小越快）、**語言**（auto 自動偵測）、**任務類型**（轉錄或翻譯成英文）、**輸出格式**（一般用 txt 或 srt）。

## License

MIT
