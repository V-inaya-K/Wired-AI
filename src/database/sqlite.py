"""SQLite helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def ensure_database(database_url: str) -> str:
    """Create the database and schema if needed."""

    db_path = database_url.replace("sqlite:///", "", 1)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    return db_path
