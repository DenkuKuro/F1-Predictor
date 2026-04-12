import { useEffect, useState } from 'react'

function ViewPredictions({ currentUser }) {
  const [summary, setSummary] = useState(null)
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  const userId = currentUser?.user_id || localStorage.getItem('user_id')

  const loadPredictions = async () => {
    if (!userId) {
      setError('You must be logged in to view predictions.')
      setLoading(false)
      return
    }
    try {
      setLoading(true)
      setError('')
      const response = await fetch(`/api/predictions/grouped?user_id=${userId}`)
      if (!response.ok) throw new Error('Could not load predictions.')
      const data = await response.json()
      if (Array.isArray(data) && data.length > 0) {
        setSummary(data[0])
        setPredictions(data[0].predictions || [])
      } else {
        setSummary(null)
        setPredictions([])
      }
    } catch {
      setError('Could not load predictions.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadPredictions() }, [])

  const handleDelete = async (predId) => {
    setDeletingId(predId)
    try {
      const response = await fetch(`/api/predictions/${predId}`, { method: 'DELETE' })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Could not delete prediction.')
      setPredictions(prev => prev.filter(p => p.pred_id !== predId))
      setSummary(prev => prev ? { ...prev, prediction_count: prev.prediction_count - 1 } : prev)
    } catch (err) {
      setError(err.message || 'Could not delete prediction.')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <section className="page-section">
      <article className="content-card">
        <div className="card-heading">
          <div>
            <p className="section-kicker">My Predictions</p>
            <h3>{currentUser?.username || 'Your'} Predictions</h3>
          </div>
          {summary && (
            <div className="group-stats">
              <span>{summary.prediction_count} prediction{summary.prediction_count !== 1 ? 's' : ''}</span>
              <span>{summary.total_earned} pts earned</span>
              {summary.avg_points !== null && (
                <span>avg {summary.avg_points} pts</span>
              )}
            </div>
          )}
        </div>

        {loading && <p className="card-copy">Loading predictions...</p>}
        {error && <p className="feedback-message error">{error}</p>}

        {!loading && !error && predictions.length === 0 && (
          <p className="card-copy">You haven't made any predictions yet.</p>
        )}

        {!loading && predictions.length > 0 && (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Race</th>
                  <th>P1</th>
                  <th>P2</th>
                  <th>P3</th>
                  <th>Safety Car</th>
                  <th>Points</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((prediction) => (
                  <tr key={prediction.pred_id}>
                    <td>{prediction.race_name}</td>
                    <td>{prediction.p1_pick}</td>
                    <td>{prediction.p2_pick}</td>
                    <td>{prediction.p3_pick}</td>
                    <td>{prediction.safety_car_prediction ? 'Yes' : 'No'}</td>
                    <td>{prediction.points_earned === -1 ? 'Pending' : prediction.points_earned}</td>
                    <td>
                      <button
                        className="delete-btn"
                        onClick={() => handleDelete(prediction.pred_id)}
                        disabled={deletingId === prediction.pred_id}
                        title="Delete prediction"
                      >
                        {deletingId === prediction.pred_id ? '…' : '✕'}
                      </button>
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
