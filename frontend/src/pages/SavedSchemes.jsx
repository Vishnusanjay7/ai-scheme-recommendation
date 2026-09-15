import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
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
      // Optimistically update list
      setSavedSchemes((prev) => prev.filter((s) => (s.scheme_id || s.id) !== schemeId))
      setActionMsg('Scheme removed from bookmarks.')
      setTimeout(() => setActionMsg(''), 3000)
    } catch (err) {
      setActionMsg(err.message || 'Failed to remove scheme.')
      setTimeout(() => setActionMsg(''), 3000)
    }
  }

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner"></div>
        <p>Loading your saved schemes...</p>
      </div>
    )
  }

  return (
    <div className="saved-schemes-page">
      <div className="page-header">
        <h1 className="page-title">Saved Government Schemes</h1>
        <p className="page-subtitle">
          Review welfare schemes and subsidies you have bookmarked. Application deadlines and activity
          statuses reflect live government timelines.
        </p>
      </div>

      {actionMsg && (
        <div className="alert alert-info mb-4">
          <span>{actionMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="alert alert-danger mb-4">
          <span>{errorMsg}</span>
          <button type="button" onClick={loadSaved} className="btn btn-sm btn-outline ml-2">
            Retry
          </button>
        </div>
      )}

      {savedSchemes.length === 0 ? (
        <div className="empty-saved-state">
          <div className="empty-icon">🔖</div>
          <h3>No saved schemes yet.</h3>
          <p className="empty-text">
            Save government schemes you want to review later. When you find eligible schemes on the
            recommendations page, click "Save Scheme" to track them here.
          </p>
          <div className="empty-actions mt-4">
            <Link to="/recommendations" className="btn btn-primary btn-lg">
              Find Government Schemes
            </Link>
          </div>
        </div>
      ) : (
        <div className="saved-grid">
          <div className="saved-count-bar">
            <span>
              You have <strong>{savedSchemes.length}</strong> saved {savedSchemes.length === 1 ? 'scheme' : 'schemes'}
            </span>
          </div>

          <div className="scheme-card-grid">
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
