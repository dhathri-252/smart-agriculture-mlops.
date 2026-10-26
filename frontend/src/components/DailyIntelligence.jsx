import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext.jsx'
import { apiFetch } from '../api.js'

const MONTH_NAMES = {
  en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
}

const SEASON_LABELS = {
  en: { kharif: 'Kharif (Monsoon)', rabi: 'Rabi (Winter)', zaid: 'Zaid (Summer)', 'kharif zaid overlap': 'KharifZaid Transition' },
}

function seasonLabel(season, lang) {
  return SEASON_LABELS[lang]?.[season] || SEASON_LABELS.en[season] || season
}

function formatDuration(days) {
  if (days == null) return '—'
  return days + ' days'
}

function formatTempRange(range) {
  if (!range) return '—'
  const [lo, hi] = range
  if (lo == null && hi == null) return '—'
  if (lo == null) return 'Up to ' + hi + '°C'
  if (hi == null) return 'From ' + lo + '°C'
  return lo + '–' + hi + '°C'
}

function scoreBadgeClass(score) {
  if (score >= 70) return 'score-high'
  if (score >= 40) return 'score-med'
  return 'score-low'
}

function DailyIntelligence() {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)
  const [catalogueById, setCatalogueById] = useState({})
  const lastFetchKey = useRef(null)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    let cancelled = false
    apiFetch('/api/catalogue')
      .then((res) => !cancelled && setCatalogueById(Object.fromEntries((res.items || []).map((i) => [i.id, i]))))
      .catch(() => !cancelled && setCatalogueById({}))
    return () => { cancelled = true }
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const qs = new URLSearchParams()
      if (location && location.trim()) qs.set('location', location.trim())
      if (soil && soil.trim()) qs.set('soil', soil.trim())
      if (water && water.trim()) qs.set('water', water.trim())
      if (month && month.trim()) qs.set('month', month.trim())
      if (limit && limit.trim()) qs.set('limit', limit.trim())
      if (forecast) qs.set('forecast', 'true')
      const key = qs.toString()
      lastFetchKey.current = key
      const res = await apiFetch('/api/daily-recommendations?' + key)
      if (lastFetchKey.current !== key) return
      setData(res)
    } catch (err) {
      if (lastFetchKey.current !== key) return
      setError(err.code === 'network' ? t('form.offline') : (err.message || t('form.failed')))
    } finally {
      setLoading(false)
    }
  }, [location, soil, water, month, limit, forecast, t])

  useEffect(() => { const timer = setTimeout(load, 50); return () => clearTimeout(timer) }, [load])

  async function handleRefresh() {
    setRefreshing(true)
    try { await load() } finally { setRefreshing(false) }
  }

  async function handleLookup(e) {
    e.preventDefault()
    if (!location.trim()) return
    setRefreshing(true)
    try { await load() } finally { setRefreshing(false) }
  }

  const recommendations = data?.recommendations || []
  const isStale = data && data.date && new Date(data.date).toDateString() !== new Date().toDateString()

  const getCropImage = (rec) => {
    const item = catalogueById[rec.id]
    if (!item || !item.image || item.image_status !== 'verified') return null
    return item.image
  }

  const getCropAlt = (rec) => {
    const item = catalogueById[rec.id]
    return item ? (item.alt_text || `Photograph of ${rec.name_en}`) : `Photograph of ${rec.name_en}`
  }

  return null
}

export default DailyIntelligence