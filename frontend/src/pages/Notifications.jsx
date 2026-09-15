import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../services/api'

export default function Notifications() {
  const { session, isAuthenticated } = useAuth()
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [actionFeedback, setActionFeedback] = useState('')

  const loadNotifications = async () => {
    if (!isAuthenticated || !session?.access_token) {
      setLoading(false)
      return
    }

    setLoading(true)
    setErrorMsg('')
    try {
      const data = await fetchNotifications(session.access_token)
      setNotifications(Array.isArray(data) ? data : [])
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load notifications.')
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
        const data = await fetchNotifications(session.access_token)
        if (isMounted) {
          setNotifications(Array.isArray(data) ? data : [])
        }
      } catch (err) {
        if (isMounted) {
          setErrorMsg(err.message || 'Failed to load notifications.')
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

  const handleMarkRead = async (id) => {
    if (!session?.access_token) return
    try {
      await markNotificationRead(id, session.access_token)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
    } catch (err) {
      setActionFeedback(err.message || 'Failed to mark as read.')
      setTimeout(() => setActionFeedback(''), 3000)
    }
  }

  const handleMarkAllRead = async () => {
    if (!session?.access_token) return
    try {
      await markAllNotificationsRead(session.access_token)
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setActionFeedback('All notifications marked as read.')
      setTimeout(() => setActionFeedback(''), 3000)
    } catch (err) {
      setActionFeedback(err.message || 'Failed to mark all as read.')
      setTimeout(() => setActionFeedback(''), 3000)
    }
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length

  const getBadgeClass = (type) => {
    switch (type) {
      case 'DEADLINE_TODAY':
        return 'notif-badge-today'
      case 'DEADLINE_URGENT':
        return 'notif-badge-urgent'
      case 'DEADLINE_APPROACHING':
        return 'notif-badge-approaching'
      default:
        return 'notif-badge-default'
    }
  }

  const getBadgeLabel = (type) => {
    switch (type) {
      case 'DEADLINE_TODAY':
        return '🚨 CLOSING TODAY'
      case 'DEADLINE_URGENT':
        return '🔴 URGENT DEADLINE'
      case 'DEADLINE_APPROACHING':
        return '🟡 DEADLINE APPROACHING'
      default:
        return '📢 NOTICE'
    }
  }

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner"></div>
        <p>Loading your notifications...</p>
      </div>
    )
  }

  return (
    <div className="notifications-page">
      <div className="page-header notif-header-row">
        <div>
          <h1 className="page-title">Citizen Notifications</h1>
          <p className="page-subtitle">
            Statutory deadline alerts and application updates for your bookmarked welfare schemes.
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            type="button"
            onClick={handleMarkAllRead}
            className="btn btn-outline btn-sm"
          >
            Mark all as read
          </button>
        )}
      </div>

      {actionFeedback && (
        <div className="alert alert-info mb-4">
          <span>{actionFeedback}</span>
        </div>
      )}

      {errorMsg && (
        <div className="alert alert-danger mb-4">
          <span>{errorMsg}</span>
          <button type="button" onClick={loadNotifications} className="btn btn-sm btn-outline ml-2">
            Retry
          </button>
        </div>
      )}

      <div className="notif-status-bar">
        <span>
          <strong>{notifications.length}</strong> total alerts (<strong>{unreadCount}</strong> unread)
        </span>
      </div>

      {notifications.length === 0 ? (
        <div className="empty-notif-state">
          <div className="empty-icon">🔔</div>
          <h3>No notifications yet.</h3>
          <p className="empty-text">
            When you bookmark government schemes that you are eligible for, deadline alerts will
            automatically appear here when application windows approach closing dates.
          </p>
          <div className="empty-actions mt-4">
            <Link to="/saved-schemes" className="btn btn-outline mr-2">
              View Saved Schemes
            </Link>
            <Link to="/recommendations" className="btn btn-primary">
              Browse Schemes
            </Link>
          </div>
        </div>
      ) : (
        <div className="notif-list">
          {notifications.map((notif) => (
            <div
              key={notif.id}
              className={`notif-card ${notif.is_read ? 'notif-read' : 'notif-unread'}`}
            >
              <div className="notif-card-header">
                <div className="notif-badge-group">
                  <span className={`badge ${getBadgeClass(notif.notification_type)}`}>
                    {getBadgeLabel(notif.notification_type)}
                  </span>
                  {!notif.is_read && <span className="unread-dot-indicator">Unread</span>}
                </div>
                <span className="notif-date text-xs text-muted">
                  {new Date(notif.created_at).toLocaleDateString(undefined, {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </span>
              </div>

              <p className="notif-message">{notif.message}</p>

              <div className="notif-card-footer">
                {notif.scheme_id ? (
                  <Link to={`/schemes/${notif.scheme_id}`} className="btn btn-sm btn-outline">
                    View Scheme Details
                  </Link>
                ) : (
                  <span></span>
                )}

                {!notif.is_read && (
                  <button
                    type="button"
                    onClick={() => handleMarkRead(notif.id)}
                    className="btn btn-sm btn-text-action"
                  >
                    Mark as read ✓
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
