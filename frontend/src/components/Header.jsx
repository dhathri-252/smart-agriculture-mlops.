import { useTranslation, SUPPORTED_LANGS } from '../i18n/LanguageContext.jsx'

export default function Header({ view, onNavigate, user, onLogin, onLogout, onStartPrediction }) {
  const { t, lang, setLang } = useTranslation()

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
          onClick={() => onNavigate('home')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onNavigate('home')}
        >
          <span className="brand-icon">🌱</span>
          <span className="brand-text">Smart Agriculture</span>
        </div>

        <nav className="nav" aria-label="Main navigation">
          {links.map((l) => (
            <button
              key={l.key}
              className={`nav-link${view === l.key ? ' active' : ''}`}
              onClick={() => onNavigate(l.key)}
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
          <div className="user-chip" title={t('auth.profile')}>
            <span className="user-avatar" aria-hidden="true">👤</span>
            <span className="user-name">{user.username}</span>
            <button className="btn btn-ghost btn-sm" onClick={onLogout}>
              {t('nav.logout')}
            </button>
          </div>
        ) : (
          <button className="btn btn-ghost btn-sm" onClick={onLogin}>
            {t('nav.login')}
          </button>
        )}

        <button className="btn btn-primary header-cta" onClick={onStartPrediction}>
          {t('nav.predict')}
        </button>
      </div>
    </header>
  )
}
