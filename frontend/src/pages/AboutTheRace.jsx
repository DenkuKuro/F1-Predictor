import { useEffect, useState } from 'react'

const SESSION_LABELS = {
  FirstPractice: 'Practice 1',
  SecondPractice: 'Practice 2',
  ThirdPractice: 'Practice 3',
  SprintQualifying: 'Sprint Qualifying',
  Sprint: 'Sprint Race',
  Qualifying: 'Qualifying',
}

function formatSessionTime(isoTime) {
  if (!isoTime) return ''
  // Convert "HH:MM:SSZ" UTC to a readable local time string
  const [h, m] = isoTime.replace('Z', '').split(':')
  const d = new Date()
  d.setUTCHours(Number(h), Number(m), 0)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function AboutTheRace({ selectedRace }) {
  const [details, setDetails] = useState(null)
  const [entryList, setEntryList] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!selectedRace) {
      setDetails(null)
      setEntryList([])
      setError('')
      return
    }

    const load = async () => {
      setLoading(true)
      setError('')
      setDetails(null)
      setEntryList([])
      try {
        const response = await fetch(
          `/api/race-info?season=${selectedRace.season}&round=${selectedRace.round}`
        )
        if (!response.ok) throw new Error('Could not load race info.')
        const data = await response.json()
        setDetails(data.details)
        setEntryList(data.entry_list)
      } catch {
        setError('Could not load race information. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [selectedRace])

  if (!selectedRace) {
    return (
      <section className="page-section">
        <article className="content-card">
          <p className="section-kicker">No Race Selected</p>
          <h3>Select a race from the sidebar</h3>
          <p className="card-copy">
            Use the Recent Races dropdown in the left navigation to choose a race and view its details.
          </p>
        </article>
      </section>
    )
  }

  const sessionEntries = details ? Object.entries(details.sessions) : []

  // Group entry list by team for the constructor section
  const teamMap = {}
  entryList.forEach((entry) => {
    if (!teamMap[entry.team]) {
      teamMap[entry.team] = { nationality: entry.team_nationality, drivers: [] }
    }
    teamMap[entry.team].drivers.push(entry)
  })

  return (
    <section className="page-section">
      {loading && (
        <article className="content-card">
          <p className="card-copy">Loading race information…</p>
        </article>
      )}

      {error && (
        <p className="feedback-message error">{error}</p>
      )}

      {details && !loading && (
        <>
          {/* Race header */}
          <article className="content-card hero-card race-hero">
            <div>
              <p className="section-kicker">Round {details.round} · {details.season} Season</p>
              <h3 className="hero-title">{details.name}</h3>
              <p className="card-copy">{details.circuit}</p>
              <p className="card-copy">{details.locality}, {details.country}</p>
            </div>
            <div className="race-date-block">
              <p className="panel-label">Race Date</p>
              <p className="panel-value">{details.date}</p>
              {details.time && (
                <p className="card-copy">{formatSessionTime(details.time)} local</p>
              )}
            </div>
          </article>

          {/* Session schedule */}
          {sessionEntries.length > 0 && (
            <article className="content-card">
              <p className="section-kicker">Weekend Schedule</p>
              <h3>Session Dates</h3>
              <div className="sessions-grid">
                {sessionEntries.map(([key, session]) => (
                  <div key={key} className="session-tile">
                    <p className="panel-label">{SESSION_LABELS[key] ?? key}</p>
                    <p className="panel-value">{session.date}</p>
                    {session.time && (
                      <p className="stat-label">{formatSessionTime(session.time)} local</p>
                    )}
                  </div>
                ))}
              </div>
            </article>
          )}

          {/* Drivers & Teams */}
          {entryList.length > 0 && (
            <>
              <article className="content-card">
                <p className="section-kicker">Entry List</p>
                <h3>Drivers</h3>
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Code</th>
                        <th>Driver</th>
                        <th>Nationality</th>
                        <th>Team</th>
                      </tr>
                    </thead>
                    <tbody>
                      {entryList.map((entry) => (
                        <tr key={entry.car_number}>
                          <td>{entry.car_number}</td>
                          <td><span className="driver-code">{entry.code}</span></td>
                          <td>{entry.first_name} {entry.last_name}</td>
                          <td>{entry.nationality}</td>
                          <td>{entry.team}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>

              <article className="content-card">
                <p className="section-kicker">Constructors</p>
                <h3>Teams</h3>
                <div className="teams-grid">
                  {Object.entries(teamMap).map(([teamName, team]) => (
                    <div key={teamName} className="team-tile">
                      <p className="panel-value">{teamName}</p>
                      <p className="stat-label">{team.nationality}</p>
                      <div className="team-drivers">
                        {team.drivers.map((d) => (
                          <span key={d.car_number} className="driver-chip">
                            #{d.car_number} {d.first_name} {d.last_name}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            </>
          )}
        </>
      )}
    </section>
  )
}

export default AboutTheRace
