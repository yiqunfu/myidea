"""AI Assistant hub GUI: chat reader, notes, todos."""

from __future__ import annotations

import json
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext

from notes import NoteManager
from todo import TodoManager
from wechat_reader import (
    extract_schedules,
    list_talkers_sqlite,
    read_conversation_json,
    read_conversation_sqlite,
    summarize_emotion,
)


class AssistantApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Assistant (Local, Consent-Driven)")
        self.geometry("960x720")

        # Shared managers
        self.notes = NoteManager()
        self.todos = TodoManager()
        self.todos.on_reminder = self._on_reminder
        self.todos.start_reminder()

        # WeChat state
        self.wc_path = tk.StringVar()
        self.wc_is_db = tk.BooleanVar()
        self.wc_talker = tk.StringVar()
        self.wc_preview = tk.IntVar(value=5)
        self.wc_talkers: list[str] = []
        self.wc_show_emotion = tk.BooleanVar(value=True)
        self.wc_show_schedule = tk.BooleanVar(value=True)
        self.wc_decrypt_cmd = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        tabs = tk.ttk.Notebook(self)
        tabs.pack(fill=tk.BOTH, expand=True)

        # WeChat tab
        wc_frame = tk.Frame(tabs)
        tabs.add(wc_frame, text="WeChat")
        self._build_wechat_tab(wc_frame)

        # Notes tab
        notes_frame = tk.Frame(tabs)
        tabs.add(notes_frame, text="Notes/Diary")
        self._build_notes_tab(notes_frame)

        # Todos tab
        todo_frame = tk.Frame(tabs)
        tabs.add(todo_frame, text="Todos")
        self._build_todo_tab(todo_frame)

    def _build_wechat_tab(self, root: tk.Frame) -> None:
        import tkinter.ttk as ttk

        top = tk.Frame(root)
        top.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(top, text="Path:").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.wc_path, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Browse", command=self._wc_browse).pack(side=tk.LEFT)
        tk.Checkbutton(top, text="DB mode", variable=self.wc_is_db).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(top, text="Emotion", variable=self.wc_show_emotion).pack(
            side=tk.LEFT, padx=5
        )
        tk.Checkbutton(top, text="Schedule", variable=self.wc_show_schedule).pack(
            side=tk.LEFT, padx=5
        )

        mid = tk.Frame(root)
        mid.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(mid, text="Talker:").pack(side=tk.LEFT)
        tk.Entry(mid, textvariable=self.wc_talker, width=20).pack(side=tk.LEFT, padx=2)
        tk.Button(mid, text="List talkers", command=self._wc_list_talkers).pack(side=tk.LEFT, padx=2)
        self.wc_talker_box = tk.Listbox(mid, height=4, exportselection=False)
        self.wc_talker_box.pack(side=tk.LEFT, padx=2)
        self.wc_talker_box.bind("<<ListboxSelect>>", self._wc_pick_talker)
        tk.Label(mid, text="Preview:").pack(side=tk.LEFT, padx=5)
        tk.Entry(mid, textvariable=self.wc_preview, width=5).pack(side=tk.LEFT)

        dec = tk.Frame(root)
        dec.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(dec, text="Decrypt cmd (optional {src}->{dst}):").pack(side=tk.LEFT)
        tk.Entry(dec, textvariable=self.wc_decrypt_cmd, width=60).pack(side=tk.LEFT, padx=5)

        btns = tk.Frame(root)
        btns.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btns, text="Load & Analyze (consent)", command=self._wc_run).pack(
            side=tk.LEFT, padx=5
        )
        self.wc_status = tk.StringVar(value="Ready")
        tk.Label(btns, textvariable=self.wc_status, fg="gray").pack(side=tk.LEFT, padx=10)

        self.wc_output = scrolledtext.ScrolledText(root, wrap=tk.WORD)
        self.wc_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _build_notes_tab(self, root: tk.Frame) -> None:
        top = tk.Frame(root)
        top.pack(fill=tk.X, padx=10, pady=5)
        self.note_title = tk.StringVar()
        tk.Label(top, text="Title:").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.note_title, width=30).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Add", command=self._add_note).pack(side=tk.LEFT, padx=5)

        self.note_text = scrolledtext.ScrolledText(root, height=10, wrap=tk.WORD)
        self.note_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.note_list = scrolledtext.ScrolledText(root, height=10, wrap=tk.WORD)
        self.note_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._refresh_notes()

    def _build_todo_tab(self, root: tk.Frame) -> None:
        top = tk.Frame(root)
        top.pack(fill=tk.X, padx=10, pady=5)
        self.todo_title = tk.StringVar()
        self.todo_due = tk.StringVar()
        tk.Label(top, text="Title:").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.todo_title, width=25).pack(side=tk.LEFT, padx=5)
        tk.Label(top, text="Due (YYYY-MM-DD HH:MM):").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self.todo_due, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Add", command=self._add_todo).pack(side=tk.LEFT, padx=5)

        self.todo_notes = scrolledtext.ScrolledText(root, height=6, wrap=tk.WORD)
        self.todo_notes.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.todo_list = scrolledtext.ScrolledText(root, height=12, wrap=tk.WORD)
        self.todo_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._refresh_todos()

    # --- WeChat handlers ---
    def _wc_browse(self) -> None:
        path = filedialog.askopenfilename()
        if path:
            self.wc_path.set(path)

    def _wc_pick_talker(self, event) -> None:
        sel = self.wc_talker_box.curselection()
        if sel:
            self.wc_talker.set(self.wc_talker_box.get(sel[0]))

    def _wc_list_talkers(self) -> None:
        path = self.wc_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Please select a DB path first.")
            return
        self.wc_status.set("Listing talkers...")
        try:
            talkers = list_talkers_sqlite(path, consent=True)
        except Exception as exc:
            self.wc_status.set("Failed.")
            messagebox.showerror("List error", str(exc))
            return
        self.wc_talkers = talkers
        self.wc_talker_box.delete(0, tk.END)
        for t in talkers:
            self.wc_talker_box.insert(tk.END, t)
        self.wc_status.set("Talkers loaded.")

    def _wc_run(self) -> None:
        path = self.wc_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Please select a file path.")
            return
        self.wc_status.set("Reading...")
        try:
            if self.wc_is_db.get():
                msgs = read_conversation_sqlite(
                    path,
                    consent=True,
                    talker=self.wc_talker.get() or None,
                    decrypt_cmd=(self.wc_decrypt_cmd.get() or None),
                )
            else:
                msgs = read_conversation_json(path, consent=True)
        except Exception as exc:
            self.wc_status.set("Failed.")
            messagebox.showerror("Read error", str(exc))
            return

        preview_n = max(self.wc_preview.get(), 0)
        emotion = summarize_emotion(msgs) if self.wc_show_emotion.get() else None
        schedules = extract_schedules(msgs) if self.wc_show_schedule.get() else []

        self.wc_output.delete("1.0", tk.END)
        self.wc_output.insert(tk.END, f"# Preview (first {preview_n})\n")
        for msg in msgs[:preview_n]:
            self.wc_output.insert(tk.END, json.dumps(msg, ensure_ascii=False) + "\n")
        if emotion:
            self.wc_output.insert(tk.END, "\n# Emotion summary\n")
            self.wc_output.insert(tk.END, json.dumps(emotion, ensure_ascii=False) + "\n")
        if schedules:
            self.wc_output.insert(tk.END, "\n# Schedule/plan items\n")
            for item in schedules:
                out = dict(item)
                ts = out.get("timestamp")
                if hasattr(ts, "isoformat"):
                    out["timestamp"] = ts.isoformat()
                self.wc_output.insert(tk.END, json.dumps(out, ensure_ascii=False) + "\n")
        self.wc_status.set("Done.")

    # --- Notes handlers ---
    def _add_note(self) -> None:
        title = self.note_title.get().strip() or "Untitled"
        content = self.note_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showerror("Error", "Please enter note content.")
            return
        self.notes.add(title=title, content=content)
        self.note_text.delete("1.0", tk.END)
        self._refresh_notes()

    def _refresh_notes(self) -> None:
        self.note_list.delete("1.0", tk.END)
        for note in self.notes.list():
            self.note_list.insert(
                tk.END,
                f"{note.created_at:%Y-%m-%d %H:%M} | {note.title}\n{note.content}\n\n",
            )

    # --- Todo handlers ---
    def _add_todo(self) -> None:
        title = self.todo_title.get().strip()
        if not title:
            messagebox.showerror("Error", "Please enter todo title.")
            return
        notes = self.todo_notes.get("1.0", tk.END).strip()
        due_str = self.todo_due.get().strip()
        due_dt = None
        if due_str:
            try:
                due_dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Due time format: YYYY-MM-DD HH:MM")
                return
        self.todos.add(title=title, due=due_dt, notes=notes)
        self.todo_notes.delete("1.0", tk.END)
        self.todo_due.set("")
        self._refresh_todos()

    def _refresh_todos(self) -> None:
        self.todo_list.delete("1.0", tk.END)
        for item in self.todos.list():
            due = item.due.isoformat() if item.due else "N/A"
            status = "overdue" if item.is_overdue() else ("due soon" if item.is_due_soon() else "pending")
            self.todo_list.insert(
                tk.END,
                f"{item.title} | due: {due} | {status}\n{item.notes}\n\n",
            )

    def _on_reminder(self, item) -> None:
        messagebox.showinfo("Reminder", f"即将到期: {item.title}")


def main() -> None:
    app = AssistantApp()
    app.mainloop()


if __name__ == "__main__":
    main()
