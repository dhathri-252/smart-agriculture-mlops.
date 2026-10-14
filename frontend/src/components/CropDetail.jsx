import { useEffect, useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext.jsx'
import { apiFetch } from '../api.js'

/** Crop detail: guide WITHOUT the 7 RF inputs; live weather reuses /api/weather. */
export function CropDetailPhoto({ item }) {
  const [failed, setFailed] = useState(false)
  if (!item.image || item.image_status !== 'verified' || failed) {
    return (
      <span className="detail-tile" role="img" aria-label={item.alt_text || item.name_en}>
        {item.emoji || '🌾'}
      </span>
    )
  }
  return (
    <img
      className="detail-photo"
      src={item.image}
      alt={item.alt_text || `Photograph of ${item.name_en}`}
      loading="lazy"
      decoding="async"
      width={320}
      height={240}
      onError={() => setFailed(true)}
    />
  )
}

export default function CropDetail({ cropId, initial, onBack }) {
  const { t, lang, pick, cropName } = useTranslation()
  const [item, setItem] = useState(initial || null)
  const [loading, setLoading] = useState(!initial)
  const [error, setError] = useState('')
  const [wxLocation, setWxLocation] = useState('')
  const [weather, setWeather] = useState(null)
  const [wxBusy, setWxBusy] = useState(false)
  const [wxError, setWxError] = useState('')

  useEffect(() => {
    if (initial && initial.id === cropId) {
      setItem(initial)
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError('')
    apiFetch(`/api/catalogue/${encodeURIComponent(cropId)}`)
      .then((res) => { if (!cancelled) setItem(res) })
      .catch((err) => { if (!cancelled) setError(err.message || t('form.failed')) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [cropId])

  async function lookupWeather(e) {
    e?.preventDefault()
    const loc = wxLocation.trim()
    if (!loc || wxBusy) return
    setWxBusy(true)
    setWxError('')
    setWeather(null)
    try {
      const res = await apiFetch(`/api/weather?location=${encodeURIComponent(loc)}`)
      setWeather(res)
    } catch (err) {
      setWxError(err.code === 'network' ? t('cat.offline') : (err.message || t('wx.unavailable')))
    } finally {
      setWxBusy(false)
    }
  }

  if (loading) {
    return (
      <section className="page-section"><div className="container">
        <div className="empty-state"><span className="spinner dark" /> {t('cat.loading')}</div>
      </div></section>
    )
  }

  if (error || !item) {
    return (
      <section className="page-section"><div className="container">
        <button className="btn btn-ghost btn-sm" onClick={onBack}>{t('cat.back')}</button>
        <div className="alert alert-error" role="alert">⚠️ {error || t('cat.noResults')}</div>
      </div></section>
    )
  }

  const name = cropName(item)
  const guideTe = (item.guide && item.guide.te) || ''
  const guideText = lang === 'te' && guideTe ? guideTe : (item.guide?.en || '')
  const catNames = Object.values(item.category_names || {}).join(' · ')

  return (
    <section className="page-section">
      <div className="container detail-wrap">
        <button className="btn btn-ghost btn-sm" onClick={onBack}>{t('cat.back')}</button>
        <div className="detail-head">
          <CropDetailPhoto item={item} />
          <div>
            <h2>{item.name_en}</h2>
            {lang !== 'en' && (
              <p className="detail-local">
                {name.text}
                {name.missing && <em className="flag flag-missing"> · {t('cat.missingName')}</em>}
                {name.unverified && <em className="flag flag-unverified"> · {t('cat.unverifiedName')}</em>}
              </p>
            )}
            <p className="muted">{catNames}</p>
            <p className="muted">{item.model_supported ? `🤖 ${t('cat.modelSupported')}` : `📖 ${t('cat.catalogueOnly')}`}</p>
          </div>
        </div>
        <div className="info-card">
          <h4>🖼️ {item.image_status === 'verified' ? (item.image_attribution?.attribution || t('cat.photoCredit')) : t('cat.noPhoto')}</h4>
          {item.image_status === 'verified' && item.image_attribution?.source_url && (
            <p className="muted">
              <a href={item.image_attribution.source_url} target="_blank" rel="noreferrer">
                {item.image_attribution.source || 'Wikimedia Commons'}
              </a>
              {' · '}{item.image_attribution.license || ''}
            </p>
          )}
          {item.image_status !== 'verified' && (
            <p className="muted">⏳ {t('cat.photoPending')}</p>
          )}
          <div className="tips-list">
            {(Object.entries(item.names || {})).map(([lc, nm]) => (
              <div className="tip-item" key={lc}>
                <span className="tip-icon">{lc.toUpperCase()}</span>
                <p>{nm}{(lc !== 'en' && (item.name_status || {})[lc] === 'unverified') ? ` (${t('cat.unverifiedName')})` : ''}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="info-card">
          <h4>🌱 {t('cat.guideTitle')}</h4>
          <p>{guideText}</p>
          <p className="disclaimer">ℹ️ {t('cat.guideUnverified')}</p>
        </div>
        <div className="info-card">
          <h4>⛅ {t('cat.weatherTitle')}</h4>
          <form className="wx-lookup" onSubmit={lookupWeather}>
            <input type="text" placeholder={t('wx.placeholder')} value={wxLocation} onChange={(e) => setWxLocation(e.target.value)} aria-label={t('wx.location')} />
            <button className="btn btn-primary btn-sm" type="submit" disabled={wxBusy || !wxLocation.trim()}>
              {wxBusy ? t('wx.loading') : t('wx.get')}
            </button>
          </form>
          {wxError && <div className="alert alert-error" role="alert">⚠️ {wxError}</div>}
          {weather && weather.configured === false && (
            <p className="muted">🔑 {t('wx.notConfigured')}</p>
          )}
          {weather && weather.configured === true && weather.found === true && (
            <div className="wx-grid">
              <div className="wx-card"><span className="wx-icon">🌡️</span><span className="wx-value">{weather.temperature != null ? `${Math.round(weather.temperature)}°C` : '—'}</span><span className="wx-label">{t('wx.temperature')}</span></div>
              <div className="wx-card"><span className="wx-icon">💧</span><span className="wx-value">{weather.humidity != null ? `${weather.humidity}%` : '—'}</span><span className="wx-label">{t('wx.humidity')}</span></div>
              <div className="wx-card"><span className="wx-icon">⛅</span><span className="wx-value">{weather.condition || '—'}</span><span className="wx-label">{t('wx.condition')}</span></div>
            </div>
          )}
          {weather && weather.configured === true && weather.found === false && (
            <p className="muted">⚠️ {pick(weather.message) || t('wx.notFound')}</p>
          )}
          <p className="muted center">🌿 {t('wx.adviceNote')}</p>
        </div>
      </div>
    </section>
  )
}
