"""Local TTS using Piper."""

from __future__ import annotations

import subprocess
from pathlib import Path


class TTSService:
    """Synthesize audio from text."""

    def __init__(self, piper_bin: str, voice_path: str) -> None:
        self._piper_bin = piper_bin
        self._voice_path = voice_path

    def synthesize(self, text: str, output_path: str | Path) -> Path:
        if not self._piper_bin or not self._voice_path:
            raise RuntimeError("Piper is not configured")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [self._piper_bin, "--model", self._voice_path, "--output_file", str(output)],
            input=text.encode("utf-8"),
            check=True,
        )
        return output

