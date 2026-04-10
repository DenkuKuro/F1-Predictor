import { useEffect, useState } from 'react'

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
        const response = await fetch(`/api/race-info?race_id=${selectedRace.race_id}`)
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

  // Group entry list by team
  const teamMap = {}
  entryList.forEach((entry) => {
    if (!teamMap[entry.team_name]) teamMap[entry.team_name] = []
    teamMap[entry.team_name].push(entry)
  })

  return (
    <section className="page-section">
      {loading && (
        <article className="content-card">
          <p className="card-copy">Loading race information…</p>
        </article>
      )}

      {error && <p className="feedback-message error">{error}</p>}

      {details && !loading && (
        <>
          {/* Race header */}
          <article className="content-card hero-card race-hero">
            <div>
              <p className="section-kicker">Round {details.round} · {details.season} Season</p>
              <h3 className="hero-title">{details.location}</h3>
            </div>
            <div className="race-date-block">
              <p className="panel-label">Race Date</p>
              <p className="panel-value">{details.date}</p>
            </div>
          </article>

          {/* Drivers table */}
          {entryList.length > 0 && (
            <>
              <article className="content-card">
                <p className="section-kicker">Entry List</p>
                <h3>Drivers</h3>
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Driver</th>
                        <th>Team</th>
                      </tr>
                    </thead>
                    <tbody>
                      {entryList.map((entry) => (
                        <tr key={entry.driver_id}>
                          <td>{entry.first_name} {entry.last_name}</td>
                          <td>{entry.team_name}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>

              {/* Teams grid */}
              <article className="content-card">
                <p className="section-kicker">Constructors</p>
                <h3>Teams</h3>
                <div className="teams-grid">
                  {Object.entries(teamMap).map(([teamName, drivers]) => (
                    <div key={teamName} className="team-tile">
                      <p className="panel-value">{teamName}</p>
                      <div className="team-drivers">
                        {drivers.map((d) => (
                          <span key={d.driver_id} className="driver-chip">
                            {d.first_name} {d.last_name}
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
