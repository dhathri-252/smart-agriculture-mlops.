export default function About() {
  return (
    <section id="about" className="about-section">
      <div className="container about-card">
        <h2>🌿 About This Project</h2>
        <p>
          Smart Agriculture Prediction System uses a machine learning model to recommend a
          suitable crop based on soil and environmental conditions.
        </p>
        <div className="about-grid">
          <div className="about-item"><span>🌳</span><div><strong>Random Forest Classifier</strong><small>Trained &amp; selected as the best model</small></div></div>
          <div className="about-item"><span>🌾</span><div><strong>22 crop classes</strong><small>Covering major Indian crops</small></div></div>
          <div className="about-item"><span>🧪</span><div><strong>7 input features</strong><small>N, P, K, temperature, humidity, pH, rainfall</small></div></div>
          <div className="about-item"><span>📊</span><div><strong>MLflow experiment tracking</strong><small>Metrics, params &amp; model artifacts</small></div></div>
          <div className="about-item"><span>🗂️</span><div><strong>DVC dataset versioning</strong><small>Raw dataset tracked with DVC</small></div></div>
          <div className="about-item"><span>⚡</span><div><strong>FastAPI backend</strong><small>React app calls POST /predict</small></div></div>
        </div>
      </div>
    </section>
  )
}
