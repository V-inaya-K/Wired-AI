"""Application service."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from agents.graph import AgentGraph
from memory.sqlite_memory import SQLiteMemory
from speech.tts import TTSService

logger = logging.getLogger(__name__)


class AssistantService:
    """High-level assistant orchestration service."""

    def __init__(self, graph: AgentGraph, memory: SQLiteMemory, tts: TTSService) -> None:
        self._graph = graph
        self._memory = memory
        self._tts = tts

    @property
    def memory(self) -> SQLiteMemory:
        """Expose the conversation store for HTTP endpoints."""

        return self._memory

    def chat(self, session_id: str, query: str, audio_output: Path) -> dict:
        logger.debug("Chat start session_id=%s query=%r", session_id, query)
        self._memory.add_message(session_id, "user", query)
        state = self._graph.invoke(session_id=session_id, query=query)
        logger.debug(
            "Graph returned route=%s context_chars=%s source_count=%s",
            state.get("route"),
            len(str(state.get("context", ""))),
            len(state.get("sources", [])),
        )
        answer = str(state.get("answer", "") or "").strip()
        if not answer:
            answer = "I could not generate a valid answer from the retrieved document."
        if any(ord(char) < 32 and char not in "\n\r\t" for char in answer):
            logger.warning("Sanitized non-printable characters from answer for session %s", session_id)
        self._memory.add_message(session_id, "assistant", answer)
        output_file = audio_output.with_name(f"{uuid4().hex}.wav")
        audio_path = None
        try:
            audio_path = str(self._tts.synthesize(answer, output_file))
        except Exception:
            audio_path = None
        logger.debug("Chat end session_id=%s answer_preview=%r audio_path=%s", session_id, answer[:500], audio_path)
        return {
            "session_id": session_id,
            "route": state.get("route", "direct"),
            "answer": answer,
            "sources": state.get("sources", []),
            "audio_path": audio_path,
        }

    def regenerate(self, session_id: str, query: str, audio_output: Path) -> dict:
        """Regenerate an answer without appending a duplicate user message."""

        logger.debug("Regenerate start session_id=%s query=%r", session_id, query)
        state = self._graph.invoke(session_id=session_id, query=query)
        answer = str(state.get("answer", "") or "").strip()
        if not answer:
            answer = "I could not generate a valid answer from the retrieved document."
        output_file = audio_output.with_name(f"{uuid4().hex}.wav")
        audio_path = None
        try:
            audio_path = str(self._tts.synthesize(answer, output_file))
        except Exception:
            audio_path = None
        return {
            "session_id": session_id,
            "route": state.get("route", "direct"),
            "answer": answer,
            "sources": state.get("sources", []),
            "audio_path": audio_path,
        }
