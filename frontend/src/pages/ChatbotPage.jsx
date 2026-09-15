import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { sendChatMessage, fetchChatHistory } from '../services/api'

const QUICK_PROMPTS = [
  { label: '🌾 Farmers Assistance', prompt: 'Find schemes for farmers' },
  { label: '🎓 Education Support', prompt: 'Education assistance' },
  { label: '🏠 Housing Schemes', prompt: 'Housing schemes' },
  { label: '👩 Women Welfare', prompt: "Women's welfare schemes" },
  { label: '💼 Employment Support', prompt: 'Employment assistance' },
  { label: '🌾 தமிழ்: விவசாயி உதவி', prompt: 'நான் ஒரு விவசாயி. எனக்கு அரசு உதவி திட்டங்கள் என்ன?' },
]

export default function ChatbotPage() {
  const { session, isAuthenticated } = useAuth()
  const [messages, setMessages] = useState([
    {
      id: 'initial-greeting',
      sender: 'bot',
      text: 'Hello! I can help you find government schemes based on your age, state, district, occupation, income and other eligibility details. Tell me what support you are looking for.',
      recommendations: [],
      verification_required: [],
      created_at: new Date().toISOString(),
    },
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [loadingHistory, setLoadingHistory] = useState(false)
  const messagesEndRef = useRef(null)

  const messageCountRef = useRef(1)

  // Scroll to bottom when messages update
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load authenticated citizen chat history
  useEffect(() => {
    let isMounted = true

    async function loadHistory() {
      if (!isAuthenticated || !session?.access_token) return
      setLoadingHistory(true)
      try {
        const res = await fetchChatHistory(session.access_token, 20)
        if (isMounted && res && res.history && res.history.length > 0) {
          const historicalMessages = []
          // Reverse so oldest first, newest last
          const sorted = [...res.history].reverse()
          sorted.forEach((item) => {
            historicalMessages.push({
              id: `user-${item.id}`,
              sender: 'user',
              text: item.user_message,
              created_at: item.created_at,
            })
            historicalMessages.push({
              id: `bot-${item.id}`,
              sender: 'bot',
              text: item.bot_response,
              recommendations: [],
              verification_required: [],
              created_at: item.created_at,
            })
          })
          setMessages((prev) => [
            prev[0], // Keep initial greeting
            ...historicalMessages,
          ])
        }
      } catch {
        // Chat history failure is non-blocking
      } finally {
        if (isMounted) setLoadingHistory(false)
      }
    }

    loadHistory()
    return () => {
      isMounted = false
    }
  }, [isAuthenticated, session?.access_token])

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputMessage).trim()
    if (!text || sending) return

    setErrorMsg('')
    const count = messageCountRef.current++
    const userMsg = {
      id: `user-msg-${count}`,
      sender: 'user',
      text,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInputMessage('')
    setSending(true)

    try {
      const token = session?.access_token || null
      const response = await sendChatMessage(text, token)

      const botCount = messageCountRef.current++
      const botMsg = {
        id: `bot-msg-${botCount}`,
        sender: 'bot',
        text: response.message,
        language: response.language,
        intent: response.intent,
        recommendations: response.recommendations || [],
        verification_required: response.verification_required || [],
        created_at: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, botMsg])
    } catch (err) {
      setErrorMsg(err.message || 'Failed to process message. Please try again.')
    } finally {
      setSending(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleSendMessage()
  }

  return (
    <div className="chat-page-container">
      {/* Header Banner */}
      <div className="chat-header">
        <div className="chat-header-title">
          <div className="chat-header-icon" aria-hidden="true">🏛️</div>
          <div>
            <h1>AI Scheme Assistant</h1>
            <p className="chat-header-subtitle">
              Natural Language Government Welfare Scheme Discovery • Tamil & English Supported
            </p>
          </div>
        </div>
        <div className="chat-header-badges">
          <span className="badge badge-success">Deterministic Eligibility Verified</span>
          <span className="badge badge-neutral">Active Schemes Only</span>
        </div>
      </div>

      {/* Main Chat Layout */}
      <div className="chat-window">
        {/* Messages Scroll Area */}
        <div className="chat-messages-container" id="chat-messages-list" role="log" aria-live="polite">
          {loadingHistory && (
            <div className="chat-loading-history">
              <span className="spinner-small" aria-hidden="true" />
              <span>Loading your previous conversation...</span>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-message-row ${msg.sender === 'user' ? 'chat-row-user' : 'chat-row-bot'}`}
            >
              {msg.sender === 'bot' && (
                <div className="chat-avatar bot-avatar" aria-label="AI Assistant Avatar">
                  🤖
                </div>
              )}

              <div className={`chat-bubble ${msg.sender === 'user' ? 'bubble-user' : 'bubble-bot'}`}>
                <div className="chat-text">{msg.text}</div>

                {/* Recommendations Embedded Cards */}
                {msg.recommendations && msg.recommendations.length > 0 && (
                  <div className="chat-recommendations-section">
                    <div className="chat-recommendations-header">
                      <span>Verified Eligible Schemes ({msg.recommendations.length})</span>
                    </div>

                    <div className="chat-recommendations-grid">
                      {msg.recommendations.map((scheme) => (
                        <div key={scheme.scheme_id} className="chat-scheme-card">
                          <div className="chat-scheme-card-header">
                            <h4 className="chat-scheme-title">{scheme.scheme_name}</h4>
                            <span className="badge badge-success">🟢 Eligible</span>
                          </div>

                          {scheme.benefits && (
                            <p className="chat-scheme-benefits">{scheme.benefits}</p>
                          )}

                          <div className="chat-scheme-meta">
                            <span className="score-pill">
                              Match/Relevance Score: {scheme.relevance_score}/100
                            </span>
                            {scheme.deadline_status && (
                              <span className="deadline-pill">
                                📅 {scheme.deadline_status.replace(/_/g, ' ')}
                                {scheme.days_remaining !== null && scheme.days_remaining !== undefined && (
                                  <> ({scheme.days_remaining}d left)</>
                                )}
                              </span>
                            )}
                          </div>

                          <div className="chat-scheme-actions">
                            <Link
                              to={`/schemes/${scheme.scheme_id}`}
                              className="btn btn-outline btn-sm"
                            >
                              View Details
                            </Link>
                            {scheme.official_url && (
                              <a
                                href={scheme.official_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn btn-primary btn-sm"
                              >
                                Apply Officially ↗
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Verification Required Cards */}
                {msg.verification_required && msg.verification_required.length > 0 && (
                  <div className="chat-verification-section">
                    <div className="chat-verification-header">
                      ⚠️ Needs Demographic Verification ({msg.verification_required.length})
                    </div>
                    <div className="chat-recommendations-grid">
                      {msg.verification_required.map((scheme) => (
                        <div key={scheme.scheme_id} className="chat-scheme-card card-warning-border">
                          <div className="chat-scheme-card-header">
                            <h4 className="chat-scheme-title">{scheme.scheme_name}</h4>
                            <span className="badge badge-warning">🟡 Verification Needed</span>
                          </div>
                          <p className="chat-scheme-benefits">
                            Some criteria need confirmation before legal qualification can be established.
                          </p>
                          <div className="chat-scheme-meta">
                            <span className="score-pill">
                              Match/Relevance Score: {scheme.relevance_score}/100
                            </span>
                          </div>
                          <div className="chat-scheme-actions">
                            <Link
                              to={`/schemes/${scheme.scheme_id}`}
                              className="btn btn-outline btn-sm"
                            >
                              Verify Criteria
                            </Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="chat-avatar user-avatar" aria-label="Citizen Avatar">
                  👤
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className="chat-message-row chat-row-bot">
              <div className="chat-avatar bot-avatar" aria-label="AI Assistant Avatar">
                🤖
              </div>
              <div className="chat-bubble bubble-bot chat-bubble-loading">
                <div className="typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
                <span className="loading-text">Analyzing schemes and deterministic criteria...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="alert alert-error chat-error-bar" role="alert">
            <span>{errorMsg}</span>
            <button
              type="button"
              className="btn-dismiss"
              onClick={() => setErrorMsg('')}
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        {/* Quick Prompts Bar */}
        <div className="chat-quick-prompts">
          <span className="quick-prompts-label">Quick Prompts:</span>
          <div className="quick-prompts-scroll">
            {QUICK_PROMPTS.map((qp, idx) => (
              <button
                key={idx}
                type="button"
                className="btn-prompt-chip"
                onClick={() => handleSendMessage(qp.prompt)}
                disabled={sending}
              >
                {qp.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <form className="chat-input-bar" onSubmit={handleSubmit}>
          <input
            id="chat-message-input"
            type="text"
            className="chat-input-field"
            placeholder="Ask a question in English or தமிழ் (e.g. 'I am a 25 year old student looking for scholarships')..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={sending}
            maxLength={2000}
            autoComplete="off"
          />
          <button
            id="chat-send-button"
            type="submit"
            className="btn btn-primary chat-send-btn"
            disabled={sending || !inputMessage.trim()}
          >
            {sending ? (
              <span className="spinner-small" aria-hidden="true" />
            ) : (
              <>Send ↗</>
            )}
          </button>
        </form>

        <div className="chat-disclaimer">
          <small>
            Eligibility is determined deterministically by official statutory criteria. The AI Assistant assists with discovery and natural language understanding, never overriding deterministic eligibility.
          </small>
        </div>
      </div>
    </div>
  )
}
