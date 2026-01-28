"""Simple local TODO/Reminder manager with in-memory storage."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class TodoItem:
    title: str
    due: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    reminded: bool = False

    def is_due_soon(self, minutes: int = 5) -> bool:
        if not self.due:
            return False
        now = datetime.now()
        return now >= self.due - timedelta(minutes=minutes) and now <= self.due

    def is_overdue(self) -> bool:
        return self.due is not None and datetime.now() > self.due


class TodoManager:
    def __init__(self) -> None:
        self.items: List[TodoItem] = []
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.on_reminder = None  # callback(item)

    def add(self, title: str, due: Optional[datetime] = None, notes: str = "") -> TodoItem:
        item = TodoItem(title=title, due=due, notes=notes)
        self.items.append(item)
        return item

    def list(self) -> List[TodoItem]:
        return list(self.items)

    def start_reminder(self, interval_seconds: int = 30, minutes_before: int = 5) -> None:
        if self._thread and self._thread.is_alive():
            return

        def run() -> None:
            while not self._stop.is_set():
                for item in self.items:
                    if not item.reminded and item.is_due_soon(minutes_before):
                        item.reminded = True
                        if self.on_reminder:
                            self.on_reminder(item)
                time.sleep(interval_seconds)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop_reminder(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
