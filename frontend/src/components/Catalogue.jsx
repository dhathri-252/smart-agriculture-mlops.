import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext.jsx'
import { apiFetch } from '../api.js'
import { filterCatalogue } from '../catalogueUtils.js'

const TILE_COLORS = {
  vegetables: 'linear-gradient(135deg,#e9f7e3,#cfe8c2)',
  fruits: 'linear-gradient(135deg,#fff3e0,#ffd9c7)',
  cereals_millets: 'linear-gradient(135deg,#fef6d8,#f0dfa8)',
  pulses_legumes: 'linear-gradient(135deg,#f3ead8,#e0cfa8)',
  oilseeds: 'linear-gradient(135deg,#fff8e1,#ffe9a8)',
  fibre_sugar_commercial: 'linear-gradient(135deg,#ede7f6,#d5cbe8)',
  spices_condiments: 'linear-gradient(135deg,#fdecea,#f8c9c0)',
  plantation_beverage: 'linear-gradient(135deg,#e8f0e4,#c4d6bd)',
  fodder_forage: 'linear-gradient(135deg,#e6f4ea,#bfe3c9)',
  medicinal_aromatic: 'linear-gradient(135deg,#eef7f0,#cdeadb)',
}

function CropImage({ item, size }) {
  const [failed, setFailed] = useState(false)
  const catId = (item.categories || [])[0] || ''
  if (!item.image || item.image_status !== 'verified' || failed) {
    return (
      <span
        className={size === 'detail' ? 'detail-tile' : 'crop-tile'}
        role="img"
        aria-label={item.alt_text || item.name_en}
        style={size === 'detail' ? undefined : { background: TILE_COLORS[catId] || 'var(--green-100)' }}
      >
        {item.emoji || '🌾'}
      </span>
    )
  }
  return (
    <img
      className={size === 'detail' ? 'detail-photo' : 'crop-photo'}
      src={item.image}
      alt={item.alt_text || `Photograph of ${item.name_en}`}
      loading="lazy"
      decoding="async"
      width={size === 'detail' ? 320 : 320}
      height={size === 'detail' ? 240 : 180}
      onError={() => setFailed(true)}
    />
  )
}

function CropCard({ item, onOpen }) {
  const { t, lang, cropName } = useTranslation()
  const name = cropName(item)
  return (
    <button
      type="button"
      className="crop-card"
      onClick={() => onOpen(item)}
      aria-label={`${item.name_en} — ${t('cat.viewGuide')}`}
    >
      <CropImage item={item} size="card" />
      <span className="crop-names">
        <strong className="crop-en">{item.name_en}</strong>
        {lang !== 'en' && (
          <span className="crop-local">
            {name.text}
            {name.missing && <em className="flag flag-missing"> · {t('cat.missingName')}</em>}
            {name.unverified && <em className="flag flag-unverified"> · {t('cat.unverifiedName')}</em>}
          </span>
        )}
      </span>
      <span className={`model-chip${item.model_supported ? ' on' : ''}`} title={item.model_supported ? t('cat.modelSupported') : t('cat.catalogueOnly')}>
        {item.model_supported ? '🤖 AI' : '📖'}
      </span>
    </button>
  )
}

export default function Catalogue({ onOpenCrop }) {
  const { t, lang } = useTranslation()
  const [items, setItems] = useState([])
  const [meta, setMeta] = useState(null)
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')
  const [modelOnly, setModelOnly] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError('')
      try {
        const [listRes, metaRes] = await Promise.all([
          apiFetch('/api/catalogue'),
          apiFetch('/api/catalogue/meta'),
        ])
        if (!cancelled) {
          setItems(listRes.items || [])
          setMeta(metaRes)
        }
      } catch (err) {
        if (!cancelled) setError(err.code === 'network' ? t('cat.offline') : (err.message || t('form.failed')))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const visible = useMemo(
    () => filterCatalogue(items, { category, search, modelOnly }),
    [items, category, search, modelOnly],
  )

  const categories = meta?.categories || []

  return (
    <section className="page-section">
      <div className="container">
        <div className="section-head">
          <h2>🌾 {t('cat.title')}</h2>
          <p>{t('cat.subtitle')}</p>
        </div>

        <div className="cat-controls">
          <input
            type="search"
            className="cat-search"
            placeholder={t('cat.search')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label={t('cat.search')}
          />
          <div className="cat-filters" role="group" aria-label={t('cat.allCategories')}>
            <button
              type="button"
              className={`chip${category === '' ? ' active' : ''}`}
              onClick={() => setCategory('')}
            >
              {t('cat.allCategories')} ({items.length})
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                type="button"
                className={`chip${category === c.id ? ' active' : ''}`}
                onClick={() => setCategory(category === c.id ? '' : c.id)}
                title={c.en}
              >
                {c.emoji} {c.en}
              </button>
            ))}
          </div>
          <label className="model-toggle">
            <input type="checkbox" checked={modelOnly} onChange={(e) => setModelOnly(e.target.checked)} />
            {t('cat.modelOnly')}
          </label>
        </div>

        {loading && <div className="empty-state"><span className="spinner dark" /> {t('cat.loading')}</div>}
        {error && <div className="alert alert-error" role="alert">⚠️ {error}</div>}

        {!loading && !error && (
          <>
            <p className="muted" role="status">
              {visible.length} {t('cat.count')}
              {lang !== 'en' && ` · ${lang}`}
            </p>
            {visible.length === 0 ? (
              <div className="empty-state">🔍 {t('cat.noResults')}</div>
            ) : (
              <div className="crop-grid">
                {visible.map((item) => (
                  <CropCard key={item.id} item={item} onOpen={onOpenCrop} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </section>
  )
}
