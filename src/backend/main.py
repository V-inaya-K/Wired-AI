"""FastAPI entry point."""

from __future__ import annotations
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from backend.dependencies import build_service
from backend.schemas import ChatRequest, ChatResponse, DocumentInfo
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
            )
        )
    return documents
