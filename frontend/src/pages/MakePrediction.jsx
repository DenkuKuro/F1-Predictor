import { useEffect, useState } from 'react'

const initialForm = {
  user_id: '',
  race_id: '',
  p1_pick: '',
  p2_pick: '',
  p3_pick: '',
  safety_car_prediction: false,
}

function MakePrediction() {
  const [formData, setFormData] = useState(initialForm)
  const [races, setRaces] = useState([])
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    const loadFormOptions = async () => {
      try {
        setPageLoading(true)
        setError('')

        const [racesResponse, driversResponse] = await Promise.all([
          fetch('/api/races'),
          fetch('/api/drivers'),
        ])

        if (!racesResponse.ok || !driversResponse.ok) {
          throw new Error('Could not load form data.')
        }

        const racesData = await racesResponse.json()
        const driversData = await driversResponse.json()

        const raceRows = Array.isArray(racesData) ? racesData : []
        const driverRows = Array.isArray(driversData) ? driversData : []

        setRaces(raceRows)
        setDrivers(driverRows)
        setFormData((current) => ({
          ...current,
          race_id: raceRows[0]?.race_id ? String(raceRows[0].race_id) : '',
        }))
      } catch (fetchError) {
        setRaces([])
        setDrivers([])
        setError('No data available yet.')
      } finally {
        setPageLoading(false)
      }
    }

    loadFormOptions()
  }, [])

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    setFormData((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (
      !formData.user_id ||
      !formData.race_id ||
      !formData.p1_pick ||
      !formData.p2_pick ||
      !formData.p3_pick
    ) {
      setError('Please complete every field before submitting.')
      return
    }

    const selectedDrivers = [formData.p1_pick, formData.p2_pick, formData.p3_pick]
    if (new Set(selectedDrivers).size !== selectedDrivers.length) {
      setError('P1, P2, and P3 must all be different drivers.')
      return
    }

    try {
      setLoading(true)

      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(formData.user_id),
          race_id: Number(formData.race_id),
          p1_pick: Number(formData.p1_pick),
          p2_pick: Number(formData.p2_pick),
          p3_pick: Number(formData.p3_pick),
          safety_car_prediction: formData.safety_car_prediction,
        }),
      })

      if (!response.ok) {
        throw new Error('Could not submit prediction.')
      }

      setSuccess('Prediction submitted successfully.')
      setFormData({
        ...initialForm,
        race_id: races[0]?.race_id ? String(races[0].race_id) : '',
      })
    } catch (fetchError) {
      setError('Could not submit prediction.')
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

          {pageLoading && <p className="card-copy">Loading form data...</p>}

          <form className="app-form" onSubmit={handleSubmit}>
            <label className="field-label" htmlFor="user_id"> User ID</label>
            <input id="user_id" name="user_id" type="number" className="app-input" value={formData.user_id} onChange={handleChange} />

            <label className="field-label" htmlFor="race_id"> Race</label>
            <select id="race_id" name="race_id" className="app-input" value={formData.race_id} onChange={handleChange} >
              <option value="">Select a race</option>
              {races.map((race) => (
                <option key={race.race_id} value={race.race_id}>
                  {race.location} - {race.race_date}
                </option>
              ))}
            </select>

            <label className="field-label" htmlFor="p1_pick">P1</label>
            <select id="p1_pick" name="p1_pick" className="app-input" value={formData.p1_pick} onChange={handleChange}>
              <option value="">Select a driver</option>
              {drivers.map((driver) => (
                <option key={driver.driver_id} value={driver.driver_id}>
                  {driver.first_name} {driver.last_name}
                </option>
              ))}
            </select>

            <label className="field-label" htmlFor="p2_pick">P2</label>
            <select id="p2_pick" name="p2_pick" className="app-input" value={formData.p2_pick} onChange={handleChange}>
              <option value="">Select a driver</option>
              {drivers.map((driver) => (
                <option key={driver.driver_id} value={driver.driver_id}>
                  {driver.first_name} {driver.last_name}
                </option>
              ))}
            </select>

            <label className="field-label" htmlFor="p3_pick">P3</label>
            <select id="p3_pick" name="p3_pick" className="app-input" value={formData.p3_pick} onChange={handleChange}>
              <option value="">Select a driver</option>
              {drivers.map((driver) => (
                <option key={driver.driver_id} value={driver.driver_id}>
                  {driver.first_name} {driver.last_name}
                </option>
              ))}
            </select>

            <label className="checkbox-row" htmlFor="safety_car_prediction">
              <input id="safety_car_prediction" name="safety_car_prediction" type="checkbox" checked={formData.safety_car_prediction} onChange={handleChange}/>
              Safety Car
            </label>

            <button type="submit" className="primary-button full-width" disabled={loading}>
              {loading ? 'Submitting...' : 'Submit Prediction'}
            </button>
          </form>

          {error && <p className="feedback-message error">{error}</p>}
          {success && <p className="feedback-message success">{success}</p>}
        </article>

        <article className="content-card lock-card">
          <p className="section-kicker">Notes</p>
          <h3>Prediction Rules</h3>
          <p className="card-copy">
            Users can submit a race prediction by selecting drivers for P1, P2, and P3 along with a safety car prediction. 
            The form retrieves available drivers and races from the backend API and stores the prediction in the database.
            All driver selections must be different before submitting.
          </p>
        </article>
      </div>
    </section>
  )
}

export default MakePrediction
