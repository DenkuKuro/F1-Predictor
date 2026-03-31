import { useState } from 'react'
import './App.css'
import Leaderboard from './pages/Leaderboard'
import LogIn from './pages/LogIn'
import SignIn from './pages/SignIn'
import MakePrediction from './pages/MakePrediction'
import ViewPredictions from './pages/ViewPredictions'
import ViewUserPredictions from './pages/ViewUserPredictions'

const navigationItems = [
  { id: 'leaderboard', label: 'Leaderboard' },
  { id: 'makePrediction', label: 'Make Prediction' },
  { id: 'viewPredictions', label: 'View Predictions' },
  { id: 'myPredictions', label: 'My Predictions' },
  { id: 'login', label: 'Login' },
  { id: 'signin', label: 'Sign In'}
]

function App() {
  const [activePage, setActivePage] = useState('leaderboard')

  const renderPage = () => {
    switch (activePage) {
      case 'makePrediction':
        return <MakePrediction />
      case 'viewPredictions':
        return <ViewPredictions />
      case 'myPredictions':
        return <ViewUserPredictions />
      case 'login':
        return <LogIn />
      case 'signin':
        return <SignIn />
      case 'leaderboard':
      default:
        return <Leaderboard />
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <h1>F1 Predictor</h1>
        </div>

        <nav className="nav-list" aria-label="Primary navigation">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`nav-button ${activePage === item.id ? 'active' : ''}`}
              onClick={() => setActivePage(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Formula 1 Prediction Database Project</p>
            <h2 className="page-title">
              {navigationItems.find((item) => item.id === activePage)?.label}
            </h2>
          </div>
        </header>

        {renderPage()}
      </main>
    </div>
  )
}

export default App
