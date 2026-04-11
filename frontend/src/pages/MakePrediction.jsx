import { useEffect, useState } from 'react'

const initialPicks = {
  p1_pick: '',
  p2_pick: '',
  p3_pick: '',
  safety_car_prediction: false,
}

function MakePrediction({ selectedRace, currentUser }) {
  const [picks, setPicks] = useState(initialPicks)
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    fetch('/api/drivers')
      .then((r) => {
        if (!r.ok) throw new Error()
        return r.json()
      })
      .then((data) => setDrivers(Array.isArray(data) ? data : []))
      .catch(() => setError('Could not load drivers.'))
      .finally(() => setPageLoading(false))
  }, [])

  const handleChange = (e) => {
    setPicks((cur) => ({ ...cur, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!selectedRace) {
      setError('Please select a race from the left nav bar first.')
      return
    }
    if (!picks.p1_pick || !picks.p2_pick || !picks.p3_pick) {
      setError('Please select a driver for P1, P2, and P3.')
      return
    }
    if (new Set([picks.p1_pick, picks.p2_pick, picks.p3_pick]).size !== 3) {
      setError('P1, P2, and P3 must all be different drivers.')
      return
    }

    try {
      setLoading(true)
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(currentUser.user_id),
          race_id: Number(selectedRace.race_id),
          p1_pick: Number(picks.p1_pick),
          p2_pick: Number(picks.p2_pick),
          p3_pick: Number(picks.p3_pick),
          safety_car_prediction: picks.safety_car_prediction,
        }),
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error || 'Could not submit prediction.')
      }
      setSuccess('Prediction submitted successfully.')
      setPicks(initialPicks)
    } catch (err) {
      setError(err.message || 'Could not submit prediction.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page-section">
      <div className="two-column-layout">
        <article className="content-card form-card">
          <p className="section-kicker">Make Prediction</p>
          <h3>Submit a race prediction</h3>

          {pageLoading && <p className="card-copy">Loading drivers…</p>}

          <form className="app-form" onSubmit={handleSubmit}>

            {/* Race — read-only, driven by the sidebar selector */}
            <label className="field-label">Race</label>
            <div className="race-display-field">
              {selectedRace ? (
                <span>{selectedRace.name} — {selectedRace.date}</span>
              ) : (
                <span className="race-hint">← Select a race from the left nav bar</span>
              )}
            </div>

            {/* P1 */}
            <label className="field-label" htmlFor="p1_pick">P1</label>
            <select id="p1_pick" name="p1_pick" className="app-input" value={picks.p1_pick} onChange={handleChange}>
              <option value="">Select a driver</option>
              {drivers.map((d) => (
                <option key={d.driver_id} value={d.driver_id}>
                  {d.first_name} {d.last_name}
                </option>
              ))}
            </select>

            {/* P2 */}
            <label className="field-label" htmlFor="p2_pick">P2</label>
            <select id="p2_pick" name="p2_pick" className="app-input" value={picks.p2_pick} onChange={handleChange}>
              <option value="">Select a driver</option>
              {drivers.map((d) => (
                <option key={d.driver_id} value={d.driver_id}>
                  {d.first_name} {d.last_name}
                </option>
              ))}
            </select>

            {/* P3 */}
            <label className="field-label" htmlFor="p3_pick">P3</label>
            <select id="p3_pick" name="p3_pick" className="app-input" value={picks.p3_pick} onChange={handleChange}>
              <option value="">Select a driver</option>
              {drivers.map((d) => (
                <option key={d.driver_id} value={d.driver_id}>
                  {d.first_name} {d.last_name}
                </option>
              ))}
            </select>

            {/* Safety car — Yes / No toggle */}
            <label className="field-label">Safety Car</label>
            <div className="safety-car-toggle">
              <button
                type="button"
                className={`toggle-btn ${picks.safety_car_prediction === true ? 'toggle-active' : ''}`}
                onClick={() => setPicks((cur) => ({ ...cur, safety_car_prediction: true }))}
              >
                Yes
              </button>
              <button
                type="button"
                className={`toggle-btn ${picks.safety_car_prediction === false ? 'toggle-active' : ''}`}
                onClick={() => setPicks((cur) => ({ ...cur, safety_car_prediction: false }))}
              >
                No
              </button>
            </div>

            <button type="submit" className="primary-button full-width" disabled={loading}>
              {loading ? 'Submitting…' : 'Submit Prediction'}
            </button>
          </form>

          {error && <p className="feedback-message error">{error}</p>}
          {success && <p className="feedback-message success">{success}</p>}
        </article>

        <article className="content-card">
          <p className="section-kicker">Notes</p>
          <h3>Prediction Rules</h3>
          <p className="card-copy">
            Select a race from the left nav bar, then choose who you think will
            finish P1, P2, and P3. You may also predict whether a safety car will
            be deployed. All three driver picks must be different.
          </p>
          <ul className="rules-list">
            <li>Correct P1, P2, or P3 position — <strong>100 pts</strong></li>
            <li>Driver on podium but wrong position — <strong>50 pts</strong></li>
            <li>Correct safety car call — <strong>50 pts</strong></li>
          </ul>
        </article>
      </div>
    </section>
  )
}

export default MakePrediction
