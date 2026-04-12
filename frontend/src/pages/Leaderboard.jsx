import { useEffect, useState } from 'react'

function Leaderboard({ currentUser }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [races, setRaces] = useState([])
  const [selectedRaceIds, setSelectedRaceIds] = useState([])
  const [filterLoading, setFilterLoading] = useState(false)

  const [stats, setStats] = useState(null)

  // Fetch race list for the division filter
  useEffect(() => {
    fetch('/api/races')
      .then((r) => r.json())
      .then((data) => { if (Array.isArray(data)) setRaces(data) })
      .catch(() => {})
  }, [])

  // Fetch overall aggregation stats
  useEffect(() => {
    fetch('/api/stats/prediction-summary')
      .then((r) => r.json())
      .then((data) => setStats(data))
      .catch(() => {})
  }, [])

  const fetchLeaderboard = (raceIds) => {
    const url = raceIds.length > 0
      ? `/api/leaderboard/division?race_ids=${raceIds.join(',')}`
      : '/api/leaderboard'

    setFilterLoading(true)
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error('Could not load leaderboard.')
        return r.json()
      })
      .then((data) => {
        setUsers(Array.isArray(data) ? data : [])
        setError('')
      })
      .catch(() => setError('Could not load leaderboard.'))
      .finally(() => {
        setLoading(false)
        setFilterLoading(false)
      })
  }

  useEffect(() => { fetchLeaderboard([]) }, [])

  const toggleRace = (raceId) => {
    const next = selectedRaceIds.includes(raceId)
      ? selectedRaceIds.filter((id) => id !== raceId)
      : [...selectedRaceIds, raceId]
    setSelectedRaceIds(next)
    fetchLeaderboard(next)
  }

  const clearFilter = () => {
    setSelectedRaceIds([])
    fetchLeaderboard([])
  }

  return (
    <section className="page-section">

      {/* ── Aggregation stats card ── */}
      {stats && stats.total_predictions > 0 && (
        <article className="content-card">
          <p className="section-kicker">Overall Stats</p>
          <div className="stats-grid">
            <div>
              <p className="panel-label">Predictions</p>
              <p className="panel-value">{stats.total_predictions}</p>
            </div>
            <div>
              <p className="panel-label">Active Players</p>
              <p className="panel-value">{stats.total_users}</p>
            </div>
            <div>
              <p className="panel-label">Highest Score</p>
              <p className="panel-value">{stats.max_points} pts</p>
            </div>
            <div>
              <p className="panel-label">Avg Score</p>
              <p className="panel-value">{stats.avg_points} pts</p>
            </div>
          </div>
        </article>
      )}

      {/* ── Leaderboard card ── */}
      <article className="content-card">
        <p className="section-kicker">Rankings</p>
        <h3>Global Leaderboard</h3>

        {/* Division filter: race checkboxes */}
        {races.length > 0 && (
          <div className="race-filter-section">
            <p className="panel-label" style={{ marginBottom: '10px' }}>
              Filter — show only users who predicted all selected races
            </p>
            <div className="race-filter-chips">
              {races.map((race) => (
                <label
                  key={race.race_id}
                  className={`race-chip${selectedRaceIds.includes(race.race_id) ? ' race-chip-active' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedRaceIds.includes(race.race_id)}
                    onChange={() => toggleRace(race.race_id)}
                    style={{ display: 'none' }}
                  />
                  {race.location} {String(race.race_date ?? '').slice(0, 4)}
                </label>
              ))}
            </div>
            {selectedRaceIds.length > 0 && (
              <p className="card-copy" style={{ marginTop: '8px', fontSize: '0.85rem' }}>
                Showing users who predicted all {selectedRaceIds.length} selected race{selectedRaceIds.length !== 1 ? 's' : ''}.
                {' '}
                <button className="clear-filter-btn" onClick={clearFilter}>Clear filter</button>
              </p>
            )}
          </div>
        )}

        {(loading || filterLoading) && <p className="card-copy">Loading…</p>}
        {error && <p className="feedback-message error">{error}</p>}

        {!loading && !filterLoading && !error && users.length === 0 && (
          <p className="empty-state">
            {selectedRaceIds.length > 0
              ? 'No users have predicted all selected races.'
              : 'No players yet.'}
          </p>
        )}

        {!loading && !filterLoading && users.length > 0 && (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Username</th>
                  <th>Points</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user, index) => {
                  const isCurrentUser = currentUser && user.username === currentUser.username
                  return (
                    <tr
                      key={user.username}
                      className={index === 0 ? 'leaderboard-top' : ''}
                      style={isCurrentUser ? { background: 'rgba(225, 6, 0, 0.12)', borderLeft: '2px solid #e10600' } : {}}
                    >
                      <td>{index + 1}</td>
                      <td style={{ fontWeight: isCurrentUser ? 'bold' : 'normal' }}>
                        {user.username}
                        {isCurrentUser && (
                          <span style={{ fontSize: '0.65rem', verticalAlign: 'middle', background: '#e10600', color: '#fff', padding: '2px 4px', borderRadius: '3px', marginLeft: '5px' }}>
                            YOU
                          </span>
                        )}
                      </td>
                      <td>{user.total_points}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  )
}

export default Leaderboard
