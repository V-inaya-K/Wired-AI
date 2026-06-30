"""Shared embedding helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=2)
def get_huggingface_embedding(model_name: str) -> Any:
    """Return a cached Hugging Face embedding model."""

    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(model_name=model_name)


DEFAULT_EMBED_MODEL = get_huggingface_embedding("sentence-transformers/all-MiniLM-L6-v2")
