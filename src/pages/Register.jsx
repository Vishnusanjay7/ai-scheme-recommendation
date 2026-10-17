import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Landmark, AlertCircle, CheckCircle2 } from 'lucide-react'
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
        navigate('/dashboard')
      } else {
        setSuccessMsg(
          'Account created successfully! You can now log in with your credentials.'
        )
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
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-3 border-slate-300 border-t-blue-700 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Verifying citizen session...</p>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto my-6 sm:my-10">
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-[#07172c] text-amber-400 flex items-center justify-center mx-auto shadow-sm">
            <Landmark className="w-6 h-6" />
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
            Citizen Registration
          </h1>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            Create your citizen profile to receive verified scheme recommendations tailored to your demographic eligibility.
          </p>
        </div>

        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-1">
            <label htmlFor="fullName" className="block text-xs font-semibold text-slate-700">
              Full Legal Name
            </label>
            <input
              id="fullName"
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. Ramesh Kumar"
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
              disabled={loading}
              required
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="email" className="block text-xs font-semibold text-slate-700">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.gov.in"
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
              disabled={loading}
              required
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="password" className="block text-xs font-semibold text-slate-700">
              Password (min. 6 characters)
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
              disabled={loading}
              required
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="confirmPassword" className="block text-xs font-semibold text-slate-700">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
              disabled={loading}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-[#07172c] hover:bg-slate-800 text-white rounded-lg text-xs sm:text-sm font-bold transition-colors disabled:opacity-50 shadow-sm"
          >
            {loading ? 'Creating Citizen Profile...' : 'Complete Registration'}
          </button>
        </form>

        <div className="space-y-2 pt-2 text-center text-xs text-slate-600">
          <div>
            <span>Already have an account? </span>
            <Link
              to="/login"
              state={email.trim() ? { registeredEmail: email.trim() } : undefined}
              className="font-semibold text-blue-700 hover:underline"
            >
              Sign In here
            </Link>
          </div>
          <p className="text-emerald-700">
            Want immediate testing?{' '}
            <Link to="/login" className="font-semibold underline">
              Use 1-Click Fast Persona Access
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
