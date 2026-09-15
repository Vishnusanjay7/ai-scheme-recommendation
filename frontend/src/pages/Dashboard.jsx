import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { fetchActiveSchemes, fetchProfile, fetchUnreadNotifications } from '../services/api'
import SchemeCard from '../components/SchemeCard'

export default function Dashboard() {
  const { user, token } = useAuth()
  const navigate = useNavigate()

  const [profile, setProfile] = useState(null)
  const [activeSchemes, setActiveSchemes] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadDashboardData() {
      setLoading(true)
      setErrorMsg('')
      try {
        // 1. Fetch user profile
        let profData = null
        if (token) {
          try {
            profData = await fetchProfile(token)
            if (isMounted) setProfile(profData)
          } catch (err) {
            console.warn('Profile not yet populated or error:', err.message)
          }

          try {
            const notifResp = await fetchUnreadNotifications(token)
            if (isMounted && notifResp.unread_count !== undefined) {
              setUnreadCount(notifResp.unread_count)
            }
          } catch {
            // Non-blocking
          }
        }

        // 2. Fetch active schemes
        try {
          const schemesResp = await fetchActiveSchemes(6, 0)
          if (isMounted) {
            setActiveSchemes(schemesResp.data || [])
          }
        } catch (err) {
          console.warn('Schemes fetch issue:', err.message)
          if (isMounted) setActiveSchemes([])
        }
      } catch {
        if (isMounted) setErrorMsg('Could not load dashboard data. Please try again.')
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadDashboardData()
    return () => {
      isMounted = false
    }
  }, [token])

  const userName =
    profile?.full_name ||
    user?.user_metadata?.full_name ||
    user?.email?.split('@')[0] ||
    'Citizen'

  return (
    <div className="dashboard-page">
      {/* Hero Welcome Banner */}
      <section className="dashboard-hero">
        <div className="hero-content">
          <div className="hero-tag">National Welfare Portal</div>
          <h1>Find Government Schemes You May Be Eligible For</h1>
          <p className="hero-desc">
            Welcome, <strong>{userName}</strong>. Our system deterministically checks legal
            qualification rules and uses AI to recommend welfare programs tailored to your profile.
          </p>

          <div className="hero-actions">
            <button
              type="button"
              className="btn btn-primary btn-lg"
              onClick={() => navigate('/recommendations')}
            >
              Find My Schemes 🔍
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-lg"
              onClick={() => navigate('/profile')}
            >
              Update Profile 👤
            </button>
          </div>
        </div>

        {/* Profile Status Card */}
        <div className="profile-summary-card">
          <div className="card-header-compact">
            <h3>Citizen Profile Status</h3>
            <span
              className={`status-pill ${
                profile?.profile_complete ? 'pill-complete' : 'pill-incomplete'
              }`}
            >
              {profile?.profile_complete ? 'Profile Complete' : 'Profile Incomplete'}
            </span>
          </div>

          <div className="profile-details-grid">
            <div className="detail-item">
              <span className="detail-label">Resident State:</span>
              <span className="detail-value">
                {profile?.state_name || (
                  <span className="text-warning">Not selected (Defaulting Pan-India)</span>
                )}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">District:</span>
              <span className="detail-value">
                {profile?.district_name || <span className="text-muted">Not specified</span>}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Occupation:</span>
              <span className="detail-value">
                {profile?.occupation || <span className="text-muted">Not specified</span>}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Social Category:</span>
              <span className="detail-value">
                {profile?.category || <span className="text-muted">Not specified</span>}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Notifications:</span>
              <span className="detail-value">
                <Link to="/notifications" className="notif-link">
                  {unreadCount > 0 ? (
                    <span className="badge badge-urgent text-xs">{unreadCount} unread</span>
                  ) : (
                    <span className="text-muted text-xs">No new notifications</span>
                  )}
                </Link>
              </span>
            </div>
          </div>

          {!profile?.profile_complete && (
            <div className="profile-prompt">
              <p>
                ⚠️ Complete your demographic profile (income, occupation, state) to receive accurate,
                verified recommendations.
              </p>
              <Link to="/profile" className="btn btn-sm btn-outline">
                Complete Profile Now →
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* How It Works Explainer */}
      <section className="dashboard-section how-it-works">
        <h2>How Scheme Recommendations Work</h2>
        <div className="steps-grid">
          <div className="step-card">
            <div className="step-num">1</div>
            <h4>Demographic Profile</h4>
            <p>Your age, resident state, occupation, income, and category are kept confidential.</p>
          </div>
          <div className="step-card">
            <div className="step-num">2</div>
            <h4>Deterministic Eligibility</h4>
            <p>Our rule engine verifies statutory criteria. AI never decides or alters legal eligibility.</p>
          </div>
          <div className="step-card">
            <div className="step-num">3</div>
            <h4>Active Deadline Filtering</h4>
            <p>Only schemes currently open and accepting applications (in IST) are recommended.</p>
          </div>
          <div className="step-card">
            <div className="step-num">4</div>
            <h4>AI Relevance Ranking</h4>
            <p>Eligible programs are scored (0–100) based on your stated needs and priority.</p>
          </div>
        </div>
      </section>

      {/* Currently Open Government Schemes */}
      <section className="dashboard-section">
        <div className="section-header">
          <div>
            <h2>Featured Active Welfare Schemes</h2>
            <p className="section-sub">Programs currently accepting applications across India</p>
          </div>
          <Link to="/recommendations" className="btn btn-outline">
            View All Recommendations →
          </Link>
        </div>

        {loading ? (
          <div className="section-loading">
            <div className="spinner"></div>
            <p>Checking active government schemes...</p>
          </div>
        ) : errorMsg ? (
          <div className="alert alert-danger">
            <span>{errorMsg}</span>
          </div>
        ) : activeSchemes.length === 0 ? (
          <div className="empty-state-box">
            <div className="empty-state-icon">🏛️</div>
            <h3>No Active Schemes Currently Loaded</h3>
            <p className="empty-state-text">
              No government schemes are currently available in the connected scheme database.
              The official-source acquisition pipeline is ready, but no live scheme records are
              currently loaded.
            </p>
            <p className="text-muted text-sm">
              Note: Database schema and pipelines are intact. Records will appear once official source
              synchronization is initiated.
            </p>
          </div>
        ) : (
          <div className="schemes-grid">
            {activeSchemes.map((scheme) => (
              <SchemeCard key={scheme.id} scheme={scheme} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
