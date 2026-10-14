import { useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext.jsx'

function pct(value) {
  return `${(value * 100).toFixed(1)}%`
}

export default function PredictionResult({ result, loading, onLoadRecommendations, onReset }) {
  const { t, pick } = useTranslation()
  const [showRecs, setShowRecs] = useState(false)
  const info = result.crop_info
  const confidence = result.confidence

  async function toggleRecommendations() {
    if (showRecs) {
      setShowRecs(false)
      return
    }
    setShowRecs(true)
    if (!result.recommendations) await onLoadRecommendations?.()
  }

  return (
    <div className="result-wrap">
      {/* Main result card */}
      <div className="result-card">
        <div className="result-icon">{info?.emoji || '🌾'}</div>
        <p className="result-eyebrow">{t('result.recommended')}</p>
        <h3 className="result-crop">
          {(info?.name || result.recommended_crop).toUpperCase()}
        </h3>
        <p className="result-note">{t('result.note')}</p>

        {confidence != null && (
          <div className="confidence" role="meter" aria-valuenow={Math.round(confidence * 100)}
               aria-valuemin={0} aria-valuemax={100} aria-label={t('result.confidence')}>
            <div className="confidence-label">{t('result.confidence')}</div>
            <div className="confidence-track">
              <div className="confidence-fill" style={{ width: `${Math.round(confidence * 100)}%` }} />
            </div>
            <div className="confidence-value">{pct(confidence)}</div>
          </div>
        )}
      </div>

      {/* Input range warnings (data-drift check) */}
      {Array.isArray(result.input_warnings) && result.input_warnings.length > 0 && (
        <div className="alert alert-warn">
          <strong>⚠️ {t('result.warningsTitle')}</strong>
          <ul className="warn-list">
            {result.input_warnings.map((w) => <li key={w}>{w}</li>)}
          </ul>
        </div>
      )}

      {/* Top-3 recommendations from real model probabilities */}
      {Array.isArray(result.top_predictions) && result.top_predictions.length > 0 && (
        <div className="info-card">
          <h4>🏆 {t('result.top3')}</h4>
          <ul className="top3-list">
            {result.top_predictions.map((p, idx) => (
              <li key={p.crop} className="top3-item">
                <span className="top3-rank">{idx + 1}</span>
                <span className="top3-crop">{p.crop}</span>
                <span className="top3-bar" aria-hidden="true">
                  <span
                    className="top3-fill"
                    style={{ width: p.probability != null ? `${Math.round(p.probability * 100)}%` : '0%' }}
                  />
                </span>
                <span className="top3-prob">
                  {p.probability != null ? pct(p.probability) : '—'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {/* Farmer-friendly crop information card */}
      {info && (
        <div className="info-card">
          <h4>📊 {info.name} — {t('result.typicalNote')}</h4>
          <div className="range-grid">
            <div className="range-chip">
              <span className="range-icon">🌡️</span>
              <span className="range-label">{t('result.temperatureRange')}</span>
              <span className="range-value">{info.ranges.temperature[0]} – {info.ranges.temperature[1]} °C</span>
            </div>
            <div className="range-chip">
              <span className="range-icon">💧</span>
              <span className="range-label">{t('result.humidityRange')}</span>
              <span className="range-value">{info.ranges.humidity[0]} – {info.ranges.humidity[1]} %</span>
            </div>
            <div className="range-chip">
              <span className="range-icon">🌧️</span>
              <span className="range-label">{t('result.rainfallRange')}</span>
              <span className="range-value">{info.ranges.rainfall[0]} – {info.ranges.rainfall[1]} mm</span>
            </div>
            <div className="range-chip">
              <span className="range-icon">🧪</span>
              <span className="range-label">{t('result.phRange')}</span>
              <span className="range-value">{info.ranges.ph[0]} – {info.ranges.ph[1]}</span>
            </div>
            <div className="range-chip">
              <span className="range-icon">⚖️</span>
              <span className="range-label">{t('result.npk')}</span>
              <span className="range-value">
                N {info.ranges.N[0]}–{info.ranges.N[1]} · P {info.ranges.P[0]}–{info.ranges.P[1]} · K {info.ranges.K[0]}–{info.ranges.K[1]}
              </span>
            </div>
          </div>

          <div className="guidance-list">
            <div className="guidance-item">
              <span className="guidance-icon">🪴</span>
              <div><strong>{t('result.soil')}</strong><p>{pick(info.soil)}</p></div>
            </div>
            <div className="guidance-item">
              <span className="guidance-icon">💦</span>
              <div><strong>{t('result.irrigation')}</strong><p>{pick(info.irrigation)}</p></div>
            </div>
            <div className="guidance-item">
              <span className="guidance-icon">🧴</span>
              <div><strong>{t('result.fertilizer')}</strong><p>{pick(info.fertilizer)}</p></div>
            </div>
            <div className="guidance-item">
              <span className="guidance-icon">🌱</span>
              <div><strong>{t('result.cultivation')}</strong><p>{pick(info.cultivation)}</p></div>
            </div>
          </div>
          <p className="disclaimer">ℹ️ {pick(info.disclaimer)}</p>
        </div>
      )}

      {/* Smart farming recommendations (loaded on demand) */}
      <div className="info-card">
        <button className="btn btn-secondary btn-full" onClick={toggleRecommendations} disabled={loading} type="button">
          {loading && showRecs
            ? t('result.loadingRecs')
            : showRecs
              ? t('result.hideRecommendations')
              : `🌿 ${t('result.recommendations')}`}
        </button>
        {showRecs && Array.isArray(result.recommendations) && (
          <div className="rec-grid">
            {result.recommendations.map((rec, idx) => (
              <div className="rec-card" key={`${rec.icon}-${idx}`}>
                <span className="rec-icon">{rec.icon}</span>
                <strong>{pick(rec.title)}</strong>
                <p>{pick(rec.body)}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="result-actions">
        <button className="btn btn-primary btn-lg" onClick={onReset}>
          🔄 {t('result.again')}
        </button>
      </div>

    </div>
  )
}
