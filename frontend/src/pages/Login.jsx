import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Login() {
  const location = useLocation()
  const [email, setEmail] = useState(location.state?.registeredEmail || '')
  const [password, setPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const { login, isAuthenticated, loading: authLoading } = useAuth()
  const navigate = useNavigate()

  // Safely resolve redirect path from location state
  const resolveRedirectPath = () => {
    const fromState = location.state?.from
    if (!fromState) return '/dashboard'

    let target = '/dashboard'
    if (typeof fromState === 'string') {
      target = fromState
    } else if (fromState && typeof fromState === 'object' && fromState.pathname) {
      target = `${fromState.pathname}${fromState.search || ''}${fromState.hash || ''}`
    }

    // Guard against open redirect attacks or redirecting back to auth pages
    if (
      !target.startsWith('/') ||
      target.startsWith('//') ||
      target.startsWith('/login') ||
      target.startsWith('/register')
    ) {
      return '/dashboard'
    }
    return target
  }

  const from = resolveRedirectPath()

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, authLoading, navigate, from])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (submitting) return
    setErrorMsg('')

    const trimmedEmail = email.trim()

    if (!trimmedEmail || !password) {
      setErrorMsg('Please enter both email and password.')
      return
    }

    if (!trimmedEmail.includes('@')) {
      setErrorMsg('Please enter a valid email address.')
      return
    }

    setSubmitting(true)
    try {
      await login(trimmedEmail, password)
      navigate(from, { replace: true })
    } catch (err) {
      const message = err.message || ''
      if (message.includes('Invalid login credentials')) {
        setErrorMsg('Invalid email or password. Please verify and try again.')
      } else if (message.includes('Email not confirmed')) {
        setErrorMsg('Please confirm your email address before logging in.')
      } else {
        setErrorMsg(message || 'Login failed. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (authLoading) {
    return (
      <div className="page-loading">
        <div className="spinner"></div>
        <p>Verifying citizen session...</p>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-emblem">🏛️</div>
          <h2>Citizen Login</h2>
          <p className="auth-subtitle">
            Sign in to access your scheme recommendations and profile
          </p>
        </div>

        {location.state?.message && !errorMsg && (
          <div className="alert alert-success" role="alert">
            <span className="alert-icon">✅</span>
            <span>{location.state.message}</span>
          </div>
        )}

        {errorMsg && (
          <div className="alert alert-danger" role="alert">
            <span className="alert-icon">⚠️</span>
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="form-group">
            <label htmlFor="login-email">Email Address</label>
            <input
              id="login-email"
              name="email"
              type="email"
              autoComplete="email"
              className="form-control"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={submitting}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              name="password"
              type="password"
              autoComplete="current-password"
              className="form-control"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            New citizen? <Link to="/register">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
