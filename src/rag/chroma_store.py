"""ChromaDB retrieval wrapper."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from config.settings import settings
from rag.embeddings import get_huggingface_embedding

logger = logging.getLogger(__name__)


class ChromaRAG:
    """Query a persistent Chroma knowledge base."""

    def __init__(self, persist_dir: Path) -> None:
        self._persist_dir = persist_dir
        self._client = None
        self._collection = None
        self._vector_store = None
        self._storage_context = None
        self._embed_model = None
        self._index = None
        self._retriever = None
        self._collection_count = -1
        self._persist_fingerprint = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize Chroma and LlamaIndex components once."""

        import chromadb
        from llama_index.core import StorageContext, VectorStoreIndex
        from llama_index.vector_stores.chroma import ChromaVectorStore

        logger.debug("Initializing ChromaRAG persist_dir=%s embed_model=%s", self._persist_dir, settings.hf_embed_model)
        self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        self._collection = self._client.get_or_create_collection("assistant_knowledge_base")
        self._vector_store = ChromaVectorStore(chroma_collection=self._collection)
        self._storage_context = StorageContext.from_defaults(vector_store=self._vector_store)
        self._embed_model = get_huggingface_embedding(settings.hf_embed_model)
        self._index = VectorStoreIndex.from_vector_store(
            vector_store=self._vector_store,
            storage_context=self._storage_context,
            embed_model=self._embed_model,
        )
        self._retriever = self._index.as_retriever(similarity_top_k=2)
        self._collection_count = self._collection.count()
        self._persist_fingerprint = self._fingerprint()
        logger.debug(
            "ChromaRAG initialized collection_count=%s fingerprint=%s",
            self._collection_count,
            self._persist_fingerprint,
        )

    def _fingerprint(self) -> str:
        """Build a simple fingerprint for the persisted Chroma state."""

        try:
            stat = self._persist_dir.stat()
            return f"{stat.st_mtime_ns}:{stat.st_size}"
        except Exception:
            return "missing"

    def _refresh_if_needed(self) -> None:
        """Rebind Chroma components when the underlying collection changes."""

        if self._collection is None:
            self._initialize()
            return

        fingerprint = self._fingerprint()
        if fingerprint != self._persist_fingerprint:
            logger.debug(
                "Persist fingerprint changed old=%s new=%s; reinitializing ChromaRAG",
                self._persist_fingerprint,
                fingerprint,
            )
            self._initialize()
            return

        try:
            current_count = self._collection.count()
        except Exception:
            current_count = -1

        if current_count != self._collection_count:
            logger.debug(
                "Collection count changed old=%s new=%s; reinitializing ChromaRAG",
                self._collection_count,
                current_count,
            )
            self._initialize()

    def has_documents(self) -> bool:
        """Return whether the vector store has any indexed documents."""

        if self._collection is None:
            return False
        return self._collection.count() > 0

    @staticmethod
    def _format_node(node: Any) -> dict[str, str]:
        """Format a retrieved node with its text and metadata."""

        text = ""
        metadata = {}
        if hasattr(node, "node"):
            text = getattr(node.node, "get_content", lambda: "")()
            metadata = getattr(node.node, "metadata", {}) or {}
        elif hasattr(node, "get_content"):
            text = node.get_content()
            metadata = getattr(node, "metadata", {}) or {}
        else:
            text = str(node)

        prefix_parts = []
        if metadata.get("file_name"):
            prefix_parts.append(f"file={metadata['file_name']}")
        if metadata.get("page_label"):
            prefix_parts.append(f"page={metadata['page_label']}")
        if metadata.get("source"):
            prefix_parts.append(f"source={metadata['source']}")

        source_name = metadata.get("file_name") or metadata.get("source") or "document"
        return {
            "source": str(source_name),
            "page": str(metadata.get("page_label", "")),
            "text": text.strip(),
            "display": f"{source_name}" + (f" (page {metadata['page_label']})" if metadata.get("page_label") else ""),
        }

    def query(self, question: str, top_k: int = 2) -> list[dict[str, str]]:
        self._refresh_if_needed()
        if self._retriever is None:
            self._initialize()
        retriever = self._retriever
        if retriever is None:
            return []
        logger.debug("Running retrieval question=%r top_k=%s collection_count=%s", question, top_k, self._collection_count)
        try:
            retriever.similarity_top_k = top_k
        except Exception:
            pass
        try:
            nodes = retriever.retrieve(question)
        except Exception as exc:
            message = str(exc)
            if "does not exist" in message or "NotFoundError" in type(exc).__name__:
                logger.warning("Stale Chroma retriever detected; reinitializing and retrying.")
                self._initialize()
                retriever = self._retriever
                if retriever is None:
                    return []
                try:
                    retriever.similarity_top_k = top_k
                except Exception:
                    pass
                nodes = retriever.retrieve(question)
            else:
                raise
        logger.debug("Retrieved %s nodes for question=%r", len(nodes), question)
        for i, node in enumerate(nodes):
            try:
                preview = node.node.get_content()[:300]
            except Exception:
                preview = "<unavailable>"
            logger.debug("Node %s preview=%r", i, preview)
        return [self._format_node(node) for node in nodes]
