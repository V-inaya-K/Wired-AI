"""Local transcription with Faster-Whisper."""

from __future__ import annotations

from pathlib import Path


class TranscriptionService:
    """Transcribe local audio files to text."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None

    def _load_model(self) -> None:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self._model_name, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: str | Path) -> str:
        self._load_model()
        segments, _ = self._model.transcribe(str(audio_path))  # type: ignore[union-attr]
        return " ".join(segment.text.strip() for segment in segments).strip()

