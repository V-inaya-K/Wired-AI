"""SQLite conversation memory."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryMessage:
    """Conversation message record."""

    role: str
    content: str


class SQLiteMemory:
    """Store and retrieve conversation history."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO conversation_messages(session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )
            conn.commit()

    def get_history(self, session_id: str, limit: int = 12) -> list[MemoryMessage]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [MemoryMessage(role=row[0], content=row[1]) for row in reversed(rows)]
