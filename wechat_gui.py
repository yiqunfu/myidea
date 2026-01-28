"""Minimal Tkinter GUI for consent-based WeChat reading and local analysis."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from wechat_reader import (
    extract_schedules,
    list_talkers_sqlite,
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
        self.talkers: list[str] = []
        self.output = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.status_var = tk.StringVar(value="Awaiting consent and input.")

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
        self.talker_entry = tk.Entry(opts, textvariable=self.talker_var, width=20)
        self.talker_entry.pack(side=tk.LEFT, padx=2)
        tk.Button(opts, text="List", command=self._list_talkers).pack(side=tk.LEFT, padx=2)
        self.talker_box = tk.Listbox(opts, height=4, exportselection=False)
        self.talker_box.pack(side=tk.LEFT, padx=2)
        self.talker_box.bind("<<ListboxSelect>>", self._on_select_talker)
        tk.Label(opts, text="Preview:").pack(side=tk.LEFT)
        tk.Entry(opts, textvariable=self.preview_var, width=5).pack(side=tk.LEFT, padx=5)

        btns = tk.Frame(self)
        btns.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btns, text="Load & Analyze (consent)", command=self._run).pack(
            side=tk.LEFT, padx=5
        )
        tk.Label(btns, textvariable=self.status_var, fg="gray").pack(side=tk.LEFT, padx=10)

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

        self.status_var.set("Reading...")
        try:
            if self.is_db_var.get():
                msgs = read_conversation_sqlite(
                    path, consent=True, talker=self.talker_var.get() or None
                )
            else:
                msgs = read_conversation_json(path, consent=True)
        except Exception as exc:
            self.status_var.set("Failed.")
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
        self.status_var.set("Done.")

    def _list_talkers(self) -> None:
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("Error", "Please select a DB path first.")
            return
        self.status_var.set("Listing talkers...")
        try:
            self.talkers = list_talkers_sqlite(path, consent=True)
        except Exception as exc:
            self.status_var.set("Failed.")
            messagebox.showerror("List error", str(exc))
            return
        self.talker_box.delete(0, tk.END)
        for t in self.talkers:
            self.talker_box.insert(tk.END, t)
        self.status_var.set("Talkers loaded.")

    def _on_select_talker(self, event: tk.Event) -> None:
        sel = self.talker_box.curselection()
        if sel:
            self.talker_var.set(self.talker_box.get(sel[0]))


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
