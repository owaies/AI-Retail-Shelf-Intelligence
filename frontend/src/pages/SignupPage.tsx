import { FormEvent, useState } from 'react'
import { Navigate, Link, useNavigate } from 'react-router-dom'
import { getAccessToken, signUp } from '../services/auth'

export function SignupPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  if (getAccessToken()) return <Navigate to="/" replace />

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMessage('')
    if (password.length < 6) {
      setError('Password must contain at least 6 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      const result = await signUp(email.trim(), password)
      if (result.confirmationRequired) {
        setMessage('Account created. Check your email to confirm your account, then sign in.')
      } else {
        navigate('/', { replace: true })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel panel">
        <span className="eyebrow">NEW WORKSPACE / <span>PRIVATE BY ACCOUNT</span></span>
        <h1>Create your<br /><span>Retail Workspace</span></h1>
        <p>Create an account to keep your analyses, history and analytics isolated from every other user.</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            <span>Email</span>
            <input value={email} onChange={event => setEmail(event.target.value)} type="email" autoComplete="email" required />
          </label>
          <label>
            <span>Password</span>
            <input value={password} onChange={event => setPassword(event.target.value)} type="password" autoComplete="new-password" minLength={6} required />
          </label>
          <label>
            <span>Confirm password</span>
            <input value={confirm} onChange={event => setConfirm(event.target.value)} type="password" autoComplete="new-password" minLength={6} required />
          </label>
          {error && <div className="auth-error" role="alert">{error}</div>}
          {message && <div className="auth-success" role="status">{message}</div>}
          <button className="primary-button" disabled={loading} type="submit">
            {loading ? 'CREATING WORKSPACE…' : 'CREATE ACCOUNT'}
          </button>
        </form>
        <p className="auth-switch">Already have an account? <Link to="/login">SIGN IN</Link></p>
      </section>
    </main>
  )
}
