import { useEffect, useMemo, useRef, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || '/api'
const THEME_KEY = 'avra-theme'

function IconButton({ label, title, active = false, onClick, children }) {
  return (
    <button
      type="button"
      className={`icon-button ${active ? 'active' : ''}`}
      onClick={onClick}
      aria-label={label}
      title={title || label}
    >
      {children}
    </button>
  )
}

function CopyIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 9a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-2" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /><path d="M6 6a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
}

function ShareIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 8a3 3 0 1 0-2.9-3.75" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /><path d="M8 14l8-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /><path d="M16 19a3 3 0 1 0-2.9-3.75" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /><circle cx="6" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" /><circle cx="18" cy="6" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" /><circle cx="18" cy="18" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" /></svg>
}

function MicIcon({ active = false }) {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a3 3 0 0 1 3 3v5a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /><path d="M5 11a7 7 0 0 0 14 0" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /><path d="M12 18v3" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />{active ? <circle cx="18" cy="6" r="2.3" fill="currentColor" /> : null}</svg>
}

function PanelIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5h6v14H5zM13 5h6v9h-6z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" /></svg>
}

function MoonIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.8A8.5 8.5 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" /></svg>
}

function SunIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.8" /><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
}

function SendIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 3 10 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /><path d="M21 3 14 21l-4-7-7-4 18-7Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" /></svg>
}

function StopIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2" fill="none" stroke="currentColor" strokeWidth="1.8" /></svg>
}

function PlusIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let value = bytes
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`
}

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || 'dark')
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID())
  const [sessionSearch, setSessionSearch] = useState('')
  const [sessions, setSessions] = useState([])
  const [messages, setMessages] = useState([])
  const [documents, setDocuments] = useState([])
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [route, setRoute] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [documentStatus, setDocumentStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [uploadingDocument, setUploadingDocument] = useState(false)
  const [error, setError] = useState('')
  const [recording, setRecording] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [documentsOpen, setDocumentsOpen] = useState(false)
  const [inputExpanded, setInputExpanded] = useState(true)
  const [sourceViewer, setSourceViewer] = useState(null)
  const [renameTarget, setRenameTarget] = useState(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const activeSessionTitle = useMemo(
    () => sessions.find((item) => item.session_id === sessionId)?.title || 'New chat',
    [sessions, sessionId],
  )

  const latestUserMessage = useMemo(
    () => [...messages].reverse().find((item) => item.role === 'user')?.content || query,
    [messages, query],
  )

  const canSubmit = useMemo(() => query.trim().length > 0 && !loading, [query, loading])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  useEffect(() => {
    void Promise.all([loadSessions(), loadDocuments()])
  }, [])

  useEffect(() => {
    void loadMessages(sessionId)
  }, [sessionId])

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void loadSessions(sessionSearch)
    }, 250)
    return () => window.clearTimeout(timeout)
  }, [sessionSearch])

  async function requestJson(url, options) {
    const response = await fetch(url, options)
    const text = await response.text()
    if (!response.ok) throw new Error(text || `Request failed (${response.status})`)
    return text ? JSON.parse(text) : null
  }

  async function loadSessions(search = '') {
    setLoadingSessions(true)
    try {
      const params = new URLSearchParams({ limit: '100', offset: '0' })
      if (search.trim()) params.set('search', search.trim())
      const data = await requestJson(`${API_URL}/sessions?${params.toString()}`)
      setSessions(data?.sessions ?? [])
    } catch {
      setSessions([])
    } finally {
      setLoadingSessions(false)
    }
  }

  async function loadMessages(id) {
    try {
      const data = await requestJson(`${API_URL}/sessions/${id}/messages?limit=200&offset=0`)
      setMessages(data?.messages ?? [])
    } catch {
      setMessages([])
    }
  }

  async function loadDocuments() {
    try {
      const data = await requestJson(`${API_URL}/documents`)
      setDocuments(Array.isArray(data) ? data : [])
    } catch {
      setDocuments([])
    }
  }

  function startNewChat() {
    setSessionId(crypto.randomUUID())
    setMessages([])
    setAnswer('')
    setSources([])
    setAudioUrl('')
    setQuery('')
    setError('')
  }

  async function clearChat() {
    try {
      await requestJson(`${API_URL}/sessions/${sessionId}/clear`, { method: 'POST' })
      setMessages([])
      setAnswer('')
      setSources([])
      setAudioUrl('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to clear chat')
    }
  }

  async function submitQuery(text, regenerate = false) {
    const payload = { session_id: sessionId, query: text }
    setLoading(true)
    setError('')
    try {
      const data = await requestJson(`${API_URL}/${regenerate ? 'chat/regenerate' : 'chat'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      setAnswer(data?.answer ?? '')
      setSources(Array.isArray(data?.sources) ? data.sources : [])
      setRoute(data?.route ?? '')
      setAudioUrl(data?.audio_url ?? '')
      setQuery(text)
      await loadMessages(sessionId)
      await loadSessions(sessionSearch)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
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
      const data = await requestJson(`${API_URL}/transcribe`, { method: 'POST', body: formData })
      setQuery(data?.text || '')
      if (data?.text) await submitQuery(data.text)
    } catch (err) {
      setError(err instanceof TypeError ? 'Could not reach the backend. Make sure the FastAPI server is running and CORS allows this frontend origin.' : err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
      setRecording(false)
    }
  }

  async function startVoiceCapture() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const file = new File([blob], `recording-${Date.now()}.webm`, { type: 'audio/webm' })
        await handleAudioUpload(file)
        stream.getTracks().forEach((track) => track.stop())
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setRecording(true)
    } catch {
      setError('Microphone access is required for push-to-talk.')
    }
  }

  function stopVoiceCapture() {
    mediaRecorderRef.current?.stop()
  }

  async function handleDocumentUpload(file) {
    if (!file) return
    setUploadingDocument(true)
    setError('')
    setDocumentStatus('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const data = await requestJson(`${API_URL}/ingest`, { method: 'POST', body: formData })
      setDocumentStatus(`Indexed ${data?.filename ?? file.name}`)
      await loadDocuments()
    } catch (err) {
      setError(err instanceof TypeError ? 'Could not reach the backend. Make sure the FastAPI server is running and CORS allows this frontend origin.' : err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setUploadingDocument(false)
    }
  }

  async function renameSession(session, title) {
    if (!title?.trim()) return
    try {
      await requestJson(`${API_URL}/sessions/${session}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      })
      await loadSessions(sessionSearch)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to rename chat')
    }
  }

  async function deleteSession(session) {
    if (!window.confirm('Delete this conversation?')) return
    try {
      await requestJson(`${API_URL}/sessions/${session}`, { method: 'DELETE' })
      if (session === sessionId) startNewChat()
      await loadSessions(sessionSearch)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete chat')
    }
  }

  async function deleteDocument(filename) {
    if (!window.confirm(`Delete ${filename}?`)) return
    try {
      await requestJson(`${API_URL}/documents/${filename}`, { method: 'DELETE' })
      await Promise.all([loadDocuments(), loadSessions(sessionSearch)])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete document')
    }
  }

  async function reindexDocument(filename) {
    try {
      await requestJson(`${API_URL}/documents/${filename}/reindex`, { method: 'POST' })
      await loadDocuments()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to reindex document')
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

  function openSource(source) {
    setSourceViewer(source)
  }

  return (
    <div className="shell">
      <div className="bg-orb orb-1" />
      <div className="bg-orb orb-2" />

      <div className="workspace">
        <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-top">
            <IconButton label={sidebarOpen ? 'Hide chats' : 'Show chats'} onClick={() => setSidebarOpen((value) => !value)}>
              <PanelIcon />
            </IconButton>
            <IconButton label="New chat" onClick={startNewChat}>
              <PlusIcon />
            </IconButton>
          </div>

          {sidebarOpen && (
            <>
              <label>
                Search chats
                <input value={sessionSearch} onChange={(e) => setSessionSearch(e.target.value)} placeholder="Title or message" />
              </label>
              <div className="sidebar-list">
                {loadingSessions ? (
                  <p className="muted">Loading chats...</p>
                ) : sessions.length === 0 ? (
                  <p className="muted">No chat history yet.</p>
                ) : (
                  sessions.map((item) => (
                    <article
                      key={item.session_id}
                      className={`session-item ${item.session_id === sessionId ? 'active' : ''}`}
                      onClick={() => setSessionId(item.session_id)}
                    >
                      <div>
                        <strong>{item.title}</strong>
                        <p>{item.preview || 'No preview'}</p>
                      </div>
                      <div className="session-actions">
                        <button className="ghost tiny" onClick={(e) => { e.stopPropagation(); setRenameTarget(item) }}>Rename</button>
                        <button className="ghost tiny" onClick={(e) => { e.stopPropagation(); void deleteSession(item.session_id) }}>Delete</button>
                      </div>
                    </article>
                  ))
                )}
              </div>
              <button className="ghost" onClick={clearChat}>Clear Chat</button>
            </>
          )}
        </aside>

        <main className="card">
          <header className="chat-header">
            <div>
              <p className="eyebrow brand">WIRED AI</p>
              <h1 className="hero-title">Ask by voice or text. Route to knowledge, web, or direct reasoning.</h1>
              <p className="lede">{activeSessionTitle}</p>
            </div>
            <div className="topbar-actions">
              <IconButton label={theme === 'dark' ? 'Light mode' : 'Dark mode'} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
                {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
              </IconButton>
              <IconButton label="Toggle input" active={inputExpanded} onClick={() => setInputExpanded((value) => !value)}>
                <span className="mini-label">{inputExpanded ? '⌄' : '⌃'}</span>
              </IconButton>
            </div>
          </header>

          <section className="controls">
            {inputExpanded && (
              <label className="composer">
                <span className="composer-label">Message</span>
                <textarea
                  rows="4"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask about your documents, current research, or anything else."
                />
              </label>
            )}

            <div className="composer-bar">
              <div className="composer-tools">
                <label className="icon-chip" title="Upload PDF">
                  <input type="file" accept="application/pdf" onChange={(e) => handleDocumentUpload(e.target.files?.[0])} />
                  <span>PDF</span>
                </label>
                <label className="icon-chip" title="Upload audio">
                  <input type="file" accept="audio/*" onChange={(e) => handleAudioUpload(e.target.files?.[0])} />
                  <span>Audio</span>
                </label>
                <IconButton label={recording ? 'Stop recording' : 'Push to talk'} active={recording} onClick={recording ? stopVoiceCapture : startVoiceCapture}>
                  {recording ? <StopIcon /> : <MicIcon active={recording} />}
                </IconButton>
              </div>
              <IconButton label="Send" onClick={() => submitQuery(query)} active={canSubmit} title={loading ? 'Working...' : 'Send'}>
                <SendIcon />
              </IconButton>
            </div>

            {documentStatus && <p className="muted">{documentStatus}</p>}
          </section>

          {error && <div className="error">{error}</div>}

          <section className="chat-panel">
            <div className="conversation-shell">
              <div className="panel-header slim">
                <h2>Conversation</h2>
                <div className="icon-row">
                  <IconButton label="Copy answer" onClick={copyAnswer} active={!!answer}>
                    <CopyIcon />
                  </IconButton>
                  <IconButton label="Share answer" onClick={shareAnswer} active={!!answer}>
                    <ShareIcon />
                  </IconButton>
                  <IconButton label="Clear chat" onClick={clearChat}>
                    <span className="mini-label">⟲</span>
                  </IconButton>
                </div>
              </div>

              <div className="chat-thread">
                {messages.length === 0 ? (
                  <div className="empty-state">
                    <p className="muted">Your conversation will appear here.</p>
                  </div>
                ) : (
                  messages.map((item, index) => (
                    <div key={`${item.created_at}-${index}`} className={`bubble ${item.role}`}>
                      <strong>{item.role === 'user' ? 'You' : 'Assistant'}</strong>
                      <p>{item.content}</p>
                    </div>
                  ))
                )}
              </div>

              <div className="answer-box">
                <div className="panel-header slim">
                  <strong>Latest answer</strong>
                  <IconButton label="Regenerate answer" onClick={() => submitQuery(latestUserMessage, true)} active={!!latestUserMessage && !loading}>
                    <span className="mini-label">↻</span>
                  </IconButton>
                </div>
                <p>{answer || 'Waiting for the assistant response.'}</p>
              </div>

              {route && <p className="muted status-line">Route: {route}</p>}
              {audioUrl && <audio controls src={`${API_URL}${audioUrl}`} className="audio-player" />}
            </div>

            <aside className="right-rail">
              <article className="panel slim-panel">
                <div className="panel-header slim">
                  <h2>Sources</h2>
                  <IconButton label="Toggle documents" onClick={() => setDocumentsOpen((value) => !value)} active={documentsOpen}>
                    <span className="mini-label">▣</span>
                  </IconButton>
                </div>
                {sources.length === 0 ? (
                  <p className="muted">No retrieved sources for this answer.</p>
                ) : (
                  <ul className="source-list">
                    {sources.map((source, index) => (
                      <li key={`${source.source || source.display || index}`}>
                        <button className="source-link" onClick={() => openSource(source)}>
                          {source.display || source.source || `Source ${index + 1}`}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </article>

              <article className="panel slim-panel">
                <div className="panel-header slim">
                  <h2>Documents</h2>
                  <IconButton label={documentsOpen ? 'Collapse documents' : 'Expand documents'} onClick={() => setDocumentsOpen((value) => !value)} active={documentsOpen}>
                    <span className="mini-label">{documentsOpen ? '−' : '+'}</span>
                  </IconButton>
                </div>
                {documentsOpen && (
                  documents.length === 0 ? (
                    <p className="muted">No uploaded PDFs yet.</p>
                  ) : (
                    <ul className="doc-list">
                      {documents.map((doc) => (
                        <li key={doc.filename} className="doc-row">
                          <div>
                            <strong>{doc.filename}</strong>
                            <p>{formatBytes(doc.size_bytes)} • {doc.uploaded_at || 'unknown date'}</p>
                          </div>
                          <div className="session-actions">
                            <a className="ghost tiny" href={`${API_URL}${doc.download_url}`} target="_blank" rel="noreferrer">View</a>
                            <button className="ghost tiny" onClick={() => reindexDocument(doc.filename)}>Re-index</button>
                            <button className="ghost tiny" onClick={() => deleteDocument(doc.filename)}>Delete</button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )
                )}
              </article>
            </aside>
          </section>
        </main>
      </div>

      {sourceViewer && (
        <div className="modal-backdrop" onClick={() => setSourceViewer(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="panel-header slim">
              <h2>Source Details</h2>
              <button className="ghost tiny" onClick={() => setSourceViewer(null)}>Close</button>
            </div>
            <p><strong>Document:</strong> {sourceViewer.display || sourceViewer.source || 'Unknown'}</p>
            <p><strong>Page:</strong> {sourceViewer.page || sourceViewer.page_number || 'Unknown'}</p>
            <p><strong>Chunk:</strong></p>
            <div className="chunk-box">{sourceViewer.text || 'No retrieved text available.'}</div>
          </div>
        </div>
      )}

      {renameTarget && (
        <div className="modal-backdrop" onClick={() => setRenameTarget(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="panel-header slim">
              <h2>Rename Chat</h2>
              <button className="ghost tiny" onClick={() => setRenameTarget(null)}>Close</button>
            </div>
            <label>
              New title
              <input
                defaultValue={renameTarget.title}
                onKeyDown={async (e) => {
                  if (e.key === 'Enter') {
                    await renameSession(renameTarget.session_id, e.currentTarget.value)
                    setRenameTarget(null)
                  }
                }}
              />
            </label>
            <p className="muted">Press Enter to save.</p>
          </div>
        </div>
      )}
    </div>
  )
}
