import { useEffect, useState } from 'react'

function ViewUserPredictions() {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadUserPredictions = async () => {
      // 1. Retrieve the logged-in user's ID from localStorage
      const userId = localStorage.getItem("user_id");

      if (!userId) {
        setError('You must be logged in to view your predictions.');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError('');

        // 2. Inject the ID into your dynamic backend route
        const response = await fetch(`/api/user_predictions/${userId}`);

        if (!response.ok) {
          throw new Error('Could not load your predictions.');
        }

        const data = await response.json();
        
        // Supabase returns an array in response.data, which your API is returning directly
        setPredictions(Array.isArray(data) ? data : []);
      } catch (fetchError) {
        console.error("Fetch Error:", fetchError);
        setError('An error occurred while fetching your data.');
      } finally {
        setLoading(false);
      }
    }

    loadUserPredictions();
  }, []);

  return (
    <section className="page-section">
      <article className="content-card">
        <div className="card-heading">
          <div>
            <p className="section-kicker">My Profile</p>
            <h3>My Predictions</h3>
          </div>
        </div>

        {loading && <p className="card-copy">Loading your records...</p>}
        {error && <p className="feedback-message error">{error}</p>}

        {!loading && !error && predictions.length === 0 && (
          <p className="card-copy">You haven't made any predictions yet.</p>
        )}

        {!loading && predictions.length > 0 && (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Race</th>
                  <th>P1</th>
                  <th>P2</th>
                  <th>P3</th>
                  <th>Safety Car</th>
                  <th>Points</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((prediction) => (
                  <tr key={prediction.pred_id}>
                    <td>{prediction.pred_id}</td>
                    <td>{prediction.race_id}</td>
                    <td>{prediction.p1_pick}</td>
                    <td>{prediction.p2_pick}</td>
                    <td>{prediction.p3_pick}</td>
                    <td>{prediction.safety_car_prediction ? 'Yes' : 'No'}</td>
                    <td>
                      {prediction.points_earned === 0 || prediction.points_earned === null 
                        ? "Pending" 
                        : prediction.points_earned}
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

export default ViewUserPredictions;