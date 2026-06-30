"""Application settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed runtime settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    whisper_model: str = Field(default="base", alias="WHISPER_MODEL")
    piper_bin: str = Field(default="", alias="PIPER_BIN")
    piper_voice: str = Field(default="", alias="PIPER_VOICE")
    database_url: str = Field(default="sqlite:///./data/assistant.db", alias="DATABASE_URL")
    chroma_persist_dir: Path = Field(default=Path("./data/chroma"), alias="CHROMA_PERSIST_DIR")
    hf_embed_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="HF_EMBED_MODEL")
    upload_dir: Path = Field(default=Path("./data/uploads"), alias="UPLOAD_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    frontend_api_url: str = Field(default="http://localhost:8000", alias="FRONTEND_API_URL")


settings = Settings()
