import { useTranslation } from '../i18n/LanguageContext.jsx'

export default function Stats() {
  const { t } = useTranslation()
  const stats = [
    { value: '22', label: t('stats.crops'), icon: '🌾' },
    { value: '99.55%', label: t('stats.accuracy'), icon: '🎯' },
    { value: '7', label: t('stats.features'), icon: '🧪' },
    { value: 'Random Forest', label: t('stats.model'), icon: '🌳' },
  ]

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
