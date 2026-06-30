"""Dependency wiring."""

from __future__ import annotations

from langchain_groq import ChatGroq

from agents.graph import AgentGraph
from config.settings import settings
from database.sqlite import ensure_database
from memory.sqlite_memory import SQLiteMemory
from rag.chroma_store import ChromaRAG
from speech.tts import TTSService
from tools.web_search import WebSearchTool


def build_service():
    """Create the assistant service with all dependencies."""

    from backend.service import AssistantService

    db_path = ensure_database(settings.database_url)
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    llm = ChatGroq(api_key=settings.groq_api_key, model=settings.groq_model)
    memory = SQLiteMemory(db_path)
    rag = ChromaRAG(settings.chroma_persist_dir)
    web = WebSearchTool(settings.tavily_api_key)
    tts = TTSService(settings.piper_bin, settings.piper_voice)
    graph = AgentGraph(llm=llm, rag_service=rag, web_search=web, memory=memory)
    return AssistantService(graph=graph, memory=memory, tts=tts)

