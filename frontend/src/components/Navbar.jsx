import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { fetchUnreadNotifications } from '../services/api'

export default function Navbar() {
  const { user, session, logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    let isMounted = true
    if (!isAuthenticated || !session?.access_token) {
      return
    }

    async function checkUnread() {
      try {
        const res = await fetchUnreadNotifications(session.access_token)
        if (isMounted && res.unread_count !== undefined) {
          setUnreadCount(res.unread_count)
        }
      } catch {
        // Non-blocking
      }
    }

    checkUnread()
    return () => {
      isMounted = false
    }
  }, [isAuthenticated, session])

  const handleLogout = async () => {
    try {
      setUnreadCount(0)
      await logout()
      navigate('/login')
    } catch (err) {
      console.error('Logout error:', err)
    }
  }

  return (
    <header className="navbar">
      <div className="nav-container">
        <Link to={isAuthenticated ? '/dashboard' : '/login'} className="brand">
          <div className="brand-logo">🏛️</div>
          <div className="brand-text">
            <span className="brand-title">SchemeSetu</span>
            <span className="brand-subtitle">AI Government Scheme Portal</span>
          </div>
        </Link>

        <nav className="nav-links">
          {isAuthenticated ? (
            <>
              <NavLink
                to="/dashboard"
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                Dashboard
              </NavLink>
              <NavLink
                to="/profile"
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                Profile
              </NavLink>
              <NavLink
                to="/recommendations"
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                Find Schemes
              </NavLink>
              <NavLink
                to="/chatbot"
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                Scheme Assistant
              </NavLink>
              <NavLink
                to="/saved-schemes"
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                Saved Schemes
              </NavLink>
              <NavLink
                to="/notifications"
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                Notifications
                {unreadCount > 0 && (
                  <span className="nav-unread-badge">{unreadCount}</span>
                )}
              </NavLink>
              <div className="user-badge" title={user?.email}>
                <span className="user-dot"></span>
                <span className="user-name">
                  {user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Citizen'}
                </span>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="btn btn-sm btn-logout"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                Login
              </NavLink>
              <NavLink
                to="/register"
                className={({ isActive }) => (isActive ? 'nav-item active btn-nav-cta' : 'nav-item btn-nav-cta')}
              >
                Register
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
