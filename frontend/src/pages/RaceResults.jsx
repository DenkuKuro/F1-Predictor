import { useState, useEffect } from 'react'

const RaceResults = ({ selectedRace }) => {
    const [simData, setSimData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // RESET logic: If the selectedRace prop changes from the sidebar, 
    // we clear the old simulation data so the button reappears.
    useEffect(() => {
        setSimData(null);
        setError('');
    }, [selectedRace]);

    const fetchSimulatedResults = async () => {
        const userId = localStorage.getItem("user_id");
        const raceData = JSON.parse(localStorage.getItem("raceSelected"));
        
        if (!userId || !raceData || !raceData.race_id) {
            setError('Please select a race and ensure you are logged in.');
            return;
        }

        setLoading(true);
        setError('');
        
        try {
            const response = await fetch(`/api/race_results?id=${userId}&race=${raceData.race_id}`);
            if (!response.ok) throw new Error('Failed to fetch race results data');
            
            const data = await response.json();
            setSimData({ ...data, metadata: raceData });
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
                        <p className='section-kicker'>Race Results</p>
                        <h3>Race & Prediction Results</h3>
                    </div>
                </div>

                {/* MODIFIED: The button only renders if simData is null */}
                {!simData && (
                    <button 
                        className="primary-button" 
                        onClick={fetchSimulatedResults}
                        disabled={loading}
                    >
                        {loading ? 'Simulating Race...' : 'View Race Results'}
                    </button>
                )}

                {error && <p className="feedback-message error" style={{marginTop: '1rem'}}>{error}</p>}

                {simData && (
                    <div style={{ marginTop: '2.5rem' }}>
                        
                        {/* 0. Race Metadata Header */}
                        <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid #333', paddingBottom: '1rem' }}>
                            <h2 style={{ margin: 0, color: '#fff' }}>{simData.metadata.name}</h2>
                            <p style={{ margin: '5px 0', color: '#888', fontSize: '0.9rem' }}>
                                📍 {simData.metadata.location} | 🗓️ {simData.metadata.season} Season ({simData.metadata.date})
                            </p>
                        </div>

                        {/* 1. Official Podium Section */}
                        <div className="results-summary" style={{ marginBottom: '2rem', padding: '1.25rem', background: '#1f2123', borderLeft: '4px solid #e10600', borderRadius: '8px' }}>
                            <h4 style={{ color: '#e10600', marginBottom: '1rem', textTransform: 'uppercase', fontSize: '0.85rem' }}>🏁 Official Podium</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '15px' }}>
                                <div><small style={{color: '#888'}}>P1</small><br/><strong>{simData.actual_race.p1}</strong></div>
                                <div><small style={{color: '#888'}}>P2</small><br/><strong>{simData.actual_race.p2}</strong></div>
                                <div><small style={{color: '#888'}}>P3</small><br/><strong>{simData.actual_race.p3}</strong></div>
                                <div><small style={{color: '#888'}}>SAFETY CAR</small><br/><strong>{simData.actual_race.safety_car ? 'Yes' : 'No'}</strong></div>
                            </div>
                        </div>

                        {/* 2. Your Specific Prediction Results */}
                        <div className="user-highlight" style={{ marginBottom: '2.5rem', padding: '1.5rem', background: 'rgba(225, 6, 0, 0.05)', border: '1px solid #e10600', borderRadius: '8px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                <h4 style={{ margin: 0, fontSize: '1.1rem' }}>⭐ Your Results: {simData.user_simulation.username}</h4>
                                <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#e10600' }}>{simData.user_simulation.score} pts</span>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '10px', fontSize: '0.9rem' }}>
                                <p style={{margin:0}}><small style={{color:'#888'}}>P1:</small> {simData.user_simulation.prediction.p1}</p>
                                <p style={{margin:0}}><small style={{color:'#888'}}>P2:</small> {simData.user_simulation.prediction.p2}</p>
                                <p style={{margin:0}}><small style={{color:'#888'}}>P3:</small> {simData.user_simulation.prediction.p3}</p>
                                <p style={{margin:0}}><small style={{color:'#888'}}>SC:</small> {simData.user_simulation.prediction.safety_car ? 'Yes' : 'No'}</p>
                            </div>
                        </div>

                        {/* 3. The Full Leaderboard */}
                        <h4 style={{ marginBottom: '1rem' }}>👥 Full Leaderboard</h4>
                        <div className="table-wrapper">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Rank</th>
                                        <th>User</th>
                                        <th>P1 Pick</th>
                                        <th>P2 Pick</th>
                                        <th>P3 Pick</th>
                                        <th>Score</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {simData.leaderboard.map((user, index) => {
                                        const isCurrentUser = user.username === simData.user_simulation.username;
                                        return (
                                            <tr key={index} style={isCurrentUser ? { background: 'rgba(225, 6, 0, 0.12)', borderLeft: '2px solid #e10600' } : {}}>
                                                <td>#{index + 1}</td>
                                                <td style={{ fontWeight: isCurrentUser ? 'bold' : 'normal' }}>
                                                    {user.username} {isCurrentUser && <span style={{fontSize: '0.65rem', verticalAlign: 'middle', background: '#e10600', color: '#fff', padding: '2px 4px', borderRadius: '3px', marginLeft: '5px'}}>YOU</span>}
                                                </td>
                                                <td>{user.prediction.p1}</td>
                                                <td>{user.prediction.p2}</td>
                                                <td>{user.prediction.p3}</td>
                                                <td style={{ fontWeight: 'bold', color: '#e10600' }}>{user.score}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </article>
        </section>
    );
}

export default RaceResults;