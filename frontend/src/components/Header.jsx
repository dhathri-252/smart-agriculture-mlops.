export default function Header({ onNavigate }) {
  return (
    <header className="header">
      <div className="container header-inner">
        <div className="brand" onClick={() => onNavigate('home')} role="button" tabIndex={0}>
          <span className="brand-icon">🌱</span>
          <span className="brand-text">Smart Agriculture</span>
        </div>
        <nav className="nav">
          <button className="nav-link" onClick={() => onNavigate('home')}>Home</button>
          <button className="nav-link" onClick={() => onNavigate('predict')}>Crop Prediction</button>
          <button className="nav-link" onClick={() => onNavigate('about')}>About</button>
        </nav>
        <button className="btn btn-primary header-cta" onClick={() => onNavigate('predict')}>
          Predict Crop
        </button>
      </div>
    </header>
  )
}
