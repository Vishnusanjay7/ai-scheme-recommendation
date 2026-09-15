import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  checkSchemeSaved,
  fetchSchemeDetails,
  removeSavedScheme,
  saveScheme,
} from '../services/api'
import DeadlineBadge from '../components/DeadlineBadge'
import EligibilityBadge from '../components/EligibilityBadge'

export default function SchemeDetails() {
  const { id } = useParams()
  const { session, isAuthenticated } = useAuth()

  const [scheme, setScheme] = useState(null)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [isSaved, setIsSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveFeedback, setSaveFeedback] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadScheme() {
      setLoading(true)
      setErrorMsg('')
      try {
        const data = await fetchSchemeDetails(id)
        if (isMounted) setScheme(data)

        if (isAuthenticated && session?.access_token) {
          try {
            const statusRes = await checkSchemeSaved(id, session.access_token)
            if (isMounted) setIsSaved(Boolean(statusRes.saved))
          } catch {
            // Non-blocking check failure
          }
        }
      } catch (err) {
        if (isMounted) {
          setErrorMsg(err.message || 'Scheme not found or failed to load.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadScheme()
    return () => {
      isMounted = false
    }
  }, [id, isAuthenticated, session])

  const handleToggleSave = async () => {
    if (!isAuthenticated || !session?.access_token) {
      setSaveFeedback('Please login to bookmark schemes.')
      setTimeout(() => setSaveFeedback(''), 3000)
      return
    }

    setSaving(true)
    setSaveFeedback('')
    try {
      if (isSaved) {
        await removeSavedScheme(id, session.access_token)
        setIsSaved(false)
        setSaveFeedback('Removed from bookmarks')
      } else {
        await saveScheme(id, session.access_token)
        setIsSaved(true)
        setSaveFeedback('Saved to bookmarks!')
      }
    } catch (err) {
      setSaveFeedback(err.message || 'Action failed')
    } finally {
      setSaving(false)
      setTimeout(() => setSaveFeedback(''), 3000)
    }
  }

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner"></div>
        <p>Loading scheme details...</p>
      </div>
    )
  }

  if (errorMsg || !scheme) {
    return (
      <div className="details-error-page">
        <div className="alert alert-danger">
          <span>{errorMsg || 'Scheme not found.'}</span>
        </div>
        <Link to="/recommendations" className="btn btn-outline mt-3">
          ← Back to Recommendations
        </Link>
      </div>
    )
  }

  const activity = scheme.activity || {}
  const officialUrl = scheme.official_url || scheme.source_url
  const documents = scheme.documents || []

  return (
    <div className="scheme-details-page">
      <div className="details-header-card">
        <div className="breadcrumb">
          <Link to="/recommendations">Recommendations</Link> / <span>{scheme.scheme_name}</span>
        </div>

        <div className="header-badge-row">
          <span className="badge badge-gov">
            {scheme.government_level === 'CENTRAL' ? 'Central Government' : 'State Government'}
          </span>
          <EligibilityBadge status={scheme.status === 'ACTIVE' ? 'ELIGIBLE' : scheme.status} />
          <DeadlineBadge
            deadlineStatus={activity.deadline_status}
            daysRemaining={activity.days_remaining}
            activityStatus={activity.status}
          />
        </div>

        <h1 className="details-title">{scheme.scheme_name}</h1>
        {scheme.description && <p className="details-summary">{scheme.description}</p>}

        <div className="details-cta-bar">
          {officialUrl ? (
            <a
              href={officialUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary btn-lg"
            >
              Apply on Official Government Portal ↗
            </a>
          ) : (
            <span className="text-muted">Official application link not yet published</span>
          )}

          {isAuthenticated && (
            <button
              type="button"
              onClick={handleToggleSave}
              disabled={saving}
              className={`btn btn-lg ${isSaved ? 'btn-saved' : 'btn-outline-save'}`}
              title={isSaved ? 'Remove from saved schemes' : 'Save scheme to bookmarks'}
            >
              {saving ? 'Processing...' : isSaved ? 'Saved to Bookmarks ✓' : '🔖 Save Scheme'}
            </button>
          )}

          <Link to="/recommendations" className="btn btn-outline btn-lg">
            Browse Other Schemes
          </Link>
        </div>

        {saveFeedback && (
          <div className="details-feedback-pill text-sm text-accent mt-2">
            {saveFeedback}
          </div>
        )}
      </div>

      <div className="details-grid">
        {/* Left Column: Benefits & Procedures */}
        <div className="details-main">
          {/* Benefits */}
          <div className="content-card">
            <h3>🎁 Scheme Benefits</h3>
            <p className="card-body-text">
              {scheme.benefits || 'Financial assistance and welfare subsidies provided as per official guidelines.'}
            </p>
          </div>

          {/* Application Procedure */}
          <div className="content-card">
            <h3>📝 Application Procedure</h3>
            <p className="card-body-text">
              {scheme.application_procedure ||
                '1. Visit the official government scheme portal.\n2. Complete citizen registration with Aadhaar / mobile.\n3. Submit required demographic documents and bank account details for Direct Benefit Transfer (DBT).'}
            </p>
          </div>

          {/* Required Documents */}
          <div className="content-card">
            <h3>📑 Required Documents</h3>
            {documents.length > 0 ? (
              <ul className="docs-list">
                {documents.map((doc, idx) => (
                  <li key={idx}>
                    <strong>{doc.document_name}</strong>
                    {doc.is_mandatory && <span className="badge badge-urgent text-xs ml-2">Mandatory</span>}
                    {doc.description && <p className="doc-desc">{doc.description}</p>}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted">
                Standard identification documents typically required: Aadhaar Card, Resident Certificate,
                Income Certificate, Bank Passbook, and Passport Size Photograph.
              </p>
            )}
          </div>
        </div>

        {/* Right Column: Timeline & Authority Meta */}
        <div className="details-sidebar">
          <div className="meta-card">
            <h4>Application Timeline</h4>
            <div className="meta-row">
              <span className="meta-label">Activity Status:</span>
              <span className="meta-value font-bold">{activity.status || scheme.status || 'Active'}</span>
            </div>
            <div className="meta-row">
              <span className="meta-label">Start Date:</span>
              <span className="meta-value">{scheme.start_date || 'Open (Rolling Registration)'}</span>
            </div>
            <div className="meta-row">
              <span className="meta-label">Deadline (Last Date):</span>
              <span className="meta-value">
                {scheme.last_date || 'No closing deadline (Continuous Program)'}
              </span>
            </div>
            {activity.days_remaining !== null && activity.days_remaining !== undefined && (
              <div className="meta-row">
                <span className="meta-label">Days Remaining:</span>
                <span className="meta-value text-accent font-bold">
                  {activity.days_remaining >= 0 ? `${activity.days_remaining} Days` : 'Expired'}
                </span>
              </div>
            )}
            <div className="meta-row">
              <span className="meta-label">Timezone:</span>
              <span className="meta-value">Asia/Kolkata (IST)</span>
            </div>
          </div>

          <div className="meta-card">
            <h4>Authority & Source</h4>
            <div className="meta-row">
              <span className="meta-label">Government Level:</span>
              <span className="meta-value">{scheme.government_level || 'Central'}</span>
            </div>
            {scheme.source_url && (
              <div className="meta-row">
                <span className="meta-label">Official Source:</span>
                <a
                  href={scheme.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="meta-link"
                >
                  Verify Source ↗
                </a>
              </div>
            )}
            {scheme.updated_at && (
              <div className="meta-row">
                <span className="meta-label">Last Updated:</span>
                <span className="meta-value text-sm text-muted">
                  {new Date(scheme.updated_at).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>

          <div className="disclaimer-card">
            <span className="disclaimer-icon">ℹ️</span>
            <p>
              <strong>Citizen Notice:</strong> This platform evaluates eligibility deterministically
              and provides recommendations. Actual applications must be filed directly on the official
              government portal.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
