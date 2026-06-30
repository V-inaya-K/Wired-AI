# Agentic Voice Research Assistant

Production-ready Python and React project for an agentic voice research assistant.

## Stack

- Python 3.11+
- FastAPI
- LangGraph
- LlamaIndex
- ChromaDB
- Faster-Whisper
- Piper TTS
- Groq
- Tavily
- React + Vite

## Recommended Python Version

Use Python 3.11 or 3.12. Several of the AI libraries used here still emit compatibility warnings on Python 3.14.

## Run

Backend:

```bash
uvicorn backend.main:app --reload --app-dir src
```

If you prefer setting the path explicitly in PowerShell:

```powershell
$env:PYTHONPATH="src"
uvicorn backend.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment

Copy `.env.example` to `.env` and provide:

- `GROQ_API_KEY`
- `TAVILY_API_KEY`
- `PIPER_BIN`
- `PIPER_VOICE`
