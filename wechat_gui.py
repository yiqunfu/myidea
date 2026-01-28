"""Minimal Tkinter GUI for consent-based WeChat reading and local analysis."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from wechat_reader import (
    extract_schedules,
    read_conversation_json,
    read_conversation_sqlite,
    summarize_emotion,
)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WeChat Local Reader (Consent Required)")
        self.geometry("800x600")

        self.path_var = tk.StringVar()
        self.is_db_var = tk.BooleanVar()
        self.talker_var = tk.StringVar()
        self.preview_var = tk.IntVar(value=5)
        self.output = scrolledtext.ScrolledText(self, wrap=tk.WORD)

        self._build_ui()

    def _build_ui(self) -> None:
        frm = tk.Frame(self)
        frm.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frm, text="Path (JSON or DB):").pack(side=tk.LEFT)
        tk.Entry(frm, textvariable=self.path_var, width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(frm, text="Browse", command=self._browse).pack(side=tk.LEFT)

        opts = tk.Frame(self)
        opts.pack(fill=tk.X, padx=10, pady=5)
        tk.Checkbutton(opts, text="DB mode (SQLite)", variable=self.is_db_var).pack(
            side=tk.LEFT, padx=5
        )
        tk.Label(opts, text="Talker (DB):").pack(side=tk.LEFT)
        tk.Entry(opts, textvariable=self.talker_var, width=20).pack(side=tk.LEFT, padx=5)
        tk.Label(opts, text="Preview:").pack(side=tk.LEFT)
        tk.Entry(opts, textvariable=self.preview_var, width=5).pack(side=tk.LEFT, padx=5)

        btns = tk.Frame(self)
        btns.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btns, text="Load & Analyze (consent)", command=self._run).pack(
            side=tk.LEFT, padx=5
        )

        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _browse(self) -> None:
        path = filedialog.askopenfilename()
        if path:
            self.path_var.set(path)

    def _run(self) -> None:
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("Error", "Please select a file path.")
            return

        try:
            if self.is_db_var.get():
                msgs = read_conversation_sqlite(
                    path, consent=True, talker=self.talker_var.get() or None
                )
            else:
                msgs = read_conversation_json(path, consent=True)
        except Exception as exc:
            messagebox.showerror("Read error", str(exc))
            return

        preview_n = max(self.preview_var.get(), 0)
        emotion = summarize_emotion(msgs)
        schedules = extract_schedules(msgs)

        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"# Preview (first {preview_n})\n")
        for msg in msgs[:preview_n]:
            self.output.insert(tk.END, json.dumps(msg, ensure_ascii=False) + "\n")
        self.output.insert(tk.END, "\n# Emotion summary\n")
        self.output.insert(tk.END, json.dumps(emotion, ensure_ascii=False) + "\n")
        self.output.insert(tk.END, "\n# Schedule/plan items\n")
        for item in schedules:
            out = dict(item)
            ts = out.get("timestamp")
            if hasattr(ts, "isoformat"):
                out["timestamp"] = ts.isoformat()
            self.output.insert(tk.END, json.dumps(out, ensure_ascii=False) + "\n")


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
