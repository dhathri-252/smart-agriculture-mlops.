export default function Hero({ onStart }) {
  return (
    <section id="home" className="hero">
      <div className="container hero-grid">
        <div className="hero-copy">
          <span className="badge">🌾 MLOps · Random Forest · MLflow · DVC</span>
          <h1>
            Smart Agriculture
            <span className="hero-accent">AI-Powered Crop Recommendation</span>
          </h1>
          <p className="hero-desc">
            Use soil and environmental conditions to get an AI-powered crop recommendation.
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary btn-lg" onClick={onStart}>
              Start Prediction →
            </button>
            <button className="btn btn-ghost btn-lg" onClick={() => document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' })}>
              Learn More
            </button>
          </div>
          <ul className="hero-points">
            <li>✅ 7 soil &amp; climate inputs</li>
            <li>✅ 22 supported crops</li>
            <li>✅ FastAPI + Random Forest backend</li>
          </ul>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="field-card">
            <div className="field-sky">☀️</div>
            <div className="field-rows">
              <span>🌱</span><span>🌱</span><span>🌱</span><span>🌱</span>
              <span>🌿</span><span>🌿</span><span>🌿</span><span>🌿</span>
              <span>🌾</span><span>🌾</span><span>🌾</span><span>🌾</span>
            </div>
            <div className="field-footer">
              <div>
                <strong>Live soil analysis</strong>
                <small>N · P · K · pH · Rainfall</small>
              </div>
              <span className="pulse">● Live</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
