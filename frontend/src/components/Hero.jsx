import { useTranslation } from '../i18n/LanguageContext.jsx'

export default function Hero({ onStart }) {
  const { t } = useTranslation()
  return (
    <section id="home" className="hero">
      <div className="container hero-grid">
        <div className="hero-copy">
          <span className="badge">🌾 {t('hero.badge')}</span>
          <h1>
            {t('hero.title')}
            <span className="hero-accent">{t('hero.accent')}</span>
          </h1>
          <p className="hero-desc">{t('hero.desc')}</p>
          <div className="hero-actions">
            <button className="btn btn-primary btn-lg" onClick={onStart}>
              {t('hero.start')}
            </button>
            <button
              className="btn btn-ghost btn-lg"
              onClick={() => document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' })}
            >
              {t('hero.learn')}
            </button>
          </div>
          <ul className="hero-points">
            <li>✅ {t('hero.point1')}</li>
            <li>✅ {t('hero.point2')}</li>
            <li>✅ {t('hero.point3')}</li>
          </ul>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="field-card">
            <div className="field-sky">☀️</div>
            <div className="field-rows">
              <span>🌱</span><span>🌱</span><span>🌱</span><span>🌱</span>
              <span>🌿</span><span>🌿</span><span>🌿</span><span>🌿</span>
              <span>🌾</span><span>🌾</span><span>🌾</span><span>🌾</span>
            </div>
            <div className="field-footer">
              <div>
                <strong>{t('hero.live')}</strong>
                <small>{t('hero.liveSub')}</small>
              </div>
              <span className="pulse">● {t('hero.liveDot')}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
