import { useState } from 'react'

function SignIn() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!email.trim() || !password.trim()) {
      setError('Please enter both your email and password.')
      return
    }

    const formData = {
        username: username,
        email: email,
        password: password
    }
    try {

        const response = await fetch("/api/sign-in", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        })
        const data = await response.json()
        if (response.ok) {
            setSuccess(data.message)
        } else {
            setError(data.message)
        }
    } catch (error) {
        console.error("Error sending data:", error)
    }

  }

  return (
    <section className="page-section narrow-layout">
      <article className="content-card form-card">
        <p className="section-kicker">Sign In</p>

        <form className="app-form" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="username">
            Username
          </label>
          <input 
            id="username"
            type='text'
            className="app-input"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />

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
            Sign In
          </button>
        </form>

        {error && <p className="feedback-message error">{error}</p>}
        {success && <p className="feedback-message success">{success}</p>}
      </article>
    </section>
  )
}

export default SignIn
