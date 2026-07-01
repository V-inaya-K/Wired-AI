# ⚡ Wired AI

- Wired AI is an Agentic AI-powered Voice Research Assistant that enables users to interact with documents using voice or text.
- The system combines LangGraph, Retrieval-Augmented Generation (RAG), speech recognition, web search, and text-to-speech to provide intelligent, context-aware responses.

## ✨ Demo Video

Coming Soon

## 🔗 Wired AI Live Link

- Currently not deployed on the cloud as the application uses local AI models (Whisper, Piper, ChromaDB) for processing.

## 🧲 Tech Stack

- Python (FastAPI) for backend APIs.
- React + Vite for frontend.
- LangGraph for AI agent workflow.
- LlamaIndex for document indexing and retrieval.
- ChromaDB as vector database.
- HuggingFace Sentence Transformers for embeddings.
- Groq API (Llama-3.3-70B-Versatile) for LLM inference.
- Faster-Whisper for speech-to-text.
- Piper TTS for text-to-speech.
- SQLite for chat history.
- HTML, CSS, JavaScript for frontend.

## 🚀 Workflow

1. Upload one or more PDF documents.
2. Documents are indexed into ChromaDB.
3. Ask questions using text or voice.
4. LangGraph decides whether to use:
   - Local RAG
   - Web Search
   - Direct LLM response
5. The assistant returns the answer along with sources and optional speech output.

## 🌀 Features

- AI-powered research assistant using Groq LLM.
- Retrieval-Augmented Generation (RAG) using uploaded PDFs.
- Agentic routing with LangGraph.
- Voice input using Faster-Whisper.
- Voice output using Piper TTS.
- PDF upload and automatic indexing.
- Web search for recent information.
- Multi-turn conversation with chat memory.
- Source-aware answers.
- Local vector database using ChromaDB.
- FastAPI backend with React frontend.
- Clean and responsive UI.
- Error handling for invalid uploads and API failures.

## 🌊 Setup

1. Clone or download the repository.

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add the required keys.

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key

HF_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

PIPER_BIN=path_to_piper.exe
PIPER_VOICE=path_to_voice.onnx
```

4. Start the backend.

```bash
python -m uvicorn backend.main:app --reload --app-dir src
```

5. Start the frontend.

```bash
cd frontend
npm install
npm run dev
```

6. Open the application in your browser.

```
http://localhost:5173
```