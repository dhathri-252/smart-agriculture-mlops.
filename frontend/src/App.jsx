import { useEffect, useState } from 'react'
import { LanguageProvider, useTranslation } from './i18n/LanguageContext.jsx'
import { apiFetch, getToken, setToken } from './api.js'
import GuidedCropper from './components/GuidedCropper.jsx'
import Header from './components/Header.jsx'
import Hero from './components/Hero.jsx'
import Stats from './components/Stats.jsx'
import PredictionForm from './components/PredictionForm.jsx'
import About from './components/About.jsx'
import DailyIntelligence from './components/DailyIntelligence.jsx'
import Dashboard from './components/Dashboard.jsx'
import Assistant from './components/Assistant.jsx'
import Weather from './components/Weather.jsx'
import AuthModal from './components/AuthModal.jsx'
import Catalogue from './components/Catalogue.jsx'
import CropDetail from './components/CropDetail.jsx'

function scrollToId(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

function Shell() {
  const { t } = useTranslation()
  const [view, setView] = useState('home')
  const [user, setUser] = useState(null)
  const [authOpen, setAuthOpen] = useState(false)
  const [historyVersion, setHistoryVersion] = useState(0)
  const [selectedCrop, setSelectedCrop] = useState(null)

  // Restore session (if a token exists) on first load.
  useEffect(() => {
    if (!getToken()) return
    apiFetch('/api/auth/me', { auth: true })
      .then(setUser)
      .catch(() => setToken(''))
  }, [])

  function navigate(next) {
    setView(next)
    setSelectedCrop(null)
    window.scrollTo({ top: 0, behavior: 'auto' })
  }

  function openCrop(item) {
    setSelectedCrop(item)
    setView('cropDetail')
    window.scrollTo({ top: 0, behavior: 'auto' })
  }

  function startPrediction() {
    setView('home')
    requestAnimationFrame(() => setTimeout(() => scrollToId('predict'), 50))
  }

  function handleLogout() {
    setToken('')
    setUser(null)
    navigate('home')
  }

  function handlePredicted() {
    setHistoryVersion((v) => v + 1)
  }

  return (
    <div className="app">
      <Header
        view={view}
        onNavigate={navigate}
        user={user}
        onLogin={() => setAuthOpen(true)}
        onLogout={handleLogout}
        onStartPrediction={startPrediction}
      />
      <main>
        {view === 'home' && (
          <>
            <Hero onStart={() => scrollToId('predict')} />
            <Stats />
            <PredictionForm onPredicted={handlePredicted} />
            <About />
          </>
        )}
        {view === 'dashboard' && (
        <>
          <DailyIntelligence onNavigate={navigate} />
          <Dashboard version={historyVersion} onNavigate={navigate} />
        </>
      )}
        {view === 'assistant' && <Assistant />}
        {view === 'weather' && <Weather />}
        {view === 'advanced' && <GuidedCropper onNavigate={navigate} />}
        {view === 'catalogue' && <Catalogue onOpenCrop={openCrop} />}
        {view === 'cropDetail' && selectedCrop && (
          <CropDetail cropId={selectedCrop.id} initial={selectedCrop} onBack={() => navigate('catalogue')} />
        )}
      </main>
      <footer className="footer">
        <p>🌱 {t('footer.text')}</p>
      </footer>
      {authOpen && (
        <AuthModal
          onClose={() => setAuthOpen(false)}
          onAuthed={(authedUser, token) => {
            setToken(token)
            setUser(authedUser)
            setAuthOpen(false)
          }}
        />
      )}
    </div>
  )
}

export default function App() {
  return (
    <LanguageProvider>
      <Shell />
    </LanguageProvider>
  )
}
