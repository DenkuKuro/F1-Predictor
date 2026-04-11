import { useState, useEffect } from 'react'

function LogIn({ onLogin }) {
  const [userData, setUserData] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    const saveId = localStorage.getItem("user_id");
    if (saveId) {
      setUserData(localStorage.getItem("username"));
    }
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!email.trim() || !password.trim()) {
      setError('Please enter both your email and password.')
      return
    }

    const formData = {
      email: email,
      password: password
    }

    try {
      const response = await fetch("/api/login", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        })
      const data = await response.json()
      if (response.ok) {
        const body = data.body;
        localStorage.setItem("user_id", body.user_id);
        localStorage.setItem("username", body.username);
        setSuccess(data.message);
        setUserData(body.username);
        if (onLogin) onLogin({ user_id: body.user_id, username: body.username });
      } else {
        setError(data.message)
      }
    } catch (error) {
      console.error("Error: ", error)
    }
  }

  return (
    <section className="page-section narrow-layout">
      <article className="content-card form-card">
        <p className="section-kicker">Login</p>
        { 
          userData ? (
            /* Welcome Message */
            <div className="welcome-container">
              <p className="section-kicker">Welcome back!</p>
              <h2>Hello, {userData}</h2>
            </div>
          ) : (
            <form className="app-form" onSubmit={handleSubmit}>
              <label className="field-label" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                className="app-input"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />

              <label className="field-label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                className="app-input"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />

              <button type="submit" className="primary-button full-width">
                Login
              </button>
            </form>
          )}

        {error && <p className="feedback-message error">{error}</p>}
        {success && <p className="feedback-message success">{success}</p>}
      </article>
    </section>
  )
}

export default LogIn
