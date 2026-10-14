import { useEffect, useRef, useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext.jsx'
import { apiFetch } from '../api.js'

export default function Weather() {
  const { t, pick } = useTranslation()
  const [location, setLocation] = useState('')
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(false)
  const [locating, setLocating] = useState(false)
  const [error, setError] = useState('')
  const [via, setVia] = useState('') // 'gps' | 'search' — how the current result was obtained
  // Last successful query params; used only by the explicit Refresh button.
  const lastQuery = useRef(null)

  // Global autocomplete state (backed by GET /api/locations/search).
  const [places, setPlaces] = useState([])
  const [placesLoading, setPlacesLoading] = useState(false)
  const [placesError, setPlacesError] = useState('')
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const suggestSeq = useRef(0)
  const listboxId = 'weather-place-listbox'

  // "lat, lon" typed directly — offered as a selectable option, no provider call.
  function parseCoords(text) {
    const m = text.match(/^\s*(-?\d{1,3}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*$/)
    if (!m) return null
    const lat = parseFloat(m[1]); const lon = parseFloat(m[2])
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null
    return { synthetic: true, lat, lon, label: text.trim() }
  }

  // Debounced autocomplete as the user types (min 2 chars). Stale responses
  // are discarded via a sequence counter.
  useEffect(() => {
    const text = location.trim()
    if (text.length < 2) {
      setPlaces([]); setPlacesError(''); setOpen(false); setActiveIndex(-1)
      return undefined
    }
    const coords = parseCoords(text)
    if (coords) {
      suggestSeq.current += 1
      setPlaces([coords]); setPlacesError(''); setPlacesLoading(false)
      setOpen(true); setActiveIndex(0)
      return undefined
    }
    const seq = ++suggestSeq.current
    setPlacesLoading(true)
    const timer = setTimeout(async () => {
      try {
        const res = await apiFetch(`/api/locations/search?q=${encodeURIComponent(text)}&limit=5`)
        if (seq !== suggestSeq.current) return // stale
        if (res.configured === false) {
          setPlaces([]); setPlacesError(''); setOpen(false)
        } else if (res.message && (!res.results || res.results.length === 0)) {
          setPlaces([]); setPlacesError(pick(res.message)); setOpen(true)
        } else {
          setPlaces(res.results || []); setPlacesError('')
          setOpen(true)
        }
        setActiveIndex(0)
      } catch (err) {
        if (seq !== suggestSeq.current) return // stale
        setPlaces([])
        setPlacesError(err.code === 'network' ? t('form.offline') : (err.message || t('wx.unavailable')))
        setOpen(true)
      } finally {
        if (seq === suggestSeq.current) setPlacesLoading(false)
      }
    }, 350)
    return () => clearTimeout(timer)
  }, [location])

  async function fetchWeather(params) {
    setError('')
    setBusy(true)
    setData(null)
    try {
      const qs = new URLSearchParams(params).toString()
      const res = await apiFetch(`/api/weather?${qs}`)
      setData(res)
      // Optional assistant context: store only the display summary (place name
      // + metrics — never coordinates, never API keys), per-tab and until the
      // tab closes. Updated only after an explicit successful lookup.
      if (res && res.found === true) {
        try {
          sessionStorage.setItem('sa_wx_context', JSON.stringify({
            location: res.location,
            temperature: res.temperature,
            humidity: res.humidity,
            condition: res.condition,
            rainfall_mm: res.precipitation_mm,
          }))
        } catch { /* storage unavailable — assistant simply has no context */ }
      }
    } catch (err) {
      setError(err.code === 'network' ? t('form.offline') : (err.message || t('wx.unavailable')))
    } finally {
      setBusy(false)
    }
  }

  function closeSuggestions() {
    setOpen(false); setActiveIndex(-1)
  }

  // Explicit user selection of a geocoded place (or typed coordinates).
  async function selectPlace(place) {
    if (busy || locating) return
    setLocation(place.label)
    closeSuggestions()
    setPlaces([])
    const params = place.synthetic
      ? { lat: place.lat.toFixed(4), lon: place.lon.toFixed(4) }
      : { lat: Number(place.lat).toFixed(4), lon: Number(place.lon).toFixed(4) }
    lastQuery.current = params
    setVia('search')
    await fetchWeather(params)
  }

  function onInputKeyDown(e) {
    if (!open || (places.length === 0 && !placesError)) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => (places.length ? (i + 1) % places.length : -1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => (places.length ? (i - 1 + places.length) % places.length : -1))
    } else if (e.key === 'Enter' && activeIndex >= 0 && activeIndex < places.length) {
      e.preventDefault()
      selectPlace(places[activeIndex])
    } else if (e.key === 'Escape') {
      closeSuggestions()
    }
  }

  async function search(e) {
    e?.preventDefault()
    const q = location.trim()
    if (!q || busy || locating) return
    closeSuggestions()
    setPlaces([])
    lastQuery.current = { location: q }
    setVia('search')
    await fetchWeather({ location: q })
  }

  // Called only from the explicit button press — no tracking before or after.
  async function refresh() {
    if (!lastQuery.current || busy || locating) return
    await fetchWeather(lastQuery.current)
  }

  function useMyLocation() {
    if (busy || locating) return
    if (!navigator.geolocation) {
      setError(t('wx.gpsUnsupported'))
      return
    }
    if (typeof window !== 'undefined' && window.isSecureContext === false) {
      // Browsers block geolocation on insecure origins (http + non-localhost).
      setError(t('wx.gpsInsecure'))
      return
    }
    setError('')
    setLocating(true)
    setData(null)
    // Single fix only — no watchPosition, no background tracking. Coordinates
    // are sent once to our backend for this lookup and never stored or logged.
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const params = {
          lat: pos.coords.latitude.toFixed(4),
          lon: pos.coords.longitude.toFixed(4),
        }
        lastQuery.current = params
        setVia('gps')
        setLocating(false)
        await fetchWeather(params)
      },
      (err) => {
        setLocating(false)
        // 1 = permission denied, 2 = position unavailable, 3 = timeout
        if (err.code === 1) setError(t('wx.gpsDenied'))
        else if (err.code === 2) setError(t('wx.gpsUnavailable'))
        else if (err.code === 3) setError(t('wx.gpsTimeout'))
        else setError(t('wx.gpsUnavailable'))
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 },
    )
  }

  return (
    <section className="page-section">
      <div className="container container-narrow">
        <div className="section-head">
          <h2>🌤️ {t('wx.title')}</h2>
          <p>{t('wx.subtitle')}</p>
        </div>

        <form className="form-card weather-form" onSubmit={search}>
          <div className="field">
            <label htmlFor="weather-location">{t('wx.location')}</label>
            <div className="input-row suggest-wrap">
              <input
                id="weather-location"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                onKeyDown={onInputKeyDown}
                onFocus={() => { if (places.length > 0 || placesError) setOpen(true) }}
                placeholder={t('wx.placeholder')}
                maxLength={100}
                disabled={busy || locating}
                role="combobox"
                aria-autocomplete="list"
                aria-expanded={open && (places.length > 0 || !!placesError)}
                aria-controls={listboxId}
                aria-label={t('wx.location')}
                aria-activedescendant={
                  open && activeIndex >= 0 ? `wx-place-option-${activeIndex}` : undefined
                }
                autoComplete="off"
              />
              <button className="btn btn-primary" type="submit" disabled={busy || locating || !location.trim()}>
                {busy ? t('wx.loading') : t('wx.get')}
              </button>
              {open && (places.length > 0 || placesLoading || placesError) && (
                <div className="suggest-panel">
                  {placesLoading && (
                    <div className="suggest-info" role="status">🔎 {t('wx.searchingPlaces')}</div>
                  )}
                  {!placesLoading && placesError && (
                    <div className="suggest-info suggest-error" role="status">⚠️ {placesError}</div>
                  )}
                  {!placesLoading && !placesError && places.length === 0 && (
                    <div className="suggest-info" role="status">🗺️ {t('wx.noResults')}</div>
                  )}
                  {!placesLoading && places.length > 0 && (
                    <ul
                      id={listboxId}
                      role="listbox"
                      aria-label={t('wx.placeSuggestions')}
                      onMouseDown={(e) => e.preventDefault()}
                    >
                      {places.map((p, idx) => (
                        <li
                          key={`${p.lat},${p.lon}`}
                          id={`wx-place-option-${idx}`}
                          role="option"
                          aria-selected={idx === activeIndex}
                          className={`suggest-item${idx === activeIndex ? ' active' : ''}`}
                          onMouseEnter={() => setActiveIndex(idx)}
                          onClick={() => selectPlace(p)}
                        >
                          <span className="suggest-main">
                            {p.synthetic ? `📍 ${t('wx.coordsOption')}` : `📍 ${p.label}`}
                          </span>
                          {!p.synthetic && p.name && p.label !== p.name && (
                            <span className="suggest-sub">{p.name}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
            <p className="muted gps-privacy">{t('wx.searchHint')}</p>
            <div className="gps-row">
              <button
                className="btn btn-secondary"
                type="button"
                onClick={useMyLocation}
                disabled={busy || locating}
                aria-busy={locating}
              >
                {locating ? `📍 ${t('wx.gpsLocating')}` : `📍 ${t('wx.gps')}`}
              </button>
              {data && data.found === true && (
                <button
                  className="btn btn-ghost"
                  type="button"
                  onClick={refresh}
                  disabled={busy || locating}
                >
                  {busy ? `🔄 ${t('wx.refreshing')}` : `🔄 ${t('wx.refresh')}`}
                </button>
              )}
            </div>
            <p className="muted gps-privacy">🔒 {t('wx.privacy')}</p>
          </div>
        </form>

        <div className="gps-status" role="status" aria-live="polite">
          {locating && <div className="alert alert-warn">📍 {t('wx.gpsLocating')}</div>}
        </div>

        {error && <div className="alert alert-error" role="alert">⚠️ {error}</div>}

        {data && data.configured === false && (
          <div className="info-card config-state">
            <span className="empty-icon">🔑</span>
            <h4>{t('wx.notConfigured')}</h4>
            <p className="muted">{t('wx.notConfiguredHelp')}</p>
          </div>
        )}

        {data && data.configured === true && data.found === false && (
          <div className="alert alert-warn">⚠️ {pick(data.message)}</div>
        )}

        {data && data.found === true && (
          <>
            <div className="wx-grid">
              <div className="wx-card">
                <span className="wx-icon">🌡️</span>
                <span className="wx-value">{data.temperature != null ? `${Math.round(data.temperature)}°C` : '—'}</span>
                <span className="wx-label">{t('wx.temperature')}</span>
              </div>
              <div className="wx-card">
                <span className="wx-icon">💧</span>
                <span className="wx-value">{data.humidity != null ? `${data.humidity}%` : '—'}</span>
                <span className="wx-label">{t('wx.humidity')}</span>
              </div>
              <div className="wx-card">
                <span className="wx-icon">⛅</span>
                <span className="wx-value">{data.condition || '—'}</span>
                <span className="wx-label">{t('wx.condition')}</span>
              </div>
              <div className="wx-card">
                <span className="wx-icon">🌧️</span>
                <span className="wx-value">
                  {data.precipitation_mm != null ? `${data.precipitation_mm} ${t('wx.mm')}` : '—'}
                </span>
                <span className="wx-label">{t('wx.rainfall')}</span>
              </div>
              <div className="wx-card">
                <span className="wx-icon">🌬️</span>
                <span className="wx-value">
                  {data.wind_speed != null ? `${data.wind_speed} ${t('wx.kmh')}` : '—'}
                </span>
                <span className="wx-label">{t('wx.wind')}</span>
              </div>
            </div>
            <p className="muted center">
              📍 {data.location}
              {via && (
                <span className="wx-tag">
                  {via === 'gps' ? t('wx.gpsTag') : t('wx.searchTag')}
                </span>
              )}
              {data.description ? ` · ${data.description}` : ''}
              {data.observed_at ? (
                <> · 🕐 {t('wx.observed')} {new Date(data.observed_at * 1000).toLocaleString()}</>
              ) : ''}
            </p>

            {Array.isArray(data.suggestions) && data.suggestions.length > 0 && (
              <div className="info-card">
                <h4>💡 {t('wx.suggestions')}</h4>
                <div className="tips-list">
                  {data.suggestions.map((s, idx) => (
                    <div className="tip-item" key={idx}>
                      <span className="tip-icon">{s.icon}</span>
                      <p>{pick(s)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <p className="muted center">🌿 {t('wx.adviceNote')}</p>
          </>
        )}
      </div>
    </section>
  )
}
