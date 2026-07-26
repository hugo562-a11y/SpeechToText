import os, sys, json, threading, subprocess, urllib.request, zipfile, shutil, tempfile
import logging, traceback, ctypes, atexit
from pathlib import Path
from tkinter import (Tk, ttk, StringVar, BooleanVar, IntVar, filedialog, messagebox)

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

# ── Error log (visible when EXE crashes) ──────────────────────────────────
ERROR_LOG = Path(tempfile.gettempdir()) / "stt_error.log"
sys.stderr = open(ERROR_LOG, "a", encoding="utf-8")

def _log_error():
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(traceback.format_exc() + "\n")

# ── Single-instance check ─────────────────────────────────────────────────
try:
    kernel32 = ctypes.windll.kernel32
    _mutex = kernel32.CreateMutexW(None, False, "Local\\AudioToText_STT")
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        ctypes.windll.user32.MessageBoxW(0, "程式已在執行中", "提示", 0)
        sys.exit(0)
except Exception:
    pass

# ── Auto-install dependencies ──────────────────────────────────────────────
_MISSING = []
for pkg, imp in [("faster-whisper", "faster-whisper")]:
    try:
        __import__(imp)
    except ImportError:
        _MISSING.append(pkg)
if _MISSING:
    print(f"正在安裝 {', '.join(_MISSING)}（首次需下載約 2~3GB PyTorch，請耐心等待）...")
    print("=" * 60)
    subprocess.check_call([sys.executable, "-m", "pip", "install", *_MISSING])
    print("=" * 60)
    print("安裝完成！")

import faster_whisper

# ── Supported formats ──────────────────────────────────────────────────────
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma"}
VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}
ALL_EXT = AUDIO_EXT | VIDEO_EXT


def default_output_dir():
    """Return an existing Desktop folder, including OneDrive-redirected ones."""
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "OneDrive" / "Desktop",
        home / "OneDrive" / "桌面",
        home,
    ]
    return next((path for path in candidates if path.is_dir()), home)

# ── FFmpeg (lazy download) ─────────────────────────────────────────────────
FFMPEG_DIR = Path(tempfile.gettempdir()) / "stt_ffmpeg"
FFMPEG_BIN = FFMPEG_DIR / "ffmpeg.exe"

def get_ffmpeg():
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    if FFMPEG_BIN.exists():
        os.environ["PATH"] = str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", "")
        return str(FFMPEG_BIN)
    return None

def download_ffmpeg(callback=None):
    FFMPEG_DIR.mkdir(parents=True, exist_ok=True)
    url = ("https://github.com/BtbN/FFmpeg-Builds/releases/download/"
           "latest/ffmpeg-master-latest-win64-gpl.zip")
    zip_path = FFMPEG_DIR / "ffmpeg.zip"
    try:
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, "r") as z:
            for member in z.namelist():
                if member.endswith("ffmpeg.exe") or member.endswith("ffprobe.exe"):
                    z.extract(member, FFMPEG_DIR)
                    name = os.path.basename(member)
                    dst = FFMPEG_DIR / name
                    if not dst.exists():
                        shutil.move(os.path.join(FFMPEG_DIR, member), dst)
        zip_path.unlink()
        for p in list(FFMPEG_DIR.iterdir()):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
        os.environ["PATH"] = str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", "")
        return str(FFMPEG_BIN)
    except Exception:
        _log_error()
        raise

