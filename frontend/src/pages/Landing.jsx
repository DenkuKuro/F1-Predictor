function Landing({ onNavigate }) {
  return (
    <section className="page-section">
      <article className="content-card hero-card landing-hero">
        <div>
          <p className="section-kicker">Welcome to F1 Predictor</p>
          <h3 className="hero-title">Predict the Podium. Climb the Ranks.</h3>
          <p className="hero-copy">
            F1 Predictor is a Formula 1 prediction game where you pick the top 3
            finishing drivers before each race. Earn points for correct podium calls and 
            track your standing against other players.
          </p>
          <div className="hero-actions">
            <button className="primary-button" onClick={() => onNavigate('login')}>
              Login
            </button>
            <button className="secondary-button" onClick={() => onNavigate('signup')}>
              Sign Up
            </button>
          </div>
        </div>
      </article>

      <div className="stats-grid">
        <article className="content-card landing-feature">
          <p className="section-kicker">Predict</p>
          <h3>Make Your Pick</h3>
          <p className="card-copy">
            Before each race, choose who you think will finish P1, P2, and P3.
            You can also predict whether a safety car will be deployed.
          </p>
        </article>

        <article className="content-card landing-feature">
          <p className="section-kicker">Discover</p>
          <h3>About The Race</h3>
          <p className="card-copy">
            Browse the full driver and constructor entry list for any of the 10
            most recent Grand Prix weekends.
          </p>
        </article>

        <article className="content-card landing-feature">
          <p className="section-kicker">Score</p>
          <h3>Earn Points</h3>
          <p className="card-copy">
            Correct on position on the podium earns 100pts, on the podium but
             wrong position earns 50pts, correct call on safety car earns 50 bonus points.
          </p>
        </article>

        <article className="content-card landing-feature">
          <p className="section-kicker">Compete</p>
          <h3>Global Leaderboard</h3>
          <p className="card-copy">
            See where you stand against all other players. Points accumulate across
            every race.
          </p>
        </article>
      </div>
    </section>
  )
}

export default Landing
