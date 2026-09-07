import { FormEvent, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { getAccessToken, signIn } from '../services/auth'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (getAccessToken()) return <Navigate to="/" replace />

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await signIn(email.trim(), password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel panel">
        <span className="eyebrow">SECURE ACCESS / <span>SUPABASE AUTH</span></span>
        <h1>Retail Vision<br /><span>Intelligence</span></h1>
        <p>Sign in with an account from the configured Supabase project to access private shelf analyses.</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            <span>Email</span>
            <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" required />
          </label>
          <label>
            <span>Password</span>
            <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" required />
          </label>
          {error && <div className="auth-error" role="alert">{error}</div>}
          <button className="primary-button" disabled={loading} type="submit">
            {loading ? 'AUTHENTICATING…' : 'SIGN IN'}
          </button>
        </form>
      </section>
    </main>
  )
}
