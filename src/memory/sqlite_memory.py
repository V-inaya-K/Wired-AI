"""SQLite conversation memory."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class MemoryMessage:
    """Conversation message record."""

    role: str
    content: str


class SQLiteMemory:
    """Store and retrieve conversation history."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def _ensure_session_exists(self, session_id: str) -> None:
        """Ensure a session row exists for the given session_id."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
            )
            if cursor.fetchone() is None:
                conn.execute(
                    "INSERT INTO sessions (session_id, title) VALUES (?, NULL)",
                    (session_id,),
                )
                conn.commit()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            self._ensure_session_exists(session_id)
            # If this is the first user message and title is not set, set it as title
            if role == "user":
                cursor = conn.execute(
                    "SELECT title FROM sessions WHERE session_id = ?", (session_id,)
                )
                row = cursor.fetchone()
                if row is None or row[0] is None:
                    # Set title as first 50 chars of content
                    title = content[:50].strip()
                    if not title:
                        title = "New chat"
                    conn.execute(
                        "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                        (title, session_id),
                    )
                else:
                    # Update updated_at timestamp
                    conn.execute(
                        "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                        (session_id,),
                    )
            else:
                # For assistant messages, just update updated_at
                conn.execute(
                    "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                    (session_id,),
                )
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

    def get_messages(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> List[dict]:
        """Return messages for a session with pagination, oldest first."""
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                """,
                (session_id, limit, offset),
            ).fetchall()
        return [
            {"role": row[0], "content": row[1], "created_at": row[2]} for row in rows
        ]

    def get_sessions(
        self, limit: int = 100, offset: int = 0, search: Optional[str] = None
    ) -> List[dict]:
        """Return list of sessions with metadata.
        Each dict contains: session_id, title, created_at, updated_at, message_count, preview.
        """
        with sqlite3.connect(self._db_path) as conn:
            if search:
                # Search in title or message content
                query = """
                    SELECT s.session_id, s.title, s.created_at, s.updated_at,
                           COUNT(m.id) as msg_count,
                           SUBSTR(
                               (SELECT content FROM conversation_messages
                                WHERE session_id = s.session_id AND role = 'user'
                                ORDER BY id LIMIT 1), 1, 100
                           ) as preview
                    FROM sessions s
                    LEFT JOIN conversation_messages m ON s.session_id = m.session_id
                    WHERE s.title LIKE ? OR m.content LIKE ?
                    GROUP BY s.session_id
                    ORDER BY s.updated_at DESC
                    LIMIT ? OFFSET ?
                """
                search_term = f"%{search}%"
                rows = conn.execute(
                    query, (search_term, search_term, limit, offset)
                ).fetchall()
            else:
                query = """
                    SELECT s.session_id, s.title, s.created_at, s.updated_at,
                           COUNT(m.id) as msg_count,
                           SUBSTR(
                               (SELECT content FROM conversation_messages
                                WHERE session_id = s.session_id AND role = 'user'
                                ORDER BY id LIMIT 1), 1, 100
                           ) as preview
                    FROM sessions s
                    LEFT JOIN conversation_messages m ON s.session_id = m.session_id
                    GROUP BY s.session_id
                    ORDER BY s.updated_at DESC
                    LIMIT ? OFFSET ?
                """
                rows = conn.execute(query, (limit, offset)).fetchall()
        sessions = []
        for row in rows:
            sessions.append(
                {
                    "session_id": row[0],
                    "title": row[1] or "Untitled",
                    "created_at": row[2],
                    "updated_at": row[3],
                    "message_count": row[4],
                    "preview": row[5] or "",
                }
            )
        return sessions

    def rename_session(self, session_id: str, title: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (title, session_id),
            )
            conn.commit()

    def delete_session(self, session_id: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM conversation_messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()

    def search_messages(
        self, query: str, limit: int = 100
    ) -> List[Tuple[str, str]]:
        """Search message content for given query.
        Returns list of (session_id, snippet) tuples.
        """
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT session_id, substr(content, 1, 200) as snippet
                FROM conversation_messages
                WHERE content LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (f"%{query}%", limit),
            ).fetchall()
        return [(row[0], row[1]) for row in rows]

    def get_session_title(self, session_id: str) -> Optional[str]:
        """Return the title of a session, or None if not found."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT title FROM sessions WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def get_sessions_count(self, search: Optional[str] = None) -> int:
        """Return the total number of sessions, optionally filtered by search term."""
        with sqlite3.connect(self._db_path) as conn:
            if search:
                query = """
                    SELECT COUNT(DISTINCT s.session_id)
                    FROM sessions s
                    LEFT JOIN conversation_messages m ON s.session_id = m.session_id
                    WHERE s.title LIKE ? OR m.content LIKE ?
                """
                search_term = f"%{search}%"
                cursor = conn.execute(query, (search_term, search_term))
            else:
                query = "SELECT COUNT(*) FROM sessions"
                cursor = conn.execute(query)
            row = cursor.fetchone()
            return row[0] if row else 0

    def delete_session_messages(self, session_id: str) -> None:
        """Delete all messages for a given session_id."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM conversation_messages WHERE session_id = ?", (session_id,))
            # Also update the session's updated_at timestamp to now?
            conn.execute(
                "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,),
            )
            conn.commit()
