import { useState } from 'react'

function App() {
  const [teamName, setTeamName] = useState('')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!teamName.trim()) return
    setLoading(true)
    setStatus(null)

    try {
      const res = await fetch('/api/teams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team_name: teamName.trim() })
      })
      const data = await res.json()

      if (res.ok) {
        setStatus({ ok: true, message: `Team "${teamName}" inserted.` })
        setTeamName('')
      } else {
        setStatus({ ok: false, message: data.error || 'Something went wrong.' })
      }
    } catch (err) {
      setStatus({ ok: false, message: 'Could not reach the server.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>DB Test</h1>

        <label style={styles.label}>Team Name</label>
        <input
          style={styles.input}
          type="text"
          value={teamName}
          onChange={e => setTeamName(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
        />

        <button
          style={{ ...styles.button, opacity: loading ? 0.6 : 1 }}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Inserting...' : 'Insert Team'}
        </button>

        {status && (
          <p style={{ ...styles.status, color: status.ok ? '#4ade80' : '#f87171' }}>
            {status.message}
          </p>
        )}
      </div>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#0f0f0f',
    fontFamily: 'monospace',
  },
  card: {
    background: '#1a1a1a',
    border: '1px solid #2e2e2e',
    borderRadius: '8px',
    padding: '40px',
    width: '100%',
    maxWidth: '400px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  title: {
    margin: 0,
    fontSize: '24px',
    color: '#f1f1f1',
  },
  sub: {
    margin: 0,
    fontSize: '13px',
    color: '#666',
  },
  label: {
    fontSize: '13px',
    color: '#999',
    marginTop: '8px',
  },
  input: {
    padding: '10px 12px',
    borderRadius: '6px',
    border: '1px solid #2e2e2e',
    background: '#111',
    color: '#f1f1f1',
    fontSize: '14px',
    outline: 'none',
  },
  button: {
    marginTop: '8px',
    padding: '10px',
    borderRadius: '6px',
    border: 'none',
    background: '#e10600',
    color: '#fff',
    fontSize: '14px',
    cursor: 'pointer',
  },
  status: {
    margin: 0,
    fontSize: '13px',
  }
}

export default App