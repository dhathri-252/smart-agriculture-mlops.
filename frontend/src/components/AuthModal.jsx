import { useEffect, useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext.jsx'
import { apiFetch } from '../api.js'

const USERNAME_PATTERN = /^[A-Za-z0-9_.-]{3,32}$/

export default function AuthModal({ onClose, onAuthed }) {
  const { t } = useTranslation()
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [farmName, setFarmName] = useState('')
  const [location, setLocation] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  async function submit(e) {
    e.preventDefault()
    setError('')

    // Client-side validation (server validates again).
    if (!USERNAME_PATTERN.test(username)) { setError(t('auth.usernameInvalid')); return }
    if (password.length < 8) { setError(t('auth.passwordMin')); return }

    setBusy(true)
    try {
      const path = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
      const body = mode === 'login'
        ? { username, password }
        : { username, password, farm_name: farmName, location }
      const res = await apiFetch(path, { method: 'POST', body })
      onAuthed(res.user, res.token)
    } catch (err) {
      if (err.code === 'network') setError(t('form.offline'))
      else if (err.status === 401) setError(t('auth.invalidCredentials'))
      else if (err.status === 409) setError(t('auth.usernameTaken'))
      else setError(err.message || t('form.failed'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-card">
        <button className="modal-close" onClick={onClose} aria-label={t('common.close')}>✕</button>
        <div className="modal-icon">🧑‍🌾</div>
        <h3>{mode === 'login' ? t('auth.loginTitle') : t('auth.registerTitle')}</h3>
        <p className="muted">{mode === 'login' ? t('auth.loginSubtitle') : t('auth.registerSubtitle')}</p>

        <form onSubmit={submit} noValidate>
          <div className="field">
            <label htmlFor="auth-username">{t('auth.username')}</label>
            <input
              id="auth-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              maxLength={32}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="auth-password">{t('auth.password')}</label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              maxLength={128}
              required
            />
          </div>
          {mode === 'register' && (
            <>
              <div className="field">
                <label htmlFor="auth-farm">{t('auth.farmName')}</label>
                <input id="auth-farm" type="text" value={farmName} onChange={(e) => setFarmName(e.target.value)} maxLength={60} />
              </div>
              <div className="field">
                <label htmlFor="auth-loc">{t('auth.location')}</label>
                <input id="auth-loc" type="text" value={location} onChange={(e) => setLocation(e.target.value)} maxLength={60} />
              </div>
            </>
          )}

          {error && <div className="alert alert-error">⚠️ {error}</div>}

          <button className="btn btn-primary btn-full" type="submit" disabled={busy}>
            {busy
              ? (mode === 'login' ? t('auth.loggingIn') : t('auth.registering'))
              : (mode === 'login' ? t('auth.login') : t('auth.register'))}
          </button>
        </form>

        <button
          className="btn btn-ghost btn-full modal-switch"
          type="button"
          onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
        >
          {mode === 'login' ? t('auth.noAccount') : t('auth.haveAccount')}{' '}
          <strong>{mode === 'login' ? t('auth.register') : t('auth.login')}</strong>
        </button>
      </div>
    </div>
  )
}
