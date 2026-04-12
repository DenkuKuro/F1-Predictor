import { useEffect, useState } from 'react'

function Leaderboard({ currentUser }) {
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
        <h3>Global Leaderboard</h3>

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
                {users.map((user, index) => {
                  const isCurrentUser = currentUser && user.username === currentUser.username
                  return (
                    <tr key={user.username} className={index === 0 ? 'leaderboard-top' : ''} style={isCurrentUser ? { background: 'rgba(225, 6, 0, 0.12)', borderLeft: '2px solid #e10600' } : {}}>
                      <td>{index + 1}</td>
                      <td style={{ fontWeight: isCurrentUser ? 'bold' : 'normal' }}>
                        {user.username}{isCurrentUser && <span style={{ fontSize: '0.65rem', verticalAlign: 'middle', background: '#e10600', color: '#fff', padding: '2px 4px', borderRadius: '3px', marginLeft: '5px' }}>YOU</span>}
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
