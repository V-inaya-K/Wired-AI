"""LangGraph agent workflow."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from agents.prompts import ANSWER_PROMPT, PLANNER_PROMPT
from config.settings import settings

logger = logging.getLogger(__name__)

Route = Literal["direct", "rag", "web"]
MAX_HISTORY_MESSAGES = 6
MAX_RETRIEVED_CHUNKS = 2
MAX_CONTEXT_CHARS = 3000
MAX_ANSWER_CHARS = 1800
PRINTABLE_RE = re.compile(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uD7FF\uE000-\uFFFD]")


class AgentState(TypedDict, total=False):
    session_id: str
    query: str
    route: Route
    history: list[dict[str, str]]
    context: str
    answer: str
    sources: list[dict[str, str]]


class AgentGraph:
    """Compile and run the orchestration graph."""

    def __init__(self, llm: Any, rag_service: Any, web_search: Any, memory: Any) -> None:
        self._llm = llm
        self._rag = rag_service
        self._web_search = web_search
        self._memory = memory
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("plan", self._plan)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("search", self._search)
        graph.add_node("answer", self._answer)
        graph.set_entry_point("plan")
        graph.add_conditional_edges("plan", lambda state: state["route"], {"direct": "answer", "rag": "retrieve", "web": "search"})
        graph.add_edge("retrieve", "answer")
        graph.add_edge("search", "answer")
        graph.add_edge("answer", END)
        return graph.compile()

    def _plan(self, state: AgentState) -> AgentState:
        query_text = state["query"].lower()
        result = self._llm.invoke(f"{PLANNER_PROMPT}\nQuestion: {state['query']}")
        raw_route = str(getattr(result, "content", "") or "").strip().lower()
        route = raw_route if raw_route in {"direct", "rag", "web"} else "direct"
        local_docs = self._has_local_docs()
        disk_pdf_count = self._pdf_count_on_disk()
        web_only = self._looks_web_only(query_text)

        logger.debug(
            "Planner raw_route=%r normalized_route=%s local_docs=%s disk_pdf_count=%s web_only=%s query=%r",
            raw_route,
            route,
            local_docs,
            disk_pdf_count,
            web_only,
            state["query"],
        )

        if route not in {"direct", "rag", "web"}:
            route = "direct"

        # Force local retrieval whenever PDFs exist on disk and the query is not clearly web-only.
        if (local_docs or disk_pdf_count > 0) and not web_only:
            route = "rag"
            logger.debug("Planner forced route=rag because local documents are available.")
        elif route == "direct":
            logger.debug("Planner kept direct route because no local docs were detected or query looks web-only.")

        state["route"] = route  # type: ignore[assignment]
        history = [message.__dict__ for message in self._memory.get_history(state["session_id"], limit=MAX_HISTORY_MESSAGES)]
        state["history"] = history[-MAX_HISTORY_MESSAGES:]
        logger.debug("Plan selected route=%s query=%r history_count=%s", route, state["query"], len(state["history"]))
        return state

    def _has_local_docs(self) -> bool:
        """Check if the local RAG store has any indexed documents."""

        has_documents = getattr(self._rag, "has_documents", None)
        if callable(has_documents):
            try:
                return bool(has_documents())
            except Exception:
                return False
        return False

    @staticmethod
    def _pdf_count_on_disk() -> int:
        """Count PDFs in the upload directory as a fallback source-of-truth."""

        upload_dir = Path(settings.upload_dir)
        if not upload_dir.exists():
            return 0
        return len(list(upload_dir.glob("*.pdf")))

    @staticmethod
    def _looks_web_only(query_text: str) -> bool:
        """Heuristic for questions that should go to web search."""

        web_signals = (
            "today",
            "latest",
            "current",
            "news",
            "recent",
            "stock",
            "price",
            "weather",
            "live",
            "this week",
        )
        return any(signal in query_text for signal in web_signals)

    @staticmethod
    def _sanitize_text(text: str) -> str:
        """Remove control characters and collapse whitespace."""

        cleaned = PRINTABLE_RE.sub(" ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def _format_history_for_prompt(history: list[dict[str, str]]) -> str:
        """Keep only recent user messages to avoid echoing prior assistant output."""

        user_messages = [item.get("content", "").strip() for item in history if item.get("role") == "user" and item.get("content")]
        if not user_messages:
            return "No prior user messages."
        return "\n".join(f"- {message}" for message in user_messages[-3:])

    def _retrieve(self, state: AgentState) -> AgentState:
        chunks = self._rag.query(state["query"], top_k=MAX_RETRIEVED_CHUNKS)
        selected_chunks = chunks[:MAX_RETRIEVED_CHUNKS]
        context = "\n\n".join(chunk["text"] for chunk in selected_chunks if chunk.get("text"))
        state["context"] = context[:MAX_CONTEXT_CHARS]
        state["sources"] = selected_chunks
        logger.debug(
            "Retrieve produced chunks=%s context_chars=%s sources=%s",
            len(selected_chunks),
            len(state["context"]),
            [chunk.get("display") for chunk in selected_chunks],
        )
        if not selected_chunks:
            logger.warning("RAG retrieval returned zero chunks for query=%r", state["query"])
        return state

    def _search(self, state: AgentState) -> AgentState:
        results = self._web_search.search(state["query"])
        context_lines = []
        sources = []
        for result in results:
            context_lines.append(f"{result.get('title', '')}: {result.get('content', '')}")
            if result.get("url"):
                sources.append(str(result["url"]))
        state["context"] = "\n".join(context_lines)
        state["sources"] = sources
        return state

    def _answer(self, state: AgentState) -> AgentState:
        context = state.get("context", "")
        if context:
            context_block = (
                "Use the following retrieved document context to answer the question.\n"
                "If the answer is present in the context, answer directly and succinctly.\n"
                f"Context:\n{context}"
            )
        else:
            context_block = "No retrieved document context is available."
        history_block = self._format_history_for_prompt(state.get("history", []))
        prompt = (
            f"{ANSWER_PROMPT}\n"
            f"Recent user messages:\n{history_block}\n"
            f"{context_block}\n"
            f"Question: {state['query']}"
        )
        logger.debug(
            "Answer prompt preview=%r context_present=%s history_preview=%r",
            prompt[:1000],
            bool(context.strip()),
            history_block[:500],
        )
        response = self._llm.invoke(prompt)
        answer_text = self._sanitize_text(str(getattr(response, "content", "") or ""))
        if not answer_text:
            answer_text = "I could not generate a valid answer from the retrieved document."
        if not any(ch.isalpha() for ch in answer_text):
            answer_text = "I could not generate a valid answer from the retrieved document."
        if "no information available" in answer_text.lower() or "no context" in answer_text.lower():
            if context.strip():
                answer_text = context[:MAX_ANSWER_CHARS]
            else:
                answer_text = "I could not generate a valid answer from the retrieved document."
        state["answer"] = answer_text[:MAX_ANSWER_CHARS]
        logger.debug("Answer output preview=%r", state["answer"][:1000])
        return state

    def invoke(self, session_id: str, query: str) -> AgentState:
        return self._graph.invoke({"session_id": session_id, "query": query})
