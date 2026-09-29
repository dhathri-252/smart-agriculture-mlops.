import Header from './components/Header.jsx'
import Hero from './components/Hero.jsx'
import Stats from './components/Stats.jsx'
import PredictionForm from './components/PredictionForm.jsx'
import About from './components/About.jsx'

function scrollTo(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

export default function App() {
  return (
    <div className="app">
      <Header onNavigate={scrollTo} />
      <main>
        <Hero onStart={() => scrollTo('predict')} />
        <Stats />
        <PredictionForm />
        <About />
      </main>
      <footer className="footer">
        <p>
          🌱 Smart Agriculture Prediction System — Random Forest · MLflow · DVC · FastAPI · React
        </p>
      </footer>
    </div>
  )
}
