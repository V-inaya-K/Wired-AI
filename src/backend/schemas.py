"""API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


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
    size_bytes: int = 0
    uploaded_at: str = ""


class SessionInfo(BaseModel):
    """Session metadata."""

    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    preview: str


class SessionListResponse(BaseModel):
    """Response for listing sessions."""

    sessions: List[SessionInfo]
    total: int


class SessionRenameRequest(BaseModel):
    """Request to rename a session."""

    title: str


class MessageResponse(BaseModel):
    """Single message response."""

    role: str
    content: str
    created_at: str


class MessagesResponse(BaseModel):
    """Response for getting messages of a session."""

    messages: List[MessageResponse]


class SearchResult(BaseModel):
    """Search result snippet."""

    session_id: str
    snippet: str
    title: Optional[str] = None


class SearchResponse(BaseModel):
    """Response for searching messages."""

    results: List[SearchResult]
