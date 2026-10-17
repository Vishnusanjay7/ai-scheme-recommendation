import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark, Compass, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { fetchSavedSchemes, removeSavedScheme } from '../services/api'
import SchemeCard from '../components/SchemeCard'

export default function SavedSchemes() {
  const { session, isAuthenticated } = useAuth()
  const [savedSchemes, setSavedSchemes] = useState([])
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [actionMsg, setActionMsg] = useState('')

  const loadSaved = async () => {
    if (!isAuthenticated || !session?.access_token) {
      setLoading(false)
      return
    }

    setLoading(true)
    setErrorMsg('')
    try {
      const data = await fetchSavedSchemes(session.access_token)
      setSavedSchemes(Array.isArray(data) ? data : [])
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load saved schemes.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let isMounted = true

    async function initialFetch() {
      if (!isAuthenticated || !session?.access_token) {
        if (isMounted) setLoading(false)
        return
      }

      try {
        const data = await fetchSavedSchemes(session.access_token)
        if (isMounted) {
          setSavedSchemes(Array.isArray(data) ? data : [])
        }
      } catch (err) {
        if (isMounted) {
          setErrorMsg(err.message || 'Failed to load saved schemes.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    initialFetch()
    return () => {
      isMounted = false
    }
  }, [isAuthenticated, session])

  const handleRemove = async (schemeId) => {
    if (!session?.access_token) return
    try {
      await removeSavedScheme(schemeId, session.access_token)
      setSavedSchemes((prev) => prev.filter((s) => (s.scheme_id || s.id) !== schemeId))
      setActionMsg('Scheme removed from saved bookmarks.')
      setTimeout(() => setActionMsg(''), 3000)
    } catch (err) {
      setActionMsg(err.message || 'Failed to remove scheme.')
      setTimeout(() => setActionMsg(''), 3000)
    }
  }

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-3 border-slate-300 border-t-blue-700 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500">Loading your saved bookmarks...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#07172c] text-white rounded-xl p-6 sm:p-8 border border-slate-800 shadow-md space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
          <span>Citizen Bookmarks</span>
          <span className="text-slate-400">·</span>
          <span className="text-slate-300">Application Tracking</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Saved Government Schemes
        </h1>
        <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
          Review welfare programs you have bookmarked. Application deadlines and registration statuses reflect live government department schedules.
        </p>
      </div>

      {actionMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{actionMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between gap-2">
          <span>{errorMsg}</span>
          <button
            type="button"
            onClick={loadSaved}
            className="px-2.5 py-1 bg-rose-600 text-white rounded font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {savedSchemes.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-10 text-center max-w-lg mx-auto space-y-4 shadow-sm">
          <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mx-auto text-slate-600">
            <Bookmark className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">No Bookmarked Schemes Yet</h3>
            <p className="text-xs text-slate-600 leading-relaxed max-w-sm mx-auto">
              Save welfare schemes you want to review or apply for later. When you find eligible schemes, tap "Save Scheme" to track deadlines here.
            </p>
          </div>
          <Link
            to="/recommendations"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#07172c] hover:bg-slate-800 text-white font-bold rounded-xl text-xs sm:text-sm transition-colors shadow-sm"
          >
            <Compass className="w-4 h-4" />
            <span>Discover Eligible Schemes</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-600 pb-2 border-b border-slate-200">
            <span>
              Tracking <strong className="text-slate-900 font-mono tabular-nums">{savedSchemes.length}</strong> bookmarked {savedSchemes.length === 1 ? 'scheme' : 'schemes'}
            </span>
            <Link
              to="/recommendations"
              className="font-semibold text-blue-700 hover:text-blue-900 flex items-center gap-1"
            >
              <span>Find More Schemes</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {savedSchemes.map((scheme) => {
              const sId = scheme.scheme_id || scheme.id
              return (
                <SchemeCard
                  key={sId}
                  scheme={scheme}
                  isSaved={true}
                  onRemove={handleRemove}
                />
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
