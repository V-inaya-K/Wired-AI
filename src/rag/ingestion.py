"""PDF ingestion pipeline."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from config.settings import settings
from rag.embeddings import get_huggingface_embedding

logger = logging.getLogger(__name__)


def ingest_pdfs(pdf_paths: Iterable[Path], persist_dir: Path) -> None:
    """Ingest PDFs into ChromaDB via LlamaIndex."""

    from llama_index.core import Document, StorageContext, VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.core.node_parser import SentenceSplitter
    from pypdf import PdfReader
    import chromadb

    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection("assistant_knowledge_base")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    docs = []
    pdf_paths = list(pdf_paths)
    logger.debug("Starting PDF ingestion. persist_dir=%s pdf_count=%s", persist_dir, len(pdf_paths))
    for pdf_path in pdf_paths:
        logger.debug("Reading PDF: %s size=%s", pdf_path, pdf_path.stat().st_size if pdf_path.exists() else "missing")
        reader = PdfReader(str(pdf_path))
        logger.debug("PDF pages detected: %s for %s", len(reader.pages), pdf_path.name)
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                logger.debug("Skipping empty page %s in %s", page_number, pdf_path.name)
                continue
            docs.append(
                Document(
                    text=text,
                    metadata={
                        "file_name": pdf_path.name,
                        "source": str(pdf_path),
                        "page_label": str(page_number),
                    },
                )
            )
    logger.debug("Documents extracted for indexing: %s", len(docs))
    embed_model = get_huggingface_embedding(settings.hf_embed_model)
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    logger.debug(
        "Indexing with embed_model=%s chunk_size=%s chunk_overlap=%s",
        settings.hf_embed_model,
        512,
        50,
    )
    VectorStoreIndex.from_documents(
        docs,
        storage_context=storage_context,
        embed_model=embed_model,
        transformations=[splitter],
    )
    try:
        logger.debug("Post-index collection count=%s", collection.count())
    except Exception:
        logger.exception("Unable to read collection count after indexing")


def rebuild_knowledge_base(upload_dir: Path, persist_dir: Path) -> None:
    """Rebuild the Chroma knowledge base from the PDFs currently on disk."""

    import chromadb

    logger.debug("Rebuilding knowledge base from upload_dir=%s persist_dir=%s", upload_dir, persist_dir)
    if persist_dir.exists():
        logger.debug("Removing existing Chroma persist dir: %s", persist_dir)
        shutil.rmtree(persist_dir, ignore_errors=True)
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        client.delete_collection("assistant_knowledge_base")
    except Exception:
        pass

    # Recreate a fresh client/collection after removing the old persisted DB.
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection("assistant_knowledge_base")
    logger.debug("Fresh collection created: %s", collection.name)

    pdf_paths = sorted(upload_dir.glob("*.pdf")) if upload_dir.exists() else []
    logger.debug("Current uploaded PDFs found on disk: %s", [path.name for path in pdf_paths])
    if pdf_paths:
        ingest_pdfs(pdf_paths, persist_dir)
    else:
        logger.debug("No PDFs found on disk during rebuild; index will remain empty.")


def save_uploaded_pdf(upload_dir: Path, filename: str, content: bytes) -> Path:
    """Persist an uploaded PDF to disk and return the saved path."""

    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid4().hex}_{Path(filename).name}"
    target = upload_dir / safe_name
    target.write_bytes(content)
    return target
