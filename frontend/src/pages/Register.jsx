import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Register() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [loading, setLoading] = useState(false)

  const { register, isAuthenticated, loading: authLoading } = useAuth()
  const navigate = useNavigate()

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, authLoading, navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (loading) return
    setErrorMsg('')
    setSuccessMsg('')

    const trimmedName = fullName.trim()
    const trimmedEmail = email.trim()

    // Client-side validations
    if (!trimmedName) {
      setErrorMsg('Please enter your full name.')
      return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!trimmedEmail || !emailRegex.test(trimmedEmail)) {
      setErrorMsg('Please enter a valid email address.')
      return
    }

    if (password.length < 6) {
      setErrorMsg('Password must be at least 6 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setErrorMsg('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      const data = await register(trimmedEmail, password, trimmedName)
      if (data?.session) {
        // Instant login
        navigate('/dashboard')
      } else {
        setSuccessMsg(
          'Account created successfully! You can now log in with your credentials.'
        )
        // Clear passwords for security
        setPassword('')
        setConfirmPassword('')
      }
    } catch (err) {
      const message = err.message || ''
      if (message.includes('User already registered')) {
        setErrorMsg('An account with this email already exists. Please sign in instead.')
      } else if (message.toLowerCase().includes('rate limit')) {
        setErrorMsg('Too many registration attempts. Please wait a moment and try again.')
      } else {
        setErrorMsg(message || 'Failed to complete registration. Please try again.')
      }
    } finally {
      setLoading(false)
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
          <div className="auth-emblem">🇮🇳</div>
          <h2>Citizen Registration</h2>
          <p className="auth-subtitle">
            Create an account to discover verified welfare schemes tailored to you
          </p>
        </div>

        {errorMsg && (
          <div className="alert alert-danger" role="alert">
            <span className="alert-icon">⚠️</span>
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="alert alert-success" role="alert">
            <span className="alert-icon">✅</span>
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="form-group">
            <label htmlFor="fullName">Full Name</label>
            <input
              id="fullName"
              name="fullName"
              type="text"
              autoComplete="name"
              className="form-control"
              placeholder="e.g. Ramesh Kumar"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              className="form-control"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password (minimum 6 characters)</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              className="form-control"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              className="form-control"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link
              to="/login"
              state={
                email.trim()
                  ? { registeredEmail: email.trim() }
                  : undefined
              }
            >
              Login here
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
