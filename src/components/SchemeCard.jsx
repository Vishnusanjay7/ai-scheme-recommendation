import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark, ExternalLink, ArrowRight, ShieldCheck } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { removeSavedScheme, saveScheme } from '../services/api'
import DeadlineBadge from './DeadlineBadge'
import EligibilityBadge from './EligibilityBadge'

export default function SchemeCard({
  scheme,
  isVerificationRequired = false,
  isSaved: initialSaved = false,
  onRemove = null,
}) {
  const { session, isAuthenticated } = useAuth()
  const schemeId = scheme.scheme_id || scheme.id
  const officialUrl = scheme.official_url || scheme.source_url

  const [saved, setSaved] = useState(initialSaved)
  const [loading, setLoading] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')

  const handleToggleSave = async () => {
    if (!isAuthenticated || !session?.access_token) {
      setSaveMsg('Please login to bookmark schemes.')
      setTimeout(() => setSaveMsg(''), 3000)
      return
    }

    setLoading(true)
    setSaveMsg('')
    try {
      if (saved) {
        if (onRemove) {
          await onRemove(schemeId)
          return
        }
        await removeSavedScheme(schemeId, session.access_token)
        setSaved(false)
        setSaveMsg('Scheme removed')
      } else {
        await saveScheme(schemeId, session.access_token)
        setSaved(true)
        setSaveMsg('Saved!')
      }
    } catch (err) {
      setSaveMsg(err.message || 'Action failed')
    } finally {
      setLoading(false)
      setTimeout(() => setSaveMsg(''), 2500)
    }
  }

  return (
    <div
      className={`scheme-card bg-white border rounded-xl p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between space-y-4 ${
        isVerificationRequired
          ? 'card-verification border-amber-300 bg-amber-50/20'
          : 'border-slate-200'
      }`}
    >
      <div className="space-y-3">
        {/* Unboxed Metadata Header Bar (Zero-Pill Discipline) */}
        <div className="scheme-card-header flex items-center justify-between gap-2 text-xs">
          <div className="badge-group flex items-center gap-1.5 flex-wrap">
            <span className="badge badge-gov font-semibold text-slate-700">
              {scheme.government_level === 'CENTRAL' ? 'Central Scheme' : 'State Scheme'}
            </span>
            <span className="text-slate-300">·</span>
            {scheme.eligibility_status && (
              <>
                <EligibilityBadge
                  status={scheme.eligibility_status}
                  isVerificationRequired={isVerificationRequired}
                />
                <span className="text-slate-300">·</span>
              </>
            )}
            <DeadlineBadge
              deadlineStatus={scheme.deadline_status}
              daysRemaining={scheme.days_remaining}
              activityStatus={scheme.activity_status}
            />
          </div>

          {scheme.relevance_score !== undefined && scheme.relevance_score !== null && (
            <div
              className="relevance-pill font-mono tabular-nums text-xs font-semibold text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200 shrink-0"
              title="Indicates priority match to your profile and need, not legal eligibility"
            >
              <span className="relevance-val">{scheme.relevance_score}/100</span>
            </div>
          )}
        </div>

        {/* Title */}
        <h3 className="scheme-title text-sm sm:text-base font-bold text-slate-900 leading-snug">
          <Link
            to={`/schemes/${schemeId}`}
            className="hover:text-blue-700 transition-colors"
          >
            {scheme.scheme_name}
          </Link>
        </h3>

        {/* Relevance Reason if provided */}
        {scheme.relevance_reason && (
          <p className="scheme-reason text-xs text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100">
            <strong className="text-slate-800 font-semibold">Priority Match:</strong> {scheme.relevance_reason}
          </p>
        )}

        {/* Key Benefits */}
        {scheme.benefits && (
          <div className="scheme-benefits text-xs text-slate-600 line-clamp-2">
            <strong className="text-slate-800 font-semibold">Key Benefits: </strong>
            <span>{scheme.benefits}</span>
          </div>
        )}

        {/* Deadline & DBT Indicators */}
        <div className="flex items-center gap-2 flex-wrap text-xs pt-1">
          {scheme.last_date && (
            <div className="scheme-last-date inline-flex items-center gap-1 text-[11px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              <span>📅 Last Date: <strong>{scheme.last_date}</strong></span>
              {scheme.days_remaining !== null && scheme.days_remaining !== undefined && (
                <span className="text-blue-700 font-semibold">({scheme.days_remaining}d left)</span>
              )}
            </div>
          )}
          {scheme.dbt_enabled && (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-800 bg-emerald-50 border border-emerald-300 px-2 py-0.5 rounded" title="Direct Benefit Transfer via Aadhaar enabled">
              ⚡ Direct Bank Transfer (DBT)
            </span>
          )}
        </div>

        {/* Missing criteria notice */}
        {isVerificationRequired && scheme.missing_criteria && scheme.missing_criteria.length > 0 && (
          <div className="missing-criteria-notice text-xs p-2 bg-amber-50 border border-amber-200 rounded text-amber-900">
            <strong>Verify:</strong> {scheme.missing_criteria.join(', ')}
          </div>
        )}

        {saveMsg && (
          <div className="save-feedback-msg text-xs text-amber-600 font-semibold">
            {saveMsg}
          </div>
        )}
      </div>

      {/* Card Action Footer */}
      <div className="scheme-card-footer pt-3 border-t border-slate-100 flex items-center justify-between gap-2 text-xs">
        <div className="footer-left-actions flex items-center gap-2">
          <Link
            to={`/schemes/${schemeId}`}
            className="btn btn-outline px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 hover:text-slate-900 font-semibold transition-colors"
          >
            View Details
          </Link>
          {isAuthenticated && (
            <button
              type="button"
              onClick={handleToggleSave}
              disabled={loading}
              className={`btn btn-save inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
                saved
                  ? 'btn-saved bg-amber-50 border-amber-300 text-amber-800'
                  : 'btn-outline-save border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
              title={saved ? 'Remove from bookmarks' : 'Save scheme to review later'}
            >
              <Bookmark className="w-3.5 h-3.5" />
              <span>{loading ? '...' : onRemove ? 'Remove' : saved ? 'Saved' : 'Save'}</span>
            </button>
          )}
        </div>

        {officialUrl ? (
          <a
            href={officialUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary inline-flex items-center gap-1 px-3 py-1.5 bg-[#07172c] hover:bg-slate-800 text-white rounded-lg font-semibold transition-colors shrink-0"
            title="External government portal"
          >
            <span>Apply</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        ) : (
          <span className="text-slate-400 text-xs">Official portal offline</span>
        )}
      </div>
    </div>
  )
}
