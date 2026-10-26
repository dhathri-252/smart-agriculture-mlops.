import { useState, useEffect } from 'react'
import { useTranslation, SUPPORTED_LANGS } from '../i18n/LanguageContext.jsx'

export default function Header({ view, onNavigate, user, onLogin, onLogout, onStartPrediction }) {
  const { t, lang, setLang } = useTranslation()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  useEffect(() => {
    if (!mobileNavOpen) return
    function onKey(e) {
      if (e.key === 'Escape') setMobileNavOpen(false)
    }
    function onDocClick(e) {
      if (!e.target.closest('.header')) setMobileNavOpen(false)
    }
    window.addEventListener('keydown', onKey)
    document.addEventListener('click', onDocClick)
    return () => {
      window.removeEventListener('keydown', onKey)
      document.removeEventListener('click', onDocClick)
    }
  }, [mobileNavOpen])

  const links = [
    { key: 'home', label: t('nav.home') },
    { key: 'catalogue', label: t('nav.catalogue') },
    { key: 'dashboard', label: t('nav.dashboard') },
    { key: 'assistant', label: t('nav.assistant') },
    { key: 'weather', label: t('nav.weather') },
  ]

  const langShort = { en: 'EN', te: 'తె', hi: 'हिं', ta: 'த', kn: 'ಕ', ml: 'മ', mr: 'म', bn: 'বাং' }

  return (
    <header className="header">
      <div className="container header-inner">
        <div
          className="brand"
          onClick={() => {
            onNavigate('home')
            setMobileNavOpen(false)
          }}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              onNavigate('home')
              setMobileNavOpen(false)
            }
          }}
        >
          <span className="brand-icon">🌱</span>
          <span className="brand-text">Smart Agriculture</span>
        </div>

        <nav className="nav" aria-label="Main navigation">
          {links.map((l) => (
            <button
              key={l.key}
              className={`nav-link${view === l.key ? ' active' : ''}`}
              onClick={() => {
                onNavigate(l.key)
                setMobileNavOpen(false)
              }}
              aria-current={view === l.key ? 'page' : undefined}
            >
              {l.label}
            </button>
          ))}
        </nav>

        <div className="lang-switch" role="group" aria-label={t('common.language')}>
          {SUPPORTED_LANGS.map((l) => (
            <button
              key={l}
              className={`lang-btn${lang === l ? ' active' : ''}`}
              onClick={() => setLang(l)}
              aria-pressed={lang === l}
              title={t(`lang.${l}`)}
            >
              {langShort[l] || l}
            </button>
          ))}
        </div>

        {user ? (
          <div className="user-chip header-auth" title={t('auth.profile')}>
            <span className="user-avatar" aria-hidden="true">👤</span>
            <span className="user-name">{user.username}</span>
            <button className="btn btn-ghost btn-sm" onClick={onLogout}>
              {t('nav.logout')}
            </button>
          </div>
        ) : (
          <button className="btn btn-ghost btn-sm header-auth" onClick={onLogin}>
            {t('nav.login')}
          </button>
        )}

        <button className="btn btn-primary header-cta" onClick={onStartPrediction}>
          {t('nav.predict')}
        </button>

        <button
          className="mobile-menu-toggle"
          aria-label={mobileNavOpen ? t('common.close') : t('nav.menu')}
          aria-expanded={mobileNavOpen}
          onClick={() => setMobileNavOpen((o) => !o)}
        >
          <span className="bar" />
          <span className="bar" />
          <span className="bar" />
        </button>

        {mobileNavOpen && (
          <div className="mobile-menu open" role="dialog" aria-label="Mobile navigation">
            <button
              className="mobile-close"
              onClick={() => setMobileNavOpen(false)}
              aria-label={t('common.close')}
            >
              ✕
            </button>

            <div className="menu-section">
              <div className="menu-title">{t('nav.menu')}</div>
              <div className="mobile-nav">
                {links.map((l) => (
                  <button
                    key={l.key}
                    className={`nav-link${view === l.key ? ' active' : ''}`}
                    onClick={() => {
                      onNavigate(l.key)
                      setMobileNavOpen(false)
                    }}
                    aria-current={view === l.key ? 'page' : undefined}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="menu-section">
              <div className="menu-title">{t('common.language')}</div>
              <div className="mobile-lang">
                {SUPPORTED_LANGS.map((l) => (
                  <button
                    key={l}
                    className={`lang-btn${lang === l ? ' active' : ''}`}
                    onClick={() => {
                      setLang(l)
                      setMobileNavOpen(false)
                    }}
                    aria-pressed={lang === l}
                    title={t(`lang.${l}`)}
                  >
                    {t(`lang.${l}`)} ({langShort[l] || l})
                  </button>
                ))}
              </div>
            </div>

            <div className="menu-section">
              <div className="mobile-auth">
                {user ? (
                  <button
                    className="btn btn-ghost"
                    onClick={() => {
                      onLogout()
                      setMobileNavOpen(false)
                    }}
                  >
                    {t('nav.logout')} ({user.username})
                  </button>
                ) : (
                  <button
                    className="btn btn-ghost"
                    onClick={() => {
                      onLogin()
                      setMobileNavOpen(false)
                    }}
                  >
                    {t('nav.login')}
                  </button>
                )}
                <button
                  className="btn mobile-predict"
                  onClick={() => {
                    onStartPrediction()
                    setMobileNavOpen(false)
                  }}
                >
                  {t('nav.predict')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
