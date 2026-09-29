export default function PredictionResult({ crop, onReset }) {
  return (
    <div className="result-card">
      <div className="result-icon">🌾</div>
      <p className="result-eyebrow">Recommended Crop</p>
      <h3 className="result-crop">{String(crop).toUpperCase()}</h3>
      <p className="result-note">Based on the soil and environmental conditions provided.</p>
      <button className="btn btn-secondary" onClick={onReset}>
        Predict Again
      </button>
    </div>
  )
}
