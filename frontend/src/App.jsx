import { useEffect, useMemo, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || '/api'

export default function App() {
  const [sessionId, setSessionId] = useState('default')
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [documents, setDocuments] = useState([])
  const [audioPath, setAudioPath] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [documentStatus, setDocumentStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploadingDocument, setUploadingDocument] = useState(false)
  const [error, setError] = useState('')
  const [recording, setRecording] = useState(false)

  const canSubmit = useMemo(() => query.trim().length > 0 && !loading, [query, loading])

  useEffect(() => {
    void loadDocuments()
  }, [])

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_URL}/documents`)
      if (!response.ok) return
      const data = await response.json()
      setDocuments(Array.isArray(data) ? data : [])
    } catch {
      setDocuments([])
    }
  }

  async function submitQuery(text) {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          query: text,
        }),
      })

      const responseText = await response.text()

      if (!response.ok) {
        throw new Error(responseText || `Request failed (${response.status})`)
      }

      const data = JSON.parse(responseText)

      setAnswer(data.answer ?? '')
      setAudioPath(data.audio_path ?? '')
      setAudioUrl(data.audio_url ?? '')
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError(String(err))
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleAudioUpload(file) {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(`${API_URL}/transcribe`, { method: 'POST', body: formData })
      if (!response.ok) throw new Error(`Transcription failed: ${response.status}`)
      const data = await response.json()
      setQuery(data.text || '')
      if (data.text) await submitQuery(data.text)
    } catch (err) {
      setError(
        err instanceof TypeError
          ? 'Could not reach the backend. Make sure the FastAPI server is running and CORS allows this frontend origin.'
          : err instanceof Error
            ? err.message
            : 'Unknown error',
      )
    } finally {
      setLoading(false)
      setRecording(false)
    }
  }

  async function handleDocumentUpload(file) {
    if (!file) return
    setUploadingDocument(true)
    setError('')
    setDocumentStatus('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(`${API_URL}/ingest`, { method: 'POST', body: formData })
      if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail || `Upload failed: ${response.status}`)
      }
      const data = await response.json()
      setDocumentStatus(`Indexed ${data.filename}`)
    } catch (err) {
      setError(
        err instanceof TypeError
          ? 'Could not reach the backend. Make sure the FastAPI server is running and CORS allows this frontend origin.'
          : err instanceof Error
            ? err.message
            : 'Unknown error',
      )
    } finally {
      setUploadingDocument(false)
      void loadDocuments()
    }
  }

  async function copyAnswer() {
    if (!answer) return
    await navigator.clipboard.writeText(answer)
  }

  async function shareAnswer() {
    if (!answer) return
    if (navigator.share) {
      await navigator.share({ title: 'Assistant Answer', text: answer })
    } else {
      await copyAnswer()
    }
  }

  return (
    <div className="shell">
      <div className="bg-orb orb-1" />
      <div className="bg-orb orb-2" />

      <main className="card">
        <header className="hero">
          <p className="eyebrow">Agentic Voice Research Assistant</p>
          <h1>Ask by voice or text. Route to knowledge, web, or direct reasoning.</h1>
          <p className="lede">
            A local-first assistant with FastAPI, LangGraph, ChromaDB, Groq, Faster-Whisper, and Piper TTS.
          </p>
        </header>

        <section className="controls">
          <label>
            Session ID
            <input value={sessionId} onChange={(e) => setSessionId(e.target.value)} />
          </label>

          <label>
            Your question
            <textarea
              rows="5"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about your documents, current research, or anything else."
            />
          </label>

          <div className="actions">
            <button disabled={!canSubmit} onClick={() => submitQuery(query)}>
              {loading ? 'Working...' : 'Send'}
            </button>

            <label className="file-button">
              {recording ? 'Processing audio...' : 'Upload audio'}
              <input
                type="file"
                accept="audio/*"
                onChange={(e) => handleAudioUpload(e.target.files?.[0])}
              />
            </label>

            <label className="file-button">
              {uploadingDocument ? 'Indexing document...' : 'Upload PDF'}
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => handleDocumentUpload(e.target.files?.[0])}
              />
            </label>
          </div>
          {documentStatus && <p className="muted">{documentStatus}</p>}
        </section>

        {error && <div className="error">{error}</div>}

        <section className="result-grid">
          <article className="panel">
            <h2>Answer</h2>
            <p>{answer || 'Your response will appear here.'}</p>
            <div className="actions">
              <button onClick={copyAnswer} disabled={!answer}>Copy</button>
              <button onClick={shareAnswer} disabled={!answer}>Share</button>
            </div>
            {audioPath && <p className="muted">Audio: {audioPath}</p>}
            {audioUrl && (
              <audio controls src={`${API_URL}${audioUrl}`} style={{ width: '100%', marginTop: '12px' }} />
            )}
          </article>

          <article className="panel">
            <h2>Sources</h2>
            {documents.length === 0 ? (
              <p className="muted">No uploaded PDFs yet.</p>
            ) : (
              <ul>
                {documents.map((doc) => (
                  <li key={doc.filename}>
                    {doc.filename}{' '}
                    <a href={`${API_URL}${doc.download_url}`} target="_blank" rel="noreferrer">
                      Download
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </section>
      </main>
    </div>
  )
}
