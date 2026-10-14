import { useState } from 'react'
import PredictionResult from './PredictionResult.jsx'
import { useTranslation } from '../i18n/LanguageContext.jsx'
import { API_URL, apiFetch, authHeaders } from '../api.js'

const FIELDS = [
  { key: 'N', labelKey: 'form.N', placeholder: '90', unit: 'ratio', step: '1' },
  { key: 'P', labelKey: 'form.P', placeholder: '42', unit: 'ratio', step: '1' },
  { key: 'K', labelKey: 'form.K', placeholder: '43', unit: 'ratio', step: '1' },
  { key: 'temperature', labelKey: 'form.temperature', placeholder: '20.87', unit: '°C', step: '0.01' },
  { key: 'humidity', labelKey: 'form.humidity', placeholder: '82', unit: '%', step: '0.01' },
  { key: 'ph', labelKey: 'form.ph', placeholder: '6.5', unit: 'pH', step: '0.01' },
  { key: 'rainfall', labelKey: 'form.rainfall', placeholder: '202.93', unit: 'mm', step: '0.01' },
]

const INITIAL = { N: '', P: '', K: '', temperature: '', humidity: '', ph: '', rainfall: '' }

export default function PredictionForm({ onPredicted }) {
  const { t } = useTranslation()
  const [values, setValues] = useState(INITIAL)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [payload, setPayload] = useState(null)
  const [apiError, setApiError] = useState('')

  function handleChange(key, raw) {
    setValues((v) => ({ ...v, [key]: raw }))
    setErrors((e) => ({ ...e, [key]: '' }))
    setApiError('')
  }

  function fillExample() {
    setValues({ N: '90', P: '42', K: '43', temperature: '20.87', humidity: '82', ph: '6.5', rainfall: '202.93' })
    setErrors({})
    setApiError('')
    setResult(null)
  }

  function validate() {
    const next = {}
    for (const f of FIELDS) {
      const label = t(f.labelKey)
      const raw = String(values[f.key]).trim()
      if (raw === '') {
        next[f.key] = `${label} ${t('form.required')}`
        continue
      }
      if (!Number.isFinite(Number(raw))) {
        next[f.key] = `${label} ${t('form.invalidNumber')}`
      }
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setApiError('')
    setResult(null)
    if (!validate()) return
    const body = {
      N: Number(values.N),
      P: Number(values.P),
      K: Number(values.K),
      temperature: Number(values.temperature),
      humidity: Number(values.humidity),
      ph: Number(values.ph),
      rainfall: Number(values.rainfall),
    }
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        let msg = `Prediction request failed (HTTP ${res.status}).`
        try {
          const data = await res.json()
          if (data?.detail) {
            msg = Array.isArray(data.detail)
              ? data.detail.map((d) => d.msg).join(' ')
              : String(data.detail)
          }
        } catch { /* keep default message */ }
        throw new Error(msg)
      }
      const data = await res.json()
      setResult(data)
      setPayload(body)
      onPredicted?.()
    } catch (err) {
      if (err instanceof TypeError) setApiError(t('form.offline'))
      else setApiError(err.message || t('form.failed'))
    } finally {
      setLoading(false)
    }
  }
  async function loadRecommendations() {
    if (!payload) return
    setLoading(true)
    setApiError('')
    try {
      const recs = await apiFetch('/api/recommendations', {
        method: 'POST',
        body: payload,
        auth: true,
      })
      setResult((r) => ({ ...r, recommendations: recs.recommendations }))
    } catch (err) {
      setApiError(err.code === 'network' ? t('form.offline') : (err.message || t('form.failed')))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section id="predict" className="predict-section">
      <div className="container">
        <div className="section-head">
          <h2>🌱 {t('form.title')}</h2>
          <p>{t('form.subtitle')}</p>
          {!result && (
            <button className="btn btn-ghost btn-sm" onClick={fillExample} type="button">
              {t('form.fillExample')}
            </button>
          )}
        </div>

        {!result ? (
          <form className="form-card" onSubmit={handleSubmit} noValidate>
            <div className="form-grid">
              {FIELDS.map((f) => (
                <div className="field" key={f.key}>
                  <label htmlFor={`input-${f.key}`}>
                    {t(f.labelKey)} <span className="unit">· {f.unit}</span>
                  </label>
                  <input
                    id={`input-${f.key}`}
                    type="number"
                    step={f.step}
                    placeholder={f.placeholder}
                    value={values[f.key]}
                    onChange={(e) => handleChange(f.key, e.target.value)}
                    disabled={loading}
                    aria-invalid={Boolean(errors[f.key])}
                  />
                  {errors[f.key] && <span className="field-error">{errors[f.key]}</span>}
                </div>
              ))}
            </div>

            {apiError && <div className="alert alert-error">⚠️ {apiError}</div>}

            <button className="btn btn-primary btn-lg btn-full" type="submit" disabled={loading}>
              {loading ? (
                <span className="loading-inline">
                  <span className="spinner" /> {t('form.loading')}
                </span>
              ) : (
                t('form.submit')
              )}
            </button>
          </form>
        ) : (
          <>
            {apiError && (
              <div className="alert alert-error" style={{ maxWidth: 760, margin: '0 auto 14px' }}>
                ⚠️ {apiError}
              </div>
            )}
            <PredictionResult
              result={result}
              loading={loading}
              onLoadRecommendations={loadRecommendations}
              onReset={() => {
                setResult(null)
                setPayload(null)
                setApiError('')
              }}
            />
          </>
        )}
      </div>
    </section>
  )
}
