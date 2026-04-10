import { useState, useEffect } from 'react'
import './App.css'
import Leaderboard from './pages/Leaderboard'
import LogIn from './pages/LogIn'
import SignUp from './pages/SignUp'
import MakePrediction from './pages/MakePrediction'
import ViewPredictions from './pages/ViewPredictions'
import ViewUserPredictions from './pages/ViewUserPredictions'
import AboutTheRace from './pages/AboutTheRace'
import RaceResults from './pages/RaceResults'

const navigationItems = [
  { id: 'aboutRace', label: 'About The Race' },
  { id: 'results', label: 'See Results'},
  { id: 'leaderboard', label: 'Leaderboard' },
  { id: 'makePrediction', label: 'Make Prediction' },
  { id: 'viewPredictions', label: 'View Predictions' },
  { id: 'myPredictions', label: 'My Predictions' },
  { id: 'login', label: 'Login' },
  { id: 'signup', label: 'Sign Up'}
]

function App() {
  const [activePage, setActivePage] = useState('leaderboard')
  const [recentRaces, setRecentRaces] = useState([])
  const [selectedRace, setSelectedRace] = useState(null)

  useEffect(() => {
    fetch('/api/recent-races')
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setRecentRaces(data)
      })
      .catch(() => {})
  }, [])

  const renderPage = () => {
    switch (activePage) {
      case 'aboutRace':
        return <AboutTheRace selectedRace={selectedRace} />
      case 'makePrediction':
        return <MakePrediction />
      case 'viewPredictions':
        return <ViewPredictions />
      case 'myPredictions':
        return <ViewUserPredictions />
      case 'login':
        return <LogIn />
      case 'signup':
        return <SignUp />
      case 'leaderboard':
        return <Leaderboard />
      case 'results':
        return <RaceResults />
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

        <div className="race-selector">
          <p className="panel-label">Recent Races</p>
          <select
            className="app-input race-dropdown"
            value={selectedRace ? selectedRace.race_id : ''}
            onChange={(e) => {
              const race = recentRaces.find((r) => String(r.race_id) === e.target.value)
              setSelectedRace(race ?? null)
            }}
          >
            <option value="">Select a race…</option>
            {recentRaces.map((race) => (
              <option key={race.race_id} value={race.race_id}>
                {race.name} — {race.date}
              </option>
            ))}
          </select>
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
