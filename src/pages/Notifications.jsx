import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell, CheckCircle2, Clock, AlertCircle, ArrowRight, ShieldAlert } from 'lucide-react'
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
        prev.map((n) => (n.id === id ? { ...n, is_read: true, read: true } : n))
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
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true, read: true })))
      setActionFeedback('All notifications marked as read.')
      setTimeout(() => setActionFeedback(''), 3000)
    } catch (err) {
      setActionFeedback(err.message || 'Failed to mark all as read.')
      setTimeout(() => setActionFeedback(''), 3000)
    }
  }

  const unreadCount = notifications.filter((n) => !n.is_read && !n.read).length

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-3 border-slate-300 border-t-blue-700 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500">Checking deadline notifications...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#07172c] text-white rounded-xl p-6 sm:p-8 border border-slate-800 shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
            <span>Direct Benefit Transfer Alerts</span>
            <span className="text-slate-400">·</span>
            <span className="text-slate-300">Statutory Timelines</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Citizen Notifications
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-xl leading-relaxed">
            Statutory application deadlines, scholarship disbursement announcements, and profile updates for your verified schemes.
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            type="button"
            onClick={handleMarkAllRead}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-xs font-semibold border border-white/20 transition-colors shrink-0"
          >
            Mark All as Read ({unreadCount})
          </button>
        )}
      </div>

      {actionFeedback && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{actionFeedback}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between gap-2">
          <span>{errorMsg}</span>
          <button
            type="button"
            onClick={loadNotifications}
            className="px-2.5 py-1 bg-rose-600 text-white rounded font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {notifications.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-10 text-center max-w-lg mx-auto space-y-4 shadow-sm">
          <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mx-auto text-slate-600">
            <Bell className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">No Notifications</h3>
            <p className="text-xs text-slate-600 leading-relaxed max-w-sm mx-auto">
              When you bookmark government schemes or application closing deadlines approach, verified alerts appear here automatically.
            </p>
          </div>
          <Link
            to="/recommendations"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#07172c] hover:bg-slate-800 text-white font-bold rounded-xl text-xs sm:text-sm transition-colors shadow-sm"
          >
            <span>Explore Active Schemes</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-600 pb-2 border-b border-slate-200">
            <span>
              <strong className="text-slate-900 font-mono tabular-nums">{notifications.length}</strong> total alerts (
              <span className="font-mono tabular-nums text-blue-700 font-bold">{unreadCount}</span> unread)
            </span>
          </div>

          <div className="space-y-2.5">
            {notifications.map((notif) => {
              const isRead = notif.is_read || notif.read
              return (
                <div
                  key={notif.id}
                  className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    isRead
                      ? 'bg-white border-slate-200 opacity-80'
                      : 'bg-blue-50/40 border-blue-200 shadow-2xs'
                  }`}
                >
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-bold text-slate-900">
                        {notif.notification_type === 'DEADLINE_URGENT'
                          ? 'Urgent Deadline'
                          : notif.notification_type === 'DEADLINE_TODAY'
                          ? 'Closing Today'
                          : 'Official Notice'}
                      </span>
                      <span className="text-slate-300">·</span>
                      <span className="text-[11px] text-slate-500 font-mono tabular-nums">
                        {new Date(notif.created_at || Date.now()).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </span>
                      {!isRead && (
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-300">
                          New
                        </span>
                      )}
                    </div>
                    <p className="text-xs sm:text-sm text-slate-800 font-normal leading-relaxed">
                      {notif.message}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 text-xs">
                    {notif.scheme_id && (
                      <Link
                        to={`/schemes/${notif.scheme_id}`}
                        className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 rounded-lg font-semibold transition-colors"
                      >
                        View Details →
                      </Link>
                    )}
                    {!isRead && (
                      <button
                        type="button"
                        onClick={() => handleMarkRead(notif.id)}
                        className="px-3 py-1.5 text-blue-700 hover:text-blue-900 font-semibold"
                      >
                        Mark Read
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
