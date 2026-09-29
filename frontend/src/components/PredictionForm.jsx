import { useState } from 'react'
import PredictionResult from './PredictionResult.jsx'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const FIELDS = [
  { key: 'N', label: 'Nitrogen (N)', placeholder: '90', unit: 'ratio', step: '1' },
  { key: 'P', label: 'Phosphorus (P)', placeholder: '42', unit: 'ratio', step: '1' },
  { key: 'K', label: 'Potassium (K)', placeholder: '43', unit: 'ratio', step: '1' },
  { key: 'temperature', label: 'Temperature (°C)', placeholder: '20.87', unit: '°C', step: '0.01' },
  { key: 'humidity', label: 'Humidity (%)', placeholder: '82', unit: '%', step: '0.01' },
  { key: 'ph', label: 'Soil pH', placeholder: '6.5', unit: 'pH', step: '0.01' },
  { key: 'rainfall', label: 'Rainfall (mm)', placeholder: '202.93', unit: 'mm', step: '0.01' },
]

const INITIAL = { N: '', P: '', K: '', temperature: '', humidity: '', ph: '', rainfall: '' }

export default function PredictionForm() {
  const [values, setValues] = useState(INITIAL)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
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
      const raw = String(values[f.key]).trim()
      if (raw === '') {
        next[f.key] = `${f.label} is required.`
        continue
      }
      const num = Number(raw)
      if (!Number.isFinite(num)) {
        next[f.key] = `${f.label} must be a valid number.`
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
    setLoading(true)
    try {
      const payload = {
        N: Number(values.N),
        P: Number(values.P),
        K: Number(values.K),
        temperature: Number(values.temperature),
        humidity: Number(values.humidity),
        ph: Number(values.ph),
        rainfall: Number(values.rainfall),
      }
      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        let msg = `Prediction request failed (HTTP ${res.status}).`
        try {
          const data = await res.json()
          if (data?.detail) msg = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join(' ') : JSON.stringify(data.detail)
        } catch { /* keep default */ }
        throw new Error(msg)
      }
      const data = await res.json()
      setResult(data.recommended_crop)
    } catch (err) {
      if (err instanceof TypeError) {
        setApiError('Unable to connect to the prediction service. Please make sure the FastAPI backend is running.')
      } else {
        setApiError(err.message || 'Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <section id="predict" className="predict-section">
      <div className="container">
        <div className="section-head">
          <h2>🌱 Crop Prediction</h2>
          <p>Enter soil &amp; climate values — the AI model recommends the best crop.</p>
          <button className="btn btn-ghost btn-sm" onClick={fillExample} type="button">
            Fill example values
          </button>
        </div>

        {!result ? (
          <form className="form-card" onSubmit={handleSubmit} noValidate>
            <div className="form-grid">
              {FIELDS.map((f) => (
                <div className="field" key={f.key}>
                  <label htmlFor={`input-${f.key}`}>
                    {f.label} <span className="unit">· {f.unit}</span>
                  </label>
                  <input
                    id={`input-${f.key}`}
                    type="number"
                    step={f.step}
                    placeholder={f.placeholder}
                    value={values[f.key]}
                    onChange={(e) => handleChange(f.key, e.target.value)}
                    disabled={loading}
                  />
                  {errors[f.key] && <span className="field-error">{errors[f.key]}</span>}
                </div>
              ))}
            </div>

            {apiError && <div className="alert alert-error">⚠️ {apiError}</div>}

            <button className="btn btn-primary btn-lg btn-full" type="submit" disabled={loading}>
              {loading ? (
                <span className="loading-inline">
                  <span className="spinner" /> Analyzing agricultural conditions...
                </span>
              ) : (
                'Predict Crop'
              )}
            </button>
          </form>
        ) : (
          <PredictionResult
            crop={result}
            onReset={() => {
              setResult(null)
              setApiError('')
            }}
          />
        )}
      </div>
    </section>
  )
}
