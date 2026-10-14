import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext.jsx'
import { apiFetch } from '../api.js'

const TIPS = [
  {
    icon: '💧',
    en: 'Water early morning or late evening to reduce evaporation — consider drip irrigation for higher efficiency.',
    te: 'ఆవిరి తగ్గడానికి ఉదయం లేదా సాయంత్రం నీరు పెట్టండి — సామర్థ్యం కోసం చిరుత పారుదల పరిగణించండి.',
  },
  {
    icon: '🧪',
    en: 'Test your soil before buying fertiliser — it saves money and protects long-term soil health.',
    te: 'ఎరువులు కొనే ముందు నేల పరీక్ష చేయించండి — డబ్బు ఆదా అవుతుంది, నేల ఆరోగ్యం కాపాడబడుతుంది.',
  },
  {
    icon: '🌦️',
    en: 'Check the weather before spraying or fertilising — rain may wash away recent applications.',
    te: 'పిచికారీ లేదా ఎరువులు వేసే ముందు వాతావరణం చూడండి — వర్షం వల్ల పట్టినది పోవచ్చు.',
  },
  {
    icon: '🚜',
    en: 'Keep records of what you sow and harvest — patterns over seasons help improve decisions.',
    te: 'ఏమి విత్తారో, ఏమి కోస్తారో నమోదు చేయండి — కాలాల పరంగా పోల్చుకుంటే నిర్ణయాలు మెరుగవుతాయి.',
  },
  {
    icon: '🐛',
    en: 'Inspect your field a few minutes every day — catching pest problems early usually means simpler solutions.',
    te: 'ప్రతిరోజూ కొన్ని నిమిషాలు పొలం పరిశీలించండి — తెగుళ్లు మొదట్లోనే పట్టుకుంటే పరిష్కారం సులభం.',
  },
]

function formatInputs(inputs) {
  if (!inputs) return ''
  return `N:${inputs.N} P:${inputs.P} K:${inputs.K} · ${inputs.temperature}°C · ${inputs.humidity}% · pH ${inputs.ph} · ${inputs.rainfall}mm`
}

function formatWhen(iso) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export default function Dashboard({ version, onNavigate }) {
  const { t, pick } = useTranslation()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [clearing, setClearing] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await apiFetch('/api/history?limit=200')
      setData(res)
    } catch (err) {
      setError(err.code === 'network' ? t('form.offline') : (err.message || t('form.failed')))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => { load() }, [version, load])

  const frequency = useMemo(() => {
    const counts = {}
    for (const item of data?.items || []) counts[item.crop] = (counts[item.crop] || 0) + 1
    return Object.entries(counts)
      .map(([crop, count]) => ({ crop, count }))
      .sort((a, b) => b.count - a.count)
  }, [data])

  const recent = data?.items?.[0] || null
  const topCrop = frequency[0] || null
  const maxCount = topCrop?.count || 1

  async function handleClear() {
    if (!window.confirm(t('dash.confirmClear'))) return
    setClearing(true)
    try {
      await apiFetch('/api/history', { method: 'DELETE' })
      await load()
    } catch (err) {
      setError(err.message || t('form.failed'))
    } finally {
      setClearing(false)
    }
  }

  if (loading && !data) {
    return (
      <section className="page-section">
        <div className="container">
          <div className="section-head"><h2>📊 {t('dash.title')}</h2></div>
          <div className="empty-state"><span className="spinner dark" /> {t('dash.loading')}</div>
        </div>
      </section>
    )
  }
  return (
    <section className="page-section">
      <div className="container">
        <div className="section-head">
          <h2>📊 {t('dash.title')}</h2>
          <p>{t('dash.subtitle')}</p>
          <button className="btn btn-ghost btn-sm" onClick={load} type="button">🔄 {t('dash.reload')}</button>
        </div>

        {error && <div className="alert alert-error">⚠️ {error}</div>}

        {!data || data.total === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">🌾</span>
            <p>{t('dash.noData')}</p>
            {onNavigate && (
              <button className="btn btn-primary" onClick={() => onNavigate('home')} type="button">
                {t('nav.predict')}
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="dash-stats">
              <div className="stat-card">
                <span className="stat-icon">🔢</span>
                <span className="stat-value">{data.total}</span>
                <span className="stat-label">{t('dash.total')}</span>
              </div>
              <div className="stat-card">
                <span className="stat-icon">🕑</span>
                <span className="stat-value stat-value-sm">{recent ? recent.crop : t('dash.noRecent')}</span>
                <span className="stat-label">{t('dash.recent')}</span>
              </div>
              <div className="stat-card">
                <span className="stat-icon">🏆</span>
                <span className="stat-value stat-value-sm">{topCrop ? topCrop.crop : t('dash.noFrequent')}</span>
                <span className="stat-label">{t('dash.frequent')}</span>
              </div>
            </div>

            <div className="info-card">
              <h4>📈 {t('dash.chart')}</h4>
              <div className="bar-chart" role="img" aria-label={t('dash.chart')}>
                {frequency.slice(0, 8).map((f) => (
                  <div className="bar-row" key={f.crop}>
                    <span className="bar-label">{f.crop}</span>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${Math.round((f.count / maxCount) * 100)}%` }} />
                    </div>
                    <span className="bar-count">{f.count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="info-card">
              <div className="card-head-row">
                <h4>🕘 {t('dash.history')}</h4>
                <div className="card-head-actions">
                  <button className="btn btn-ghost btn-sm" onClick={load} type="button">🔄 {t('dash.reload')}</button>
                  <button className="btn btn-danger btn-sm" onClick={handleClear} disabled={clearing} type="button">
                    🗑️ {t('dash.clearHistory')}
                  </button>
                </div>
              </div>
              {data.items.length === 0 ? (
                <p className="muted">{t('hist.empty')}</p>
              ) : (
                <div className="table-scroll">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>{t('hist.when')}</th>
                        <th>{t('hist.crop')}</th>
                        <th>{t('hist.confidence')}</th>
                        <th>{t('hist.inputs')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.map((item) => (
                        <tr key={item.id}>
                          <td>{formatWhen(item.created_at)}</td>
                          <td><strong>{item.crop}</strong></td>
                          <td>{item.confidence != null ? `${(item.confidence * 100).toFixed(1)}%` : '—'}</td>
                          <td className="inputs-cell">{formatInputs(item.inputs)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

        <div className="info-card">
          <h4>💡 {t('dash.tips')}</h4>
          <div className="tips-list">
            {TIPS.map((tip) => (
              <div className="tip-item" key={tip.icon + tip.en.slice(0, 12)}>
                <span className="tip-icon">{tip.icon}</span>
                <p>{pick(tip)}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