# ── Main app ───────────────────────────────────────────────────────────────
class AudioToTextApp:
    def __init__(self, root: Tk):
        self.root = root
        root.title("語音轉文字工具")
        root.geometry("650x580")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._worker = None
        self._running = False

        self.file_path = StringVar()
        self.output_dir = StringVar(value=str(default_output_dir()))
        self.model_size = StringVar(value="base")
        self.language = StringVar(value="auto")
        self.task = StringVar(value="transcribe")
        self.output_format = StringVar(value="txt")
        self.use_cuda = BooleanVar(value=False)
        self.progress_var = IntVar(value=0)
        self.status_var = StringVar(value="就緒")

        self._build_ui()
        self._center_window()
        self.root.after(100, self._check_ffmpeg)  # delayed ffmpeg check

    def _on_close(self):
        self._running = False
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)  # force kill all threads

    def _check_ffmpeg(self):
        if get_ffmpeg() is None:
            self.status_var.set("正在下載 ffmpeg（首次需下載約 120MB）...")
            self.root.update()
            try:
                download_ffmpeg()
                self.status_var.set("ffmpeg 就緒")
            except Exception as e:
                messagebox.showerror("錯誤", f"ffmpeg 下載失敗：{e}\n請手動安裝 ffmpeg")
                self.status_var.set("ffmpeg 下載失敗")

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="選擇檔案（影片或音檔）:", font=("", 10, "bold"))\
            .grid(row=0, column=0, sticky="w", pady=(0, 4))
        f1 = ttk.Frame(main)
        f1.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Entry(f1, textvariable=self.file_path, state="readonly")\
            .pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(f1, text="瀏覽...", command=self._browse_file).pack(side="right")

        ttk.Label(main, text="輸出位置:", font=("", 10, "bold"))\
            .grid(row=2, column=0, sticky="w", pady=(0, 4))
        f2 = ttk.Frame(main)
        f2.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Entry(f2, textvariable=self.output_dir, state="readonly")\
            .pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(f2, text="瀏覽...", command=self._browse_output).pack(side="right")

        opt = ttk.LabelFrame(main, text="轉換選項", padding=10)
        opt.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 12))

        ttk.Label(opt, text="模型大小:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Combobox(opt, textvariable=self.model_size, state="readonly", width=14,
                     values=["tiny", "base", "small", "medium", "large-v3"])\
            .grid(row=0, column=1, sticky="w", padx=(0, 24))
        ttk.Label(opt, text="（越小越快）", foreground="gray").grid(row=0, column=2, sticky="w")

        ttk.Label(opt, text="語言:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(6, 0))
        ttk.Combobox(opt, textvariable=self.language, state="readonly", width=14,
                     values=["auto", "zh", "en", "ja", "ko", "fr", "de", "es", "ru", "th", "vi"])\
            .grid(row=1, column=1, sticky="w", padx=(0, 24), pady=(6, 0))
        ttk.Label(opt, text="（auto = 自動）", foreground="gray")\
            .grid(row=1, column=2, sticky="w", pady=(6, 0))

        ttk.Label(opt, text="任務類型:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(6, 0))
        ttk.Combobox(opt, textvariable=self.task, state="readonly", width=14,
                     values=["transcribe", "translate"])\
            .grid(row=2, column=1, sticky="w", padx=(0, 24), pady=(6, 0))
        ttk.Label(opt, text="（translate → 英文）", foreground="gray")\
            .grid(row=2, column=2, sticky="w", pady=(6, 0))

        ttk.Label(opt, text="輸出格式:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(6, 0))
        ttk.Combobox(opt, textvariable=self.output_format, state="readonly", width=14,
                     values=["txt", "srt", "vtt", "json", "tsv"])\
            .grid(row=3, column=1, sticky="w", padx=(0, 24), pady=(6, 0))

        ttk.Checkbutton(opt, text="使用 GPU (CUDA)", variable=self.use_cuda)\
            .grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))

        pf = ttk.Frame(main)
        pf.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        self.prog = ttk.Progressbar(pf, variable=self.progress_var, mode="determinate")
        self.prog.pack(fill="x", expand=True)
        ttk.Label(pf, textvariable=self.status_var, foreground="#555")\
            .pack(anchor="w", pady=(2, 0))

        bf = ttk.Frame(main)
        bf.grid(row=6, column=0, columnspan=3, pady=(4, 0))
        self.btn = ttk.Button(bf, text="開始轉換", command=self._start, width=16)
        self.btn.pack(side="left", padx=6)
        ttk.Button(bf, text="離開", command=self._on_close, width=10).pack(side="left", padx=6)

        for i in range(3):
            main.columnconfigure(i, weight=1)

    def _center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}")

    def _browse_file(self):
        p = filedialog.askopenfilename(title="選擇檔案", filetypes=[
            ("支援格式", " ".join(f"*{e}" for e in sorted(ALL_EXT))),
            ("影片", " ".join(f"*{e}" for e in sorted(VIDEO_EXT))),
            ("音檔", " ".join(f"*{e}" for e in sorted(AUDIO_EXT))),
            ("所有", "*.*")])
        if p:
            ext = os.path.splitext(p)[1].lower()
            if ext not in ALL_EXT:
                messagebox.showwarning("不支援格式",
                    "此工具僅支援影片與音檔，不支援圖片。\n\n"
                    f"支援格式：{', '.join(sorted(ALL_EXT))}")
                return
            self.file_path.set(p)

    def _browse_output(self):
        p = filedialog.askdirectory(title="選擇輸出資料夾")
        if p:
            self.output_dir.set(p)

    def _start(self):
        src = self.file_path.get()
        if not src or not os.path.isfile(src):
            return messagebox.showwarning("提示", "請選擇一個有效的檔案")
        if os.path.splitext(src)[1].lower() not in ALL_EXT:
            return messagebox.showwarning("提示", "不支援的格式")
        if get_ffmpeg() is None:
            return messagebox.showwarning("提示", "ffmpeg 尚未下載完成，請稍候")

        self._running = True
        self.btn.config(state="disabled")
        self.progress_var.set(0)
        sizes = {"tiny": 1, "base": 1, "small": 2, "medium": 5, "large-v3": 10}
        self.status_var.set(f"首次會下載模型 (~{sizes.get(self.model_size.get(),5)}GB)，請耐心等待...")
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def _run(self):
        try:
            def upd(pct, msg):
                if not self._running:
                    return
                self.root.after(0, lambda: self.progress_var.set(pct))
                self.root.after(0, lambda: self.status_var.set(msg))

            upd(5, "載入模型中...")
            model = faster_whisper.WhisperModel(
                self.model_size.get(),
                device="cuda" if self.use_cuda.get() else "cpu",
                compute_type="float16" if self.use_cuda.get() else "int8")

            upd(15, "正在辨識語音...請耐心等候")
            segs, info = model.transcribe(
                self.file_path.get(),
                language=None if self.language.get() == "auto" else self.language.get(),
                task=self.task.get(), beam_size=5, vad_filter=True)

            upd(50, f"偵測到語言：{info.language}，產出結果中...")
            seg_list = list(segs)
            base = os.path.splitext(os.path.basename(self.file_path.get()))[0]
            out_dir = Path(self.output_dir.get()).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
            out = str(out_dir / f"{base}.{self.output_format.get()}")
            fmts = {"txt": self._w_txt, "srt": self._w_srt, "vtt": self._w_vtt,
                    "json": self._w_json, "tsv": self._w_tsv}
            fmts[self.output_format.get()](out, seg_list, info)

            upd(100, f"完成！{out}")
            self.root.after(0, lambda: messagebox.showinfo("完成", f"輸出：{out}"))
        except Exception as e:
            _log_error()
            self.root.after(0, lambda: messagebox.showerror("錯誤", str(e)))
            self.root.after(0, lambda: self.status_var.set("錯誤"))
        finally:
            self.root.after(0, lambda: self.btn.config(state="normal"))

    # ── Writers ──
    @staticmethod
    def _w_txt(p, segs, _info):
        with open(p, "w", encoding="utf-8") as f:
            for s in segs:
                f.write(s.text.strip() + "\n")

    @staticmethod
    def _w_srt(p, segs, _info):
        def ts(sec):
            h, m = int(sec//3600), int((sec%3600)//60)
            s, ms = int(sec%60), int((sec-int(sec))*1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        with open(p, "w", encoding="utf-8") as f:
            for i, s in enumerate(segs, 1):
                f.write(f"{i}\n{ts(s.start)} --> {ts(s.end)}\n{s.text.strip()}\n\n")

    @staticmethod
    def _w_vtt(p, segs, _info):
        def ts(sec):
            h, m = int(sec//3600), int((sec%3600)//60)
            s, ms = int(sec%60), int((sec-int(sec))*1000)
            return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
        with open(p, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for s in segs:
                f.write(f"{ts(s.start)} --> {ts(s.end)}\n{s.text.strip()}\n\n")

    @staticmethod
    def _w_json(p, segs, info):
        data = {"language": getattr(info, "language", None),
                "duration": getattr(info, "duration", None),
                "segments": [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segs]}
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _w_tsv(p, segs, _info):
        with open(p, "w", encoding="utf-8") as f:
            f.write("start\tend\ttext\n")
            for s in segs:
                f.write(f"{s.start}\t{s.end}\t{s.text.strip()}\n")

# ── Entry ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        root = Tk()
        app = AudioToTextApp(root)
        root.mainloop()
    except Exception as e:
        _log_error()
        print(f"\n錯誤：{e}")
        print(f"詳細資訊已記錄至：{ERROR_LOG}")
        print("\n請截圖此畫面或查看錯誤記錄檔。")
        os.system("pause")
    finally:
        try:
            os._exit(0)
        except Exception:
            pass
