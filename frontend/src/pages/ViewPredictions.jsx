import { useEffect, useState } from 'react'

function ViewPredictions() {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadPredictions = async () => {
      try {
        setLoading(true)
        setError('')
        const response = await fetch('/api/predictions')

        if (!response.ok) {
          throw new Error('Could not load predictions.')
        }

        const data = await response.json()
        setPredictions(Array.isArray(data) ? data : [])
      } catch (fetchError) {
        setPredictions([])
        setError('Could not load predictions.')
      } finally {
        setLoading(false)
      }
    }

    loadPredictions()
  }, [])

  return (
    <section className="page-section">
      <article className="content-card">
        <div className="card-heading">
          <div>
            <p className="section-kicker">View Predictions</p>
            <h3>Prediction records</h3>
          </div>
        </div>

        {loading && <p className="card-copy">Loading predictions...</p>}
        {error && <p className="feedback-message error">{error}</p>}

        {!loading && predictions.length === 0 && <p className="card-copy">No data available yet.</p>}

        {!loading && predictions.length > 0 && (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Prediction ID</th>
                  <th>User</th>
                  <th>Race</th>
                  <th>P1</th>
                  <th>P2</th>
                  <th>P3</th>
                  <th>Safety Car</th>
                  <th>Points Earned</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((prediction) => (
                  <tr key={prediction.pred_id}>
                    <td>{prediction.pred_id}</td>
                    <td>{prediction.user_id}</td>
                    <td>{prediction.race_id}</td>
                    <td>{prediction.p1_pick}</td>
                    <td>{prediction.p2_pick}</td>
                    <td>{prediction.p3_pick}</td>
                    <td>{prediction.safety_car_prediction ? 'Yes' : 'No'}</td>
                    <td>
                      {prediction.points_earned === 0 ? "Pending" : prediction.points_earned}
                    </td>
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

export default ViewPredictions
