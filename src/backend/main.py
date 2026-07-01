"""FastAPI entry point."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.dependencies import build_service
from backend.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentInfo,
    MessageResponse,
    MessagesResponse,
    SearchResponse,
    SearchResult,
    SessionInfo,
    SessionListResponse,
    SessionRenameRequest,
)
from config.settings import settings
from rag.ingestion import rebuild_knowledge_base, save_uploaded_pdf
from speech.transcription import TranscriptionService
from utilities.logging import configure_logging

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Voice Research Assistant",
    version="0.1.0",
)

# Enable CORS for frontend (Streamlit/React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # React
        "http://127.0.0.1:3000",
        "http://localhost:8501",  # Streamlit
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
service = build_service()
output_dir = Path("./data/output")
upload_dir = settings.upload_dir
output_dir.mkdir(parents=True, exist_ok=True)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(output_dir)), name="audio")
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    rebuild_knowledge_base(settings.upload_dir, settings.chroma_persist_dir)
    result = service.chat(request.session_id, request.query, output_dir / "audio.wav")
    if result.get("audio_path"):
        result["audio_url"] = f"/audio/{Path(result['audio_path']).name}"
    return ChatResponse(**result)


@app.post("/chat/regenerate", response_model=ChatResponse)
def regenerate(request: ChatRequest) -> ChatResponse:
    """Re-run the last user query with the same session history."""

    rebuild_knowledge_base(settings.upload_dir, settings.chroma_persist_dir)
    result = service.regenerate(request.session_id, request.query, output_dir / "audio.wav")
    if result.get("audio_path"):
        result["audio_url"] = f"/audio/{Path(result['audio_path']).name}"
    return ChatResponse(**result)


@app.post("/transcribe")
def transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    target = settings.upload_dir / file.filename
    with target.open("wb") as handle:
        handle.write(file.file.read())
    text = TranscriptionService(settings.whisper_model).transcribe(target)
    return {"text": text}


@app.post("/ingest")
def ingest(file: UploadFile = File(...)) -> dict[str, str]:
    """Upload a PDF and add it to the local knowledge base."""

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        logger.debug("Starting ingest filename=%s content_type=%s", file.filename, file.content_type)
        contents = file.file.read()
        logger.debug("Uploaded bytes=%s", len(contents))
        saved_path = save_uploaded_pdf(settings.upload_dir, file.filename, contents)
        logger.debug("Saved uploaded PDF to %s", saved_path)
        rebuild_knowledge_base(settings.upload_dir, settings.chroma_persist_dir)
        logger.debug("Ingest rebuild complete for upload_dir=%s", settings.upload_dir)
        return {"status": "ok", "filename": saved_path.name}
    except Exception as exc:
        logger.exception("Failed to ingest document")
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {exc}") from exc


@app.get("/documents", response_model=list[DocumentInfo])
def list_documents() -> list[DocumentInfo]:
    """Return uploaded PDF documents available for download."""

    if not upload_dir.exists():
        return []
    documents: list[DocumentInfo] = []
    for path in sorted(upload_dir.glob("*.pdf")):
        documents.append(
            DocumentInfo(
                filename=path.name,
                download_url=f"/uploads/{path.name}",
                size_bytes=path.stat().st_size,
                uploaded_at=datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            )
        )
    return documents


@app.delete("/documents/{filename}")
def delete_document(filename: str) -> dict[str, str]:
    """Delete a PDF and rebuild the local knowledge base."""

    path = upload_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    path.unlink()
    rebuild_knowledge_base(settings.upload_dir, settings.chroma_persist_dir)
    return {"status": "ok", "filename": filename}


@app.post("/documents/{filename}/reindex")
def reindex_document(filename: str) -> dict[str, str]:
    """Rebuild the local knowledge base from the current uploads directory."""

    path = upload_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    rebuild_knowledge_base(settings.upload_dir, settings.chroma_persist_dir)
    return {"status": "ok", "filename": filename}


# Session management endpoints
@app.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
) -> SessionListResponse:
    """List sessions with optional search."""
    sessions = service.memory.get_sessions(limit=limit, offset=offset, search=search)
    total = service.memory.get_sessions_count(search=search)
    return SessionListResponse(sessions=[SessionInfo(**s) for s in sessions], total=total)


@app.get("/sessions/{session_id}", response_model=SessionInfo)
def get_session(session_id: str) -> SessionInfo:
    """Get a single session by ID."""
    sessions = service.memory.get_sessions(limit=1000, offset=0, search=None)
    for s in sessions:
        if s["session_id"] == session_id:
            return SessionInfo(**s)
    raise HTTPException(status_code=404, detail="Session not found")


@app.patch("/sessions/{session_id}", response_model=SessionInfo)
def rename_session(session_id: str, request: SessionRenameRequest) -> SessionInfo:
    """Rename a session."""
    service.memory.rename_session(session_id, request.title)
    sessions = service.memory.get_sessions(limit=1000, offset=0, search=None)
    for s in sessions:
        if s["session_id"] == session_id:
            return SessionInfo(**s)
    raise HTTPException(status_code=404, detail="Session not found")


@app.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str) -> None:
    """Delete a session and all its messages."""
    service.memory.delete_session(session_id)
    return None


@app.post("/sessions/{session_id}/clear", status_code=204)
def clear_session(session_id: str) -> None:
    """Clear only the active conversation messages."""

    service.memory.delete_session_messages(session_id)
    return None


@app.get("/sessions/{session_id}/messages", response_model=MessagesResponse)
def get_session_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> MessagesResponse:
    """Get messages for a session."""
    messages = service.memory.get_messages(session_id=session_id, limit=limit, offset=offset)
    # Convert to MessageResponse models
    msg_responses = [MessageResponse(**m) for m in messages]
    return MessagesResponse(messages=msg_responses)


@app.get("/sessions/search", response_model=SearchResponse)
def search_messages(
    q: str = Query(..., min_length=1),
    limit: int = Query(100, ge=1, le=1000),
) -> SearchResponse:
    """Search messages across sessions."""
    results = service.memory.search_messages(query=q, limit=limit)
    # Get session title for each result
    search_results = []
    for session_id, snippet in results:
        title = service.memory.get_session_title(session_id)
        search_results.append(
            SearchResult(session_id=session_id, snippet=snippet, title=title)
        )
    return SearchResponse(results=search_results)
