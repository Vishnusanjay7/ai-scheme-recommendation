import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { fetchRecommendations } from '../services/api'
import SchemeCard from '../components/SchemeCard'

export default function Recommendations() {
  const { token } = useAuth()

  const [query, setQuery] = useState('')
  const [recommendations, setRecommendations] = useState([])
  const [verificationRequired, setVerificationRequired] = useState([])
  const [rankingMethod, setRankingMethod] = useState('DETERMINISTIC_FALLBACK')
  const [totalCandidates, setTotalCandidates] = useState(0)

  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const executeSearch = async (searchQuery = null) => {
    setErrorMsg('')
    setSearching(true)

    try {
      const data = await fetchRecommendations(searchQuery, token, 50, 0)
      setRecommendations(data.recommendations || [])
      setVerificationRequired(data.verification_required || [])
      setRankingMethod(data.ranking_method || 'DETERMINISTIC_FALLBACK')
      setTotalCandidates(data.total_candidates || 0)
    } catch (err) {
      setErrorMsg(err.message || 'Failed to retrieve recommendations. Please check your network and try again.')
      setRecommendations([])
      setVerificationRequired([])
    } finally {
      setSearching(false)
    }
  }

  // Load initial recommendations on mount or when token updates
  useEffect(() => {
    let ignore = false

    async function fetchInitialRecommendations() {
      try {
        const data = await fetchRecommendations(null, token, 50, 0)
        if (!ignore) {
          setRecommendations(data.recommendations || [])
          setVerificationRequired(data.verification_required || [])
          setRankingMethod(data.ranking_method || 'DETERMINISTIC_FALLBACK')
          setTotalCandidates(data.total_candidates || 0)
          setLoading(false)
        }
      } catch (err) {
        if (!ignore) {
          setErrorMsg(err.message || 'Failed to retrieve recommendations. Please check your network and try again.')
          setRecommendations([])
          setVerificationRequired([])
          setLoading(false)
        }
      }
    }

    fetchInitialRecommendations()
    return () => {
      ignore = true
    }
  }, [token])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    executeSearch(query.trim() || null)
  }

  const handleClearSearch = () => {
    setQuery('')
    executeSearch(null)
  }

  return (
    <div className="recommendations-page">
      <div className="page-header-rec">
        <div className="header-tag">Personalized AI Evaluation</div>
        <h1>Your Government Scheme Recommendations</h1>
        <p className="header-sub">
          Every scheme in your primary recommendation list is verified <strong>Eligible</strong> and{' '}
          <strong>Active</strong>. AI scores match priority based on your demographic profile and
          expressed needs.
        </p>

        {/* Natural Language Query Search Form */}
        <form onSubmit={handleSearchSubmit} className="query-search-form">
          <div className="search-input-wrap">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="form-control query-input"
              placeholder="Tell us what you need, e.g. 'farmer looking for equipment subsidy' or 'scholarship for college'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={searching}
            />
            {query && (
              <button
                type="button"
                className="clear-btn"
                onClick={handleClearSearch}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>
          <button type="submit" className="btn btn-primary" disabled={searching}>
            {searching ? 'Scoring...' : 'Filter Recommendations'}
          </button>
        </form>

        <div className="query-pills">
          <span className="pill-hint">Quick prompts:</span>
          <button
            type="button"
            className="btn-pill"
            onClick={() => {
              setQuery('Farmer crop loan and subsidy assistance')
              loadRecommendations('Farmer crop loan and subsidy assistance')
            }}
          >
            🌾 Farmer Support
          </button>
          <button
            type="button"
            className="btn-pill"
            onClick={() => {
              setQuery('Higher education scholarship grant')
              loadRecommendations('Higher education scholarship grant')
            }}
          >
            🎓 Education & Scholarship
          </button>
          <button
            type="button"
            className="btn-pill"
            onClick={() => {
              setQuery('Housing construction assistance')
              loadRecommendations('Housing construction assistance')
            }}
          >
            🏠 Housing & Shelter
          </button>
          <button
            type="button"
            className="btn-pill"
            onClick={() => {
              setQuery('Business loan for self-employed')
              loadRecommendations('Business loan for self-employed')
            }}
          >
            💼 MSME / Business
          </button>
        </div>
      </div>

      {/* Meta Bar */}
      {!loading && !errorMsg && (
        <div className="rec-meta-bar">
          <div className="meta-left">
            <span className="meta-badge">
              <strong>{recommendations.length}</strong> Recommended Eligible Schemes
            </span>
            <span className="meta-badge text-muted" title="Total public schemes evaluated against your profile">
              <strong>{totalCandidates}</strong> Evaluated
            </span>
            {verificationRequired.length > 0 && (
              <span className="meta-badge badge-warning-subtle">
                <strong>{verificationRequired.length}</strong> Needs Profile Verification
              </span>
            )}
          </div>
          <div className="meta-right">
            <span className="ranking-badge" title="Algorithm used for relevance score ordering">
              Ranking Engine: {rankingMethod === 'OPENAI' ? '🤖 OpenAI LLM' : '⚙️ Deterministic Multi-Factor'}
            </span>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="alert alert-danger" role="alert">
          <span className="alert-icon">⚠️</span>
          <span>{errorMsg}</span>
          <button
            type="button"
            className="btn btn-sm btn-outline ml-auto"
            onClick={() => loadRecommendations(query || null)}
          >
            Retry ↻
          </button>
        </div>
      )}

      {loading ? (
        <div className="page-loading">
          <div className="spinner"></div>
          <p>Evaluating legal eligibility and scoring schemes...</p>
        </div>
      ) : recommendations.length === 0 && verificationRequired.length === 0 ? (
        <div className="empty-state-card">
          <div className="empty-icon">🏛️</div>
          <h3>No Government Schemes Available</h3>
          <p className="empty-desc">
            No government schemes are currently available in the connected scheme database.
            The official-source acquisition pipeline is ready, but no live scheme records are
            currently loaded.
          </p>
          <p className="empty-hint text-muted">
            Tip: Make sure your <Link to="/profile">Profile</Link> is filled out so when live schemes
            are synchronized, your verified recommendations appear automatically.
          </p>
        </div>
      ) : (
        <>
          {/* Main Eligible Recommendations */}
          <div className="schemes-grid">
            {recommendations.map((scheme) => (
              <SchemeCard key={scheme.scheme_id} scheme={scheme} />
            ))}
          </div>

          {/* Verification Required Section (Separated) */}
          {verificationRequired.length > 0 && (
            <div className="verification-section">
              <div className="verification-header">
                <h3>⚠️ Schemes Requiring Demographic Verification</h3>
                <p>
                  You may qualify for these active schemes, but some eligibility criteria could not
                  be verified against your profile. Update your{' '}
                  <Link to="/profile">Profile</Link> to check full qualification.
                </p>
              </div>

              <div className="schemes-grid">
                {verificationRequired.map((scheme) => (
                  <SchemeCard
                    key={scheme.scheme_id}
                    scheme={scheme}
                    isVerificationRequired={true}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
