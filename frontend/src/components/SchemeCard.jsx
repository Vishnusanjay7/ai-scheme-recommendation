import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { removeSavedScheme, saveScheme } from '../services/api'
import DeadlineBadge from './DeadlineBadge'
import EligibilityBadge from './EligibilityBadge'

/**
 * SchemeCard Component
 * Displays a single government scheme candidate with:
 *   - Government Level badge
 *   - Title
 *   - Eligibility Badge
 *   - Relevance Match Score (0–100)
 *   - Deadline Badge
 *   - Benefits Summary
 *   - Relevance Reason
 *   - Action buttons (View Details, Official Portal Link, and Bookmark Save/Remove)
 */
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
      setSaveMsg('Please login to save schemes.')
      setTimeout(() => setSaveMsg(''), 3000)
      return
    }

    setLoading(true)
    setSaveMsg('')
    try {
      if (saved) {
        // If already saved and onRemove provided, invoke callback
        if (onRemove) {
          await onRemove(schemeId)
          return
        }
        // Otherwise remove via API
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
    <div className={`scheme-card ${isVerificationRequired ? 'card-verification' : ''}`}>
      <div className="scheme-card-header">
        <div className="badge-group">
          <span className="badge badge-gov">
            {scheme.government_level === 'CENTRAL' ? 'Central Scheme' : 'State Scheme'}
          </span>
          {scheme.eligibility_status && (
            <EligibilityBadge
              status={scheme.eligibility_status}
              isVerificationRequired={isVerificationRequired}
            />
          )}
          <DeadlineBadge
            deadlineStatus={scheme.deadline_status}
            daysRemaining={scheme.days_remaining}
            activityStatus={scheme.activity_status}
          />
        </div>

        {scheme.relevance_score !== undefined && scheme.relevance_score !== null && (
          <div className="relevance-pill" title="Indicates priority match to your profile and need, not legal eligibility">
            <span className="relevance-label">Relevance Match:</span>
            <span className="relevance-val">{scheme.relevance_score}/100</span>
          </div>
        )}
      </div>

      <h3 className="scheme-title">
        <Link to={`/schemes/${schemeId}`}>{scheme.scheme_name}</Link>
      </h3>

      {scheme.relevance_reason && (
        <p className="scheme-reason">
          <strong>Why recommended:</strong> {scheme.relevance_reason}
        </p>
      )}

      {scheme.benefits && (
        <div className="scheme-benefits">
          <strong>Key Benefits:</strong>
          <p>{scheme.benefits}</p>
        </div>
      )}

      {scheme.last_date && (
        <div className="scheme-last-date text-sm text-muted">
          <span>📅 Application Deadline: <strong>{scheme.last_date}</strong></span>
        </div>
      )}

      {isVerificationRequired && scheme.missing_criteria && scheme.missing_criteria.length > 0 && (
        <div className="missing-criteria-notice">
          <strong>Please verify:</strong> {scheme.missing_criteria.join(', ')}
        </div>
      )}

      {saveMsg && (
        <div className="save-feedback-msg text-xs text-accent">
          {saveMsg}
        </div>
      )}

      <div className="scheme-card-footer">
        <div className="footer-left-actions">
          <Link to={`/schemes/${schemeId}`} className="btn btn-outline">
            View Details
          </Link>
          {isAuthenticated && (
            <button
              type="button"
              onClick={handleToggleSave}
              disabled={loading}
              className={`btn btn-save ${saved ? 'btn-saved' : 'btn-outline-save'}`}
              title={saved ? 'Remove from bookmarks' : 'Save scheme to review later'}
            >
              {loading ? '...' : onRemove ? '🗑️ Remove' : saved ? 'Saved ✓' : '🔖 Save Scheme'}
            </button>
          )}
        </div>

        {officialUrl ? (
          <a
            href={officialUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary"
            title="External government portal"
          >
            Apply Officially ↗
          </a>
        ) : (
          <span className="text-muted text-sm">Official link not listed</span>
        )}
      </div>
    </div>
  )
}

