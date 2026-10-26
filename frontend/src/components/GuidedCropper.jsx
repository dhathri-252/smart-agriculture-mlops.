import { useMemo, useEffect, useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext.jsx'
import { apiFetch } from '../api.js'

export default function GuidedCropper({ onNavigate }) {
  const { t, lang, cropName } = useTranslation()
  const [catalogue, setCatalogue] = useState([])
  const [catalogueLoading, setCatalogueLoading] = useState(true)
  const [catalogueError, setCatalogueError] = useState('')
  const [meta, setMeta] = useState(null)
  const [item, setItem] = useState(null)
  const [crop, setCrop] = useState('')
  const [location, setLocation] = useState('')
  const [soil, setSoil] = useState('unsure')
  const [water, setWater] = useState('unsure')
  const [land, setLand] = useState('')
  const [landUnit, setLandUnit] = useState('acres')
  const [result, setResult] = useState(null)
  const [resultLoading, setResultLoading] = useState(false)
  const [error, setError] = useState('')
  const [browse, setBrowse] = useState(false)
  const [browseCat, setBrowseCat] = useState('')
  const [browseSearch, setBrowseSearch] = useState('')

  useEffect(() => {
    let cancelled = false
    Promise.all([apiFetch('/api/catalogue'), apiFetch('/api/catalogue/meta')])
      .then(([listRes, metaRes]) => {
        if (!cancelled) {
          setCatalogue(listRes.items || [])
          setMeta(metaRes)
        }
      })
      .catch(() => { if (!cancelled) setCatalogueError(t('cat.offline')) })
      .finally(() => { if (!cancelled) setCatalogueLoading(false) })
    return () => { cancelled = true }
  }, [t])

  const categories = meta?.categories || []
  const catNames = meta?.category_names || (categories || []).reduce((acc, c) => {
    acc[c.id] = c.en
    return acc
  }, {})

  const browseItems = useMemo(() => {
    let list = catalogue.filter((c) => {
      if (browseCat && (!c.categories || !c.categories.includes(browseCat))) return false
      if (browseSearch) {
        const q = browseSearch.toLowerCase()
        const hay = [c.name_en, ...(c.names || {})].some((v) => String(v).toLowerCase().includes(q))
        if (!hay) return false
      }
      return true
    })
    return list.sort((a, b) => (a.name_en || '').localeCompare(b.name_en || ''))
  }, [catalogue, browseCat, browseSearch])

  function openCrop(cropId) {
    setBrowse(false)
    setBrowseSearch('')
    setBrowseCat('')
    setResultLoading(true)
    setError('')
    apiFetch(`/api/catalogue/${encodeURIComponent(cropId)}`)
      .then((res) => { setItem(res); setResult(res) })
      .catch((err) => setError(err.message || t('form.failed')))
      .finally(() => setResultLoading(false))
    setCrop(cropId)
  }

  function getCropMove() {
    if (!crop) return
    setResult(item)
    setError('')
  }

  function resetResult() {
    setResult(null)
    setItem(null)
    setError('')
  }

  return (
    <section className="page-section cropper-section" id="cropper">
      <div className="container">
        <div className="section-head">
          <h2>🌾 {t('cropper.title')}</h2>
          <p>{t('cropper.subtitle')}</p>
        </div>

        {/* Choose a crop */}
        <div className="form-card">
          <label className="crop-label" htmlFor="cropper-crop">
            {t('cropper.pickTitle')}
          </label>
          <select
            id="cropper-crop"
            className="cropper-select"
            value={crop}
            onChange={(e) => { setCrop(e.target.value); setResult(null); setItem(null) }}
            disabled={catalogueLoading}
            aria-invalid={Boolean(error) && !crop}
          >
            <option value="">{t('cropper.pickUnsure')}</option>
            {catalogue.map((c) => {
              const cd = cropName(c)
              return <option key={c.id} value={c.id}>{cd.text}</option>
            })}
          </select>
          {catalogueLoading && <span className="muted">{t('cat.loading')}</span>}
          {catalogueError && <span className="muted">{catalogueError}</span>}
        </div>

        {/* Optional farm details */}
        <div className="form-card farm-details">
          <p className="section-sub">{t('cropper.locTitle')}</p>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="cropper-loc">{t('cropper.locTitle')}</label>
              <input
                id="cropper-loc"
                type="text"
                className="input"
                placeholder={t('cropper.locHint')}
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                disabled={catalogueLoading}
              />
            </div>
            <div className="field">
              <label htmlFor="cropper-land">{t('cropper.landTitle')}</label>
              <input
                id="cropper-land"
                type="number"
                className="input"
                placeholder="0"
                value={land}
                onChange={(e) => setLand(e.target.value)}
                disabled={catalogueLoading}
              />
              <span className="unit">{t(landUnit)}</span>
            </div>
          </div>
          <div className="option-grid">
            <div className="field">
              <p className="opt-label">{t('cropper.soilTitle')}</p>
              <div className="option-group">
                {t('cropper.soilOptions').map((o) => (
                  <label key={o} className={`radio${soil === o ? ' selected' : ''}`}>
                    <input
                      type="radio"
                      name="soil"
                      value={o}
                      checked={soil === o}
                      onChange={() => setSoil(o)}
                      disabled={catalogueLoading}
                    />
                    <span>{o}</span>
                  </label>
                ))}
                <label className="radio">
                  <input
                    type="radio"
                    name="soil"
                    value="unsure"
                    checked={soil === 'unsure'}
                    onChange={() => setSoil('unsure')}
                    disabled={catalogueLoading}
                  />
                  <span>{t('cropper.soilUnsure')}</span>
                </label>
              </div>
            </div>
            <div className="field">
              <p className="opt-label">{t('cropper.waterTitle')}</p>
              <div className="option-group">
                {t('cropper.waterOptions').map((o) => (
                  <label key={o} className={`radio${water === o ? ' selected' : ''}`}>
                    <input
                      type="radio"
                      name="water"
                      value={o}
                      checked={water === o}
                      onChange={() => setWater(o)}
                      disabled={catalogueLoading}
                    />
                    <span>{o}</span>
                  </label>
                ))}
                <label className="radio">
                  <input
                    type="radio"
                    name="water"
                    value="unsure"
                    checked={water === 'unsure'}
                    onChange={() => setWater('unsure')}
                    disabled={catalogueLoading}
                  />
                  <span>{t('cropper.waterUnsure')}</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Browse by category (shown when "I'm not sure") */}
        {crop === '' && (
          <div className="form-card">
            <button
              type="button"
              className="btn btn-secondary btn-full"
              onClick={() => setBrowse(true)}
            >
              📚 {t('cropper.browseLabel')}
            </button>
            {browse && (
              <div className="browse-wrap">
                <div className="browse-filters">
                  <button
                    type="button"
                    className={`chip${browseCat === '' ? ' active' : ''}`}
                    onClick={() => setBrowseCat('')}
                  >
                    {t('cropper.browseAll')}
                  </button>
                  {categories.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      className={`chip${browseCat === c.id ? ' active' : ''}`}
                      onClick={() => setBrowseCat(c.id)}
                    >
                      {c.emoji} {c.en}
                    </button>
                  ))}
                </div>
                <input
                  type="search"
                  className="cat-search browse-search"
                  placeholder={t('cropper.browseSearch')}
                  value={browseSearch}
                  onChange={(e) => setBrowseSearch(e.target.value)}
                  aria-label={t('cropper.browseSearch')}
                />
                <div className="crop-grid browse-grid">
                  {browseItems.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      className="crop-card"
                      onClick={() => openCrop(c.id)}
                      aria-label={`${c.name_en} — ${t('cat.viewGuide')}`}
                    >
                      {c.emoji && <span className="crop-tile" aria-hidden="true">{c.emoji}</span>}
                      <span className="crop-names">
                        <strong className="crop-en">{c.name_en}</strong>
                        <span className="crop-local">{cropName(c).text}</span>
                      </span>
                      <span className={`model-chip${c.model_supported ? ' on' : ''}`}>
                        {c.model_supported ? '🤖 AI' : '📖'}
                      </span>
                    </button>
                  ))}
                  {browseItems.length === 0 && (
                    <div className="empty-state">{t('cropper.browseEmpty')}</div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Result card */}
        {result && (
          <div className="result-wrap" aria-live="polite">
            <div className="result-card">
              <PhotoTile item={result} emoji={result.emoji || '🌾'} />
              <div className="result-text">
                <p className="result-eyebrow">{t('cropper.resultTitle')}</p>
                <h3 className="result-crop">{result.name_en}</h3>
                <p className="result-note">{t('cropper.resultSub')}</p>
                <div className="result-meta">
                  <span className="muted">{catNames[(result.categories || [])[0]] || ''}</span>
                  {result.model_supported && (
                    <span className="chip model-chip on">🤖 {t('cropper.modelCta')}</span>
                  )}
                </div>
              </div>
            </div>

            {result.guide?.en && (
              <div className="info-card">
                <h4>🌱 {t('cat.guideTitle')}</h4>
                <p>{result.guide.en}</p>
                {result.guide.te && <p>{result.guide.te}</p>}
                <p className="disclaimer">ℹ️ {t('cat.guideUnverified')}</p>
              </div>
            )}

            <div className="info-card">
              <h4>🔍 {t('cropper.modelCta')}</h4>
              <p className="muted">
                {result.model_supported ? t('cropper.modelAgri') : t('cropper.modelNot')}
              </p>
              <p className="muted">{t('cropper.mlNeeds')}</p>
              <ul className="tips-list">
                <li className="tip-item">
                  <span className="tip-icon">🧪</span>
                  <p>{t('cropper.mlSoil')}</p>
                </li>
                <li className="tip-item">
                  <span className="tip-icon">🌡️</span>
                  <p>{t('cropper.mlWeather')}</p>
                </li>
              </ul>
              <p className="disclaimer">ℹ️ {t('cropper.noGuess')}</p>
              <button
                type="button"
                className="btn btn-primary btn-full"
                onClick={() => onNavigate && onNavigate('advanced')}
              >
                🚀 {t('cropper.mlCta')}
              </button>
            </div>
          </div>
        )}

        {!result && error && <div className="alert alert-error" role="alert">⚠️ {error}</div>}

        <p className="muted centre-text">{t('cropper.imSureHint')}</p>
      </div>
    </section>
  )
}

function PhotoTile({ item, emoji = '🌾' }) {
  if (!item || !item.image || item.image_status !== 'verified') {
    return (
      <span
        className="result-photo"
        role="img"
        aria-label={item?.alt_text || ''}
      >
        {emoji}
      </span>
    )
  }
  return (
    <img
      className="result-photo"
      src={item.image}
      alt={item.alt_text || 'Photograph of crop'}
      loading="lazy"
      decoding="async"
    />
  )
}