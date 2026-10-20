
import { useState } from 'react'
import './App.css'

function App() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem('mini-juztina-theme') || 'dark',
  )

  const [conversations, setConversations] = useState([
    { id: 1, title: 'Nueva consulta', messages: [] },
  ])

  const [activeConversation, setActiveConversation] = useState(1)
  const [question, setQuestion] = useState('')
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(false)

  const currentConversation = conversations.find(
    (conversation) => conversation.id === activeConversation,
  )

  const messages = currentConversation?.messages ?? []

  function changeTheme() {
    const nextTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(nextTheme)
    localStorage.setItem('mini-juztina-theme', nextTheme)
  }

  function updateConversation(id, updater) {
    setConversations((previous) =>
      previous.map((conversation) =>
        conversation.id === id ? updater(conversation) : conversation,
      ),
    )
  }

  function newConversation() {
    if (loading) return

    const id = Date.now()

    setConversations((previous) => [
      { id, title: 'Nueva consulta', messages: [] },
      ...previous,
    ])

    setActiveConversation(id)
    setQuestion('')
    setSources([])
  }

  function selectConversation(id) {
    if (loading) return

    setActiveConversation(id)
    setQuestion('')
    setSources([])
  }

  function deleteConversation(event, id) {
    event.stopPropagation()
    if (loading) return

    const remaining = conversations.filter(
      (conversation) => conversation.id !== id,
    )

    if (remaining.length === 0) {
      const newId = Date.now()

      setConversations([
        { id: newId, title: 'Nueva consulta', messages: [] },
      ])
      setActiveConversation(newId)
      setQuestion('')
      setSources([])
      return
    }

    setConversations(remaining)

    if (activeConversation === id) {
      setActiveConversation(remaining[0].id)
      setQuestion('')
      setSources([])
    }
  }

  async function sendMessage(event) {
    event.preventDefault()

    const text = question.trim()

    if (!text || loading || !currentConversation) return

    const conversationId = activeConversation
    const isFirstMessage = currentConversation.messages.length === 0

    updateConversation(conversationId, (conversation) => ({
      ...conversation,
      title: isFirstMessage
        ? text.length > 30
          ? `${text.slice(0, 30)}…`
          : text
        : conversation.title,
      messages: [
        ...conversation.messages,
        { role: 'user', content: text },
      ],
    }))

    setQuestion('')
    setSources([])
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          conversation_id: String(conversationId),
        }),
      })

      if (!response.ok) {
        throw new Error(`Error del servidor: ${response.status}`)
      }

      const data = await response.json()

      updateConversation(conversationId, (conversation) => ({
        ...conversation,
        messages: [
          ...conversation.messages,
          {
            role: 'assistant',
            content: data.answer ?? 'El servidor no devolvió una respuesta.',
            status: data.status ?? 'answered',
          },
        ],
      }))

      setSources(Array.isArray(data.sources) ? data.sources : [])
    } catch {
      updateConversation(conversationId, (conversation) => ({
        ...conversation,
        messages: [
          ...conversation.messages,
          {
            role: 'assistant',
            content:
              'No se pudo conectar con el motor jurídico local. Comprueba que el backend esté iniciado. El servidor RAG todavía debe estar configurado para responder consultas.',
            status: 'connection_error',
          },
        ],
      }))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className={`app-shell theme-${theme}`}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <ScaleIcon />
          </div>

          <div>
            <h1>Mini-Juztina</h1>
            <p>Asistente jurídico local</p>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={newConversation}
          disabled={loading}
        >
          <span>＋</span> Nueva consulta
        </button>

        <div className="sidebar-label">CONVERSACIONES</div>

        <div className="conversation-list">
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`conversation-item ${
                activeConversation === conversation.id ? 'active' : ''
              }`}
            >
              <button
                className="conversation-select"
                onClick={() => selectConversation(conversation.id)}
                disabled={loading}
                title={conversation.title}
              >
                <ChatIcon />
                <span>{conversation.title}</span>
              </button>

              <button
                className="delete-chat-button"
                onClick={(event) =>
                  deleteConversation(event, conversation.id)
                }
                disabled={loading}
                aria-label={`Eliminar conversación: ${conversation.title}`}
                title="Eliminar conversación"
              >
                <TrashIcon />
              </button>
            </div>
          ))}
        </div>

        <div className="sidebar-bottom">
          <div className="privacy-card">
            <div className="privacy-icon">
              <LockIcon />
            </div>

            <div>
              <strong>Procesamiento local</strong>
              <p>Diseñado para mantener tus consultas en tu equipo.</p>
            </div>
          </div>

          <div className="sidebar-version">MINI-JUZTINA · PROTOTIPO</div>
        </div>
      </aside>

      <section className="chat-panel">
        <header className="topbar">
          <div className="mobile-brand">
            <ScaleIcon />
            <strong>Mini-Juztina</strong>
          </div>

          <div className="breadcrumb">
            <span>Asistente</span>
            <span className="breadcrumb-divider">/</span>
            <strong>Consulta jurídica</strong>
          </div>

          <div className="topbar-actions">
            <button
              className="theme-toggle"
              onClick={changeTheme}
              aria-label={
                theme === 'dark'
                  ? 'Activar modo claro'
                  : 'Activar modo oscuro'
              }
              title={
                theme === 'dark'
                  ? 'Activar modo claro'
                  : 'Activar modo oscuro'
              }
            >
              {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
              <span>
                {theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
              </span>
            </button>

            <div className="local-badge">
              <span className="status-dot" />
              Entorno local
            </div>
          </div>
        </header>

        <div className="chat-content">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon">
                <ScaleIcon />
              </div>

              <div className="eyebrow">ASISTENTE LEGAL INTELIGENTE</div>

              <h2>
                ¿Qué deseas consultar
                <br />
                sobre la legislación peruana?
              </h2>

              <p className="welcome-description">
                Consulta la Constitución Política del Perú y el Código Penal.
                Las respuestas deberán sustentarse en artículos recuperados
                de las fuentes jurídicas locales.
              </p>

              <div className="suggestion-grid">
                <button
                  className="suggestion-card"
                  onClick={() =>
                    setQuestion(
                      '¿Qué derechos reconoce la Constitución Política del Perú?',
                    )
                  }
                >
                  <span className="suggestion-icon blue">
                    <BookIcon />
                  </span>

                  <strong>Derechos constitucionales</strong>

                  <span>
                    Consultar derechos reconocidos por la Constitución
                  </span>

                  <span className="suggestion-arrow">↗</span>
                </button>

                <button
                  className="suggestion-card"
                  onClick={() =>
                    setQuestion(
                      '¿Qué establece el Código Penal sobre el delito consultado?',
                    )
                  }
                >
                  <span className="suggestion-icon violet">
                    <GavelIcon />
                  </span>

                  <strong>Código Penal</strong>

                  <span>Buscar disposiciones penales relevantes</span>

                  <span className="suggestion-arrow">↗</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <article
                  className={`message ${message.role}`}
                  key={`${activeConversation}-${index}`}
                >
                  <div className="message-avatar">
                    {message.role === 'assistant' ? (
                      <ScaleIcon />
                    ) : (
                      <UserIcon />
                    )}
                  </div>

                  <div className="message-body">
                    <div className="message-author">
                      {message.role === 'assistant' ? 'Mini-Juztina' : 'Tú'}
                    </div>

                    <div className="message-bubble">
                      <p>{message.content}</p>
                    </div>

                    {message.status === 'connection_error' && (
                      <span className="message-note">
                        Backend no conectado
                      </span>
                    )}
                  </div>
                </article>
              ))}

              {loading && (
                <div className="loading-indicator">
                  <span />
                  <span />
                  <span />
                  <p>Consultando el motor jurídico local...</p>
                </div>
              )}
            </div>
          )}

          <div className="composer-area">
            <form className="composer" onSubmit={sendMessage}>
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (
                    event.key === 'Enter' &&
                    !event.shiftKey &&
                    !event.nativeEvent.isComposing
                  ) {
                    event.preventDefault()
                    event.currentTarget.form.requestSubmit()
                  }
                }}
                placeholder="Escribe tu consulta jurídica..."
                rows={2}
                aria-label="Consulta jurídica"
              />

              <div className="composer-footer">
                <span>
                  <LockIcon />
                  Tus consultas se procesarán localmente cuando el backend
                  esté configurado.
                </span>

                <button
                  type="submit"
                  className="send-button"
                  disabled={!question.trim() || loading}
                  aria-label="Enviar consulta"
                >
                  <SendIcon />
                </button>
              </div>
            </form>

            <p className="disclaimer">
              Prototipo informativo. Las respuestas deben verificarse con las
              fuentes legales oficiales. No sustituye la asesoría de un abogado.
            </p>
          </div>
        </div>
      </section>

      <aside className="sources-panel">
        <div className="sources-header">
          <div>
            <div className="panel-eyebrow">TRANSPARENCIA</div>
            <h2>Fuentes jurídicas</h2>
          </div>

          <span className="sources-count">{sources.length}</span>
        </div>

        <p className="sources-intro">
          Consulta los artículos recuperados por el motor RAG para fundamentar
          la respuesta.
        </p>

        {sources.length === 0 ? (
          <div className="empty-sources">
            <div className="empty-sources-icon">
              <BookIcon />
            </div>

            <strong>Sin fuentes recuperadas</strong>

            <p>
              Cuando el backend local esté conectado, aquí aparecerán las normas,
              los artículos y sus fragmentos originales.
            </p>
          </div>
        ) : (
          <div className="source-list">
            {sources.map((source, index) => (
              <article
                className="source-card"
                key={`${source.law}-${source.article}-${index}`}
              >
                <div className="source-card-top">
                  <span className="source-number">FUENTE {index + 1}</span>

                  {source.score != null && (
                    <span className="source-score">
                      Relevancia: {Number(source.score).toFixed(2)}
                    </span>
                  )}
                </div>

                <h3>{source.law ?? 'Norma jurídica'}</h3>

                <div className="article-label">
                  {source.article ?? 'Artículo no especificado'}
                </div>

                <blockquote>
                  {source.excerpt ??
                    source.text ??
                    'Sin fragmento disponible.'}
                </blockquote>

                {source.url && (
                  <a href={source.url} target="_blank" rel="noreferrer">
                    Consultar fuente oficial ↗
                  </a>
                )}
              </article>
            ))}
          </div>
        )}

        <div className="sources-footer">
          <LockIcon />
          <p>
            Las fuentes visibles deben corresponder a documentos verificados e
            indexados localmente.
          </p>
        </div>
      </aside>
    </main>
  )
}

function ScaleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 3v17M7 21h10M5 7h14M12 4l-7 3m7-3 7 3M5 7l-3 7h6L5 7Zm14 0-3 7h6l-3-7Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H5l1.8-3.6A7.5 7.5 0 1 1 20 11.5Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function LockIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect
        x="5"
        y="10"
        width="14"
        height="11"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path
        d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v3"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 7h16M9 7V4h6v3m-9 0 1 13h10l1-13M10 11v5m4-5v5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function BookIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v17H6.5A2.5 2.5 0 0 0 4 22V5.5Zm0 0V22m5-15h7m-7 4h7"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function GavelIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="m14 5 5 5m-8-2 5-5 5 5-5 5-5-5Zm-4 4 5 5m-8-2 5-5 5 5-5 5-5-5Zm-1 9h15"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function UserIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M4 21a8 8 0 0 1 16 0"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="m21 3-7.5 18-3.7-7.8L2 9.5 21 3Zm0 0L9.8 13.2"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle
        cx="12"
        cy="12"
        r="4"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path
        d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.5 8.5 0 1 0 20.5 15.5Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default App
