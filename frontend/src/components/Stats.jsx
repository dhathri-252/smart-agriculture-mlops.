const stats = [
  { value: '22', label: 'Supported Crops', icon: '🌾' },
  { value: '99.55%', label: 'Model Accuracy', icon: '🎯' },
  { value: '7', label: 'Input Features', icon: '🧪' },
  { value: 'Random Forest', label: 'ML Model', icon: '🌳' },
]

export default function Stats() {
  return (
    <section className="stats-section">
      <div className="container stats-grid">
        {stats.map((s) => (
          <div className="stat-card" key={s.label}>
            <span className="stat-icon">{s.icon}</span>
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
