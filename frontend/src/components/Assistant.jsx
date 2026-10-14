import { useEffect, useRef, useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext.jsx'
import { apiFetch } from '../api.js'

export default function Assistant() {
  const { t, pick, lang } = useTranslation()
  const [messages, setMessages] = useState([
    { role: 'ai', textKey: 'ai.greeting' },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  // Optional live-weather summary saved by the Weather page (place name +
  // metrics only, per-tab). Shown as a removable chip; sent only while shown.
  const [wxContext, setWxContext] = useState(null)
  const [contextDismissed, setContextDismissed] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [messages, busy])

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem('sa_wx_context')
      if (raw) setWxContext(JSON.parse(raw))
    } catch { /* no context available */ }
  }, [])

  async function send(e) {
    e.preventDefault()
    const question = input.trim()
    if (!question || busy) return
    setError('')
    setBusy(true)
    setInput('')
    setMessages((m) => [...m, { role: 'user', text: question }])
    const body = { question, language: lang }
    if (wxContext && !contextDismissed) body.weather = wxContext
    try {
      const res = await apiFetch('/api/assistant', { method: 'POST', body })
      const answer = res.answer?.[lang] ?? res.answer?.en ??
        (Object.values(res.answer || {})[0] || '')
      setMessages((m) => [...m, { role: 'ai', text: answer, provider: res.provider }])
    } catch (err) {
      setError(err.code === 'network' ? t('ai.error') : (err.message || t('ai.error')))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="page-section">
      <div className="container container-narrow">
        <div className="section-head">
          <h2>🤖 {t('ai.title')}</h2>
          <p>{t('ai.subtitle')}</p>
        </div>

        <div className="chat-card">
          <div className="chat-log" role="log" aria-live="polite">
            {messages.map((m, idx) => (
              <div key={idx} className={`chat-bubble ${m.role === 'user' ? 'user' : 'ai'}`}>
                {m.role === 'ai' && <span className="chat-avatar" aria-hidden="true">🌾</span>}
                <div className="chat-text">
                  {m.textKey ? t(m.textKey) : m.text}
                  {m.provider === 'knowledge_base' && <span className="chat-source">KB</span>}
                </div>
              </div>
            ))}
            {busy && (
              <div className="chat-bubble ai">
                <span className="chat-avatar" aria-hidden="true">🌾</span>
                <div className="chat-text muted"><span className="spinner dark" /> {t('ai.thinking')}</div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {error && <div className="alert alert-error">⚠️ {error}</div>}

          {wxContext && !contextDismissed && (
            <p className="wx-context-chip" role="status">
              🌤️ {t('ai.weatherContext')}: {wxContext.location}
              {wxContext.temperature != null ? ` · ${Math.round(wxContext.temperature)}°C` : ''}
              {wxContext.condition ? ` · ${wxContext.condition}` : ''}
              <button
                type="button"
                className="context-clear"
                onClick={() => setContextDismissed(true)}
                aria-label={t('ai.clearContext')}
              >
                ×
              </button>
            </p>
          )}

          <form className="chat-input-row" onSubmit={send}>
            <input
              className="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t('ai.placeholder')}
              maxLength={1000}
              aria-label={t('ai.placeholder')}
              disabled={busy}
            />
            <button className="btn btn-primary" type="submit" disabled={busy || !input.trim()}>
              {t('ai.send')} ➤
            </button>
          </form>
          <p className="disclaimer">⚠️ {t('ai.disclaimer')}</p>
        </div>
      </div>
    </section>
  )
}
