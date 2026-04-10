import { useState } from 'react'

const RaceResults = () => {
    // We update the state to hold an object rather than just an array
    const [simData, setSimData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchSimulatedResults = async () => {
        const userId = localStorage.getItem("user_id");
        
        if (!userId) {
            setError('Please log in first to run the simulation.');
            return;
        }

        setLoading(true);
        setError('');
        
        try {
            // Passing the current user ID as a query parameter
            const response = await fetch(`/api/race_results?id=${userId}`);
            
            if (!response.ok) {
                throw new Error('Failed to race results data');
            }
            
            const data = await response.json();
            setSimData(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <section className='page-section'>
            <article className='content-card'>
                <div className='card-heading'>
                    <div>
                        <p className='section-kicker'>StormForge Simulation</p>
                        <h3>Race & Prediction Results</h3>
                    </div>
                </div>

                <button 
                    className="primary-button" 
                    onClick={fetchSimulatedResults}
                    disabled={loading}
                >
                    {loading ? 'Simulating Race...' : 'View Race Results'}
                </button>

                {error && <p className="feedback-message error" style={{marginTop: '1rem'}}>{error}</p>}

                {simData && (
                    <div style={{ marginTop: '2.5rem' }}>
                        
                        {/* 1. Actual Race Results Section */}
                        <div className="results-summary" style={{ marginBottom: '2rem', padding: '1rem', background: '#f9f9f9', borderRadius: '8px' }}>
                            <h4 style={{ color: '#e10600', marginBottom: '1rem' }}>🏁 Official Race Results</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
                                <div><strong>P1:</strong> {simData.actual_race.p1}</div>
                                <div><strong>P2:</strong> {simData.actual_race.p2}</div>
                                <div><strong>P3:</strong> {simData.actual_race.p3}</div>
                                <div><strong>Safety Car:</strong> {simData.actual_race.safety_car ? 'Yes' : 'No'}</div>
                            </div>
                        </div>

                        {/* 2. Other Users Leaderboard Section */}
                        <h4 style={{ marginBottom: '1rem' }}>👥 Other Users' Scores</h4>
                        <div className="table-wrapper">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Rank</th>
                                        <th>User</th>
                                        <th>P1 Pick</th>
                                        <th>P2 Pick</th>
                                        <th>P3 Pick</th>
                                        <th>SC Pred.</th>
                                        <th>Total Score</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {simData.leaderboard.map((user, index) => (
                                        <tr key={index}>
                                            <td>#{index + 1}</td>
                                            <td><strong>{user.username}</strong></td>
                                            <td>{user.prediction.p1}</td>
                                            <td>{user.prediction.p2}</td>
                                            <td>{user.prediction.p3}</td>
                                            <td>{user.prediction.safety_car ? 'Yes' : 'No'}</td>
                                            <td style={{ fontWeight: 'bold', color: '#e10600' }}>{user.score} pts</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {!simData && !loading && (
                    <p className="card-copy" style={{marginTop: '1rem'}}>
                        Click the button to generate a random race and see how other users performed!
                    </p>
                )}
            </article>
        </section>
    );
}

export default RaceResults;