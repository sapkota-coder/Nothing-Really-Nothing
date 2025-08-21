import subprocess
import sys
import importlib
import threading
from transformers import AutoModel, AutoTokenizer
import torch
import torchvision.models as models
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


class ModelDownloaderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Model/Package Downloader")
        self.geometry("700x500")
        self.configure(bg="#2E3B4E")
        self.resizable(False, False)

        self.downloading = False
        self.download_thread = None

        # Frame to hold the centered entry
        self.frame = tk.Frame(self, bg="#2E3B4E")
        self.frame.grid(row=0, column=0, pady=10, padx=10)

        # Center the entry inside the frame
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.entry = tk.Entry(
            self.frame,
            width=30,
            bg="#2C3E50",
            fg="#ffffff",
            insertbackground="#ffffff",
            font=("Helvetica", 11),
        )
        self.entry.grid(row=0, column=0, sticky="ew")  # Expand horizontally in frame

        self.progress = ttk.Progressbar(
            self, orient="horizontal", length=250, mode="indeterminate"
        )
        self.progress.grid(row=1, column=0, pady=10)

        self.log = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            state="disabled",
            bg="#34495E",
            fg="#ffffff",
            font=("Helvetica", 11),
        )
        self.log.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.bind("<Control-Key-8>", self._stop_download)
        self.bind("<Control-c>", self._stop_download)
        self.bind("<Control-0>", self._stop_download)
        self.bind("<Control-q>", self._stop_download)
        self.entry.bind("<Return>", self._on_click)

        self.entry.focus_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _on_click(self, event=None):
        name = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        if name.lower() == "exit":
            self.destroy()
            return

        if not name:
            messagebox.showwarning(
                "Input Required", "Please enter a model or package name."
            )
            return

        if name.lower() in ["clear", "cls"]:
            self._clear_log()
            return

        if self.downloading:
            self._log(
                "⚠️ Already downloading. Press Ctrl+8, Ctrl+C, Ctrl+0, or Ctrl+Q to stop.\n",
                color="#ff5555",
            )
            return

        self.progress.start()
        self.downloading = True
        self.download_thread = threading.Thread(
            target=self.handle_input, args=(name,), daemon=True
        )
        self.download_thread.start()

    def _stop_download(self, event=None):
        if self.download_thread and self.download_thread.is_alive():
            self._log("⛔ Download interrupted by user.\n", color="#ff5555")
            self.downloading = False
            self._stop_progress()

    def handle_input(self, name: str):
        self._log(f"📦 Processing: {name}\n")
        success = False

        try:
            if not self.downloading:
                return
            AutoModel.from_pretrained(name)
            AutoTokenizer.from_pretrained(name)
            self._log("✅ HuggingFace model downloaded.\n", color="#2ECC71")
            success = True
        except Exception as e:
            print(f"{e}")

        if not success and self.downloading:
            try:
                if hasattr(models, name):
                    model_fn = getattr(models, name)
                    model = model_fn(pretrained=True)
                    torch.save(model.state_dict(), f"{name}.pt")
                    self._log("✅ TorchVision model downloaded.\n", color="#2ECC71")
                    success = True
            except Exception:
                pass

        if not success and self.downloading:
            try:
                importlib.import_module(name)
                self._log(f"✅ Library '{name}' already installed.\n", color="#2ECC71")
            except ImportError:
                self._log(f"📥 Installing '{name}' via pip...\n", color="#F39C12")
                try:
                    process = subprocess.Popen(
                        [sys.executable, "-m", "pip", "install", name],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )
                    for line in process.stdout:
                        if not self.downloading:
                            process.terminate()
                            self._log("⛔ Download stopped.\n", color="#ff5555")
                            break
                        self._log(line, color="#BDC3C7")
                    process.wait()
                    if process.returncode == 0 and self.downloading:
                        self._log(
                            f"✅ '{name}' installed successfully.\n", color="#2ECC71"
                        )
                    elif self.downloading:
                        self._log(
                            f"❌ Pip install failed with return code {process.returncode}.\n",
                            color="#E74C3C",
                        )
                except Exception as e:
                    self._log(f"❌ Pip install failed: {e}\n", color="#E74C3C")

        self._stop_progress()
        self.downloading = False

    def _log(self, message: str, color: str = "#ffffff"):
        self.log.configure(state="normal")
        self.log.insert(tk.END, message, color)
        self.log.tag_configure(color, foreground=color)
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.configure(state="disabled")

    def _stop_progress(self):
        self.progress.stop()


if __name__ == "__main__":
    app = ModelDownloaderGUI()
    app.mainloop()
