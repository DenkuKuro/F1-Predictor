import { useEffect, useState } from 'react'

function Leaderboard() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/leaderboard')
      .then((r) => {
        if (!r.ok) throw new Error('Could not load leaderboard.')
        return r.json()
      })
      .then((data) => {
        setUsers(Array.isArray(data) ? data : [])
      })
      .catch(() => setError('Could not load leaderboard.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <section className="page-section">
      <article className="content-card">
        <p className="section-kicker">Rankings</p>
        <h3>Player Leaderboard</h3>

        {loading && <p className="card-copy">Loading…</p>}
        {error && <p className="feedback-message error">{error}</p>}

        {!loading && !error && users.length === 0 && (
          <p className="empty-state">No players yet.</p>
        )}

        {!loading && users.length > 0 && (
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
                {users.map((user, index) => (
                  <tr key={user.username} className={index === 0 ? 'leaderboard-top' : ''}>
                    <td>{index + 1}</td>
                    <td>{user.username}</td>
                    <td>{user.total_points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  )
}

export default Leaderboard
