"""Simple local note/diary storage in memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Note:
    title: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)


class NoteManager:
    def __init__(self) -> None:
        self.notes: List[Note] = []

    def add(self, title: str, content: str) -> Note:
        note = Note(title=title, content=content)
        self.notes.append(note)
        return note

    def list(self) -> List[Note]:
        return list(self.notes)
