"""API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request body."""

    session_id: str = Field(default="default")
    query: str


class ChatResponse(BaseModel):
    """Chat response body."""

    session_id: str
    route: str
    answer: str
    sources: list[dict[str, str]] = Field(default_factory=list)
    audio_path: str | None = None
    audio_url: str | None = None


class DocumentInfo(BaseModel):
    """Uploaded document metadata."""

    filename: str
    download_url: str
