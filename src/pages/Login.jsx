import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Landmark, AlertCircle, CheckCircle2 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function Login() {
  const location = useLocation()
  const [email, setEmail] = useState(location.state?.registeredEmail || '')
  const [password, setPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const { login, isAuthenticated, loading: authLoading } = useAuth()
  const navigate = useNavigate()

  const resolveRedirectPath = () => {
    const fromState = location.state?.from
    if (!fromState) return '/dashboard'

    let target = '/dashboard'
    if (typeof fromState === 'string') {
      target = fromState
    } else if (fromState && typeof fromState === 'object' && fromState.pathname) {
      target = `${fromState.pathname}${fromState.search || ''}${fromState.hash || ''}`
    }

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
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-3 border-slate-300 border-t-blue-700 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Verifying citizen session...</p>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto my-6 sm:my-10">
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
        {/* Header Lockup */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-[#07172c] text-amber-400 flex items-center justify-center mx-auto shadow-sm">
            <Landmark className="w-6 h-6" />
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
            Citizen Portal Login
          </h1>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            Access personalized welfare recommendations, DBT eligibility tracking, and save bookmarks.
          </p>
        </div>

        {location.state?.message && !errorMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{location.state.message}</span>
          </div>
        )}

        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Email & Password Form */}
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-1">
            <label htmlFor="login-email" className="block text-xs font-semibold text-slate-700">
              Email Address
            </label>
            <input
              id="login-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="citizen@example.gov.in"
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
              disabled={submitting}
              required
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="login-password" className="block text-xs font-semibold text-slate-700">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
              disabled={submitting}
              required
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 px-4 bg-[#07172c] hover:bg-slate-800 text-white rounded-lg text-xs sm:text-sm font-bold transition-colors disabled:opacity-50 shadow-sm"
          >
            {submitting ? 'Authenticating...' : 'Sign In as Citizen'}
          </button>
        </form>

        <div className="pt-2 text-center text-xs text-slate-600">
          <span>New citizen applicant? </span>
          <Link to="/register" className="font-semibold text-blue-700 hover:underline">
            Register your profile
          </Link>
        </div>
      </div>
    </div>
  )
}
