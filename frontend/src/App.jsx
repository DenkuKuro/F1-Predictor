import { useState, useEffect } from 'react'
import './App.css'
import Landing from './pages/Landing'
import Leaderboard from './pages/Leaderboard'
import LogIn from './pages/LogIn'
import SignUp from './pages/SignUp'
import MakePrediction from './pages/MakePrediction'
import ViewPredictions from './pages/ViewPredictions'
import ViewUserPredictions from './pages/ViewUserPredictions'
import AboutTheRace from './pages/AboutTheRace'
import RaceResults from './pages/RaceResults'

const PROTECTED_PAGES = new Set(['results', 'leaderboard', 'makePrediction', 'viewPredictions', 'myPredictions'])

const navigationItems = [
  { id: 'aboutRace', label: 'About The Race' },
  { id: 'results', label: 'See Results' },
  { id: 'leaderboard', label: 'Leaderboard' },
  { id: 'makePrediction', label: 'Make Prediction' },
  { id: 'viewPredictions', label: 'View Predictions' },
  { id: 'myPredictions', label: 'My Predictions' },
  { id: 'login', label: 'Login' },
  { id: 'signup', label: 'Sign Up' },
]

function App() {
  const [activePage, setActivePage] = useState('landing')
  const [recentRaces, setRecentRaces] = useState([])
  const [selectedRace, setSelectedRace] = useState(null)
  const [currentUser, setCurrentUser] = useState(() => {
    const id = localStorage.getItem('user_id')
    const username = localStorage.getItem('username')
    return id && username ? { user_id: id, username } : null
  })

  useEffect(() => {
    fetch('/api/recent-races')
      .then((r) => r.json())
      .then((data) => { if (Array.isArray(data)) setRecentRaces(data) })
      .catch(() => {})
  }, [])

  const handleLogin = (user) => {
    setCurrentUser(user)
    setActivePage('leaderboard')
  }

  const handleLogout = () => {
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
    setCurrentUser(null)
    setActivePage('landing')
  }

  const handleNavClick = (id) => {
    if (PROTECTED_PAGES.has(id) && !currentUser) {
      setActivePage('login')
    } else {
      setActivePage(id)
    }
  }

  const pageTitle = activePage === 'landing'
    ? null
    : navigationItems.find((item) => item.id === activePage)?.label

  const renderPage = () => {
    switch (activePage) {
      case 'landing':
        return <Landing onNavigate={setActivePage} />
      case 'aboutRace':
        return <AboutTheRace selectedRace={selectedRace} />
      case 'results':
        return <RaceResults selectedRace={selectedRace} />
      case 'makePrediction':
        return <MakePrediction />
      case 'viewPredictions':
        return <ViewPredictions />
      case 'myPredictions':
        return <ViewUserPredictions />
      case 'login':
        return <LogIn onLogin={handleLogin} />
      case 'signup':
        return <SignUp />
      case 'leaderboard':
      default:
        return <Leaderboard />
    }
  }

  // Logged out: show only About The Race + Login + Sign Up
  // Logged in: show everything except Login + Sign Up
  const visibleNav = currentUser
    ? navigationItems.filter((item) => item.id !== 'login' && item.id !== 'signup')
    : navigationItems.filter((item) => !PROTECTED_PAGES.has(item.id))

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block brand-clickable" onClick={() => setActivePage('landing')}>
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
          {visibleNav.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`nav-button ${activePage === item.id ? 'active' : ''}`}
              onClick={() => handleNavClick(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {currentUser && (
          <div className="user-block">
            <p className="panel-label">Signed in as</p>
            <p className="user-name">{currentUser.username}</p>
            <button className="logout-button" onClick={handleLogout}>
              Log Out
            </button>
          </div>
        )}
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Formula 1 Prediction Database Project</p>
            {pageTitle && <h2 className="page-title">{pageTitle}</h2>}
          </div>
        </header>

        {renderPage()}
      </main>
    </div>
  )
}

export default App
