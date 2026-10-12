import { useEffect, useState, useRef } from 'react'
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import {
  Landmark,
  LayoutDashboard,
  Compass,
  Bookmark,
  Bell,
  Bot,
  User,
  LogOut,
  Menu,
  X,
  LogIn,
  UserPlus,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { fetchUnreadNotifications } from '../services/api'
import { cn } from '../lib/utils'

export default function Navbar() {
  const { user, session, logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [unreadCount, setUnreadCount] = useState(0)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const mobileMenuRef = useRef(null)

  // Fetch unread notifications for authenticated citizen
  useEffect(() => {
    let isMounted = true
    if (!isAuthenticated || !session?.access_token) {
      return
    }

    async function checkUnread() {
      try {
        const res = await fetchUnreadNotifications(session.access_token)
        if (isMounted && res && res.unread_count !== undefined) {
          setUnreadCount(res.unread_count)
        }
      } catch {
        // Non-blocking for offline or dev resilience
      }
    }

    checkUnread()
    return () => {
      isMounted = false
    }
  }, [isAuthenticated, session])

  // Automatically close mobile menu when pathname changes (e.g. back/forward button)
  const [prevPathname, setPrevPathname] = useState(location.pathname)
  if (location.pathname !== prevPathname) {
    setPrevPathname(location.pathname)
    setIsMobileMenuOpen(false)
  }

  // Keyboard navigation & click-outside handling for mobile menu
  useEffect(() => {
    if (!isMobileMenuOpen) return

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setIsMobileMenuOpen(false)
      }
    }

    function handleClickOutside(event) {
      if (
        mobileMenuRef.current &&
        !mobileMenuRef.current.contains(event.target) &&
        !event.target.closest('#mobile-nav-toggle')
      ) {
        setIsMobileMenuOpen(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    document.addEventListener('mousedown', handleClickOutside)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isMobileMenuOpen])

  const handleLogout = async () => {
    try {
      setUnreadCount(0)
      setIsMobileMenuOpen(false)
      await logout()
      navigate('/login')
    } catch (err) {
      console.error('Logout error:', err)
    }
  }

  const displayName =
    user?.user_metadata?.full_name ||
    user?.email?.split('@')[0] ||
    'Citizen'

  return (
    <header className="navbar sticky top-0 z-50 bg-[#0a2342] text-white shadow-md border-b border-slate-800 transition-colors duration-150">
      {/* Top Civic Utility Ribbon */}
      <div className="hidden sm:block bg-slate-950/50 text-slate-300 text-[11px] border-b border-white/5 py-1 px-4 text-center font-normal tracking-wide">
        SchemeSetu Citizen Portal • Academic Project Prototype • Deterministic Welfare Eligibility Engine
      </div>

      <div className="nav-container max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5 flex items-center justify-between gap-4">
        {/* Brand Link */}
        <Link
          to={isAuthenticated ? '/dashboard' : '/login'}
          className="brand flex items-center gap-3 text-white no-underline hover:no-underline group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 rounded-md p-1"
          aria-label="SchemeSetu Home"
        >
          <div className="brand-logo flex items-center justify-center w-9 h-9 rounded-lg bg-amber-500/20 border border-amber-400/40 text-amber-400 group-hover:scale-105 transition-transform duration-150 shadow-inner">
            <Landmark className="w-5 h-5 text-amber-400" aria-hidden="true" />
          </div>
          <div className="brand-text flex flex-col">
            <span className="brand-title text-lg sm:text-xl font-bold tracking-tight text-white flex items-center gap-1.5 leading-tight">
              SchemeSetu
              <span className="text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Prototype
              </span>
            </span>
            <span className="brand-subtitle text-[11px] text-blue-200 tracking-wider font-medium leading-tight">
              Government Scheme Discovery Portal
            </span>
          </div>
        </Link>

        {/* Desktop Primary Navigation */}
        <nav
          className="nav-links !hidden md:!flex items-center gap-1.5 lg:gap-2"
          aria-label="Primary Navigation"
        >
          {isAuthenticated ? (
            <>
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  cn(
                    'nav-item inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs lg:text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400',
                    isActive
                      ? 'active bg-white/15 text-white font-semibold shadow-sm'
                      : 'text-slate-200 hover:text-white hover:bg-white/10'
                  )
                }
              >
                <LayoutDashboard className="w-4 h-4 text-blue-300" aria-hidden="true" />
                <span>Dashboard</span>
              </NavLink>

              <NavLink
                to="/recommendations"
                className={({ isActive }) =>
                  cn(
                    'nav-item inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs lg:text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400',
                    isActive
                      ? 'active bg-white/15 text-white font-semibold shadow-sm'
                      : 'text-slate-200 hover:text-white hover:bg-white/10'
                  )
                }
              >
                <Compass className="w-4 h-4 text-blue-300" aria-hidden="true" />
                <span>Find Schemes</span>
              </NavLink>

              <NavLink
                to="/saved-schemes"
                className={({ isActive }) =>
                  cn(
                    'nav-item inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs lg:text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400',
                    isActive
                      ? 'active bg-white/15 text-white font-semibold shadow-sm'
                      : 'text-slate-200 hover:text-white hover:bg-white/10'
                  )
                }
              >
                <Bookmark className="w-4 h-4 text-blue-300" aria-hidden="true" />
                <span>Saved Schemes</span>
              </NavLink>

              <NavLink
                to="/notifications"
                className={({ isActive }) =>
                  cn(
                    'nav-item inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs lg:text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 relative',
                    isActive
                      ? 'active bg-white/15 text-white font-semibold shadow-sm'
                      : 'text-slate-200 hover:text-white hover:bg-white/10'
                  )
                }
              >
                <Bell className="w-4 h-4 text-blue-300" aria-hidden="true" />
                <span>Notifications</span>
                {unreadCount > 0 && (
                  <span
                    className="nav-unread-badge inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold leading-none text-white bg-rose-600 rounded-full ml-1 animate-pulse"
                    aria-label={`${unreadCount} unread notifications`}
                  >
                    {unreadCount}
                  </span>
                )}
              </NavLink>

              <NavLink
                to="/chatbot"
                className={({ isActive }) =>
                  cn(
                    'nav-item inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs lg:text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400',
                    isActive
                      ? 'active bg-white/15 text-white font-semibold shadow-sm'
                      : 'text-slate-200 hover:text-white hover:bg-white/10'
                  )
                }
              >
                <Bot className="w-4 h-4 text-blue-300" aria-hidden="true" />
                <span>Scheme Assistant</span>
              </NavLink>

              <NavLink
                to="/profile"
                className={({ isActive }) =>
                  cn(
                    'nav-item inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs lg:text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400',
                    isActive
                      ? 'active bg-white/15 text-white font-semibold shadow-sm'
                      : 'text-slate-200 hover:text-white hover:bg-white/10'
                  )
                }
              >
                <User className="w-4 h-4 text-blue-300" aria-hidden="true" />
                <span>Profile</span>
              </NavLink>

              {/* Citizen Indicator Pill */}
              <div
                className="user-badge inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10 border border-white/15 text-xs text-slate-200 ml-1"
                title={user?.email}
              >
                <span className="user-dot w-2 h-2 rounded-full bg-emerald-400" />
                <span className="user-name max-w-[100px] lg:max-w-[130px] truncate font-medium">
                  {displayName}
                </span>
              </div>

              {/* Primary Logout Button */}
              <button
                type="button"
                onClick={handleLogout}
                className="btn btn-sm btn-logout inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-semibold bg-rose-600/90 hover:bg-rose-700 text-white transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 cursor-pointer ml-1"
                aria-label="Logout from session"
              >
                <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className={({ isActive }) =>
                  cn(
                    'nav-item inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400',
                    isActive
                      ? 'active bg-white/15 text-white font-semibold shadow-sm'
                      : 'text-slate-200 hover:text-white hover:bg-white/10'
                  )
                }
              >
                <LogIn className="w-4 h-4 text-blue-300" aria-hidden="true" />
                <span>Login</span>
              </NavLink>

              <NavLink
                to="/register"
                className={({ isActive }) =>
                  cn(
                    'nav-item btn-nav-cta inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-sm font-semibold bg-amber-500 hover:bg-amber-600 text-slate-950 transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300 shadow-sm ml-1',
                    isActive ? 'active ring-2 ring-white/50' : ''
                  )
                }
              >
                <UserPlus className="w-4 h-4 text-slate-950" aria-hidden="true" />
                <span>Register</span>
              </NavLink>
            </>
          )}
        </nav>

        {/* Mobile Menu Toggle Button */}
        <button
          id="mobile-nav-toggle"
          type="button"
          onClick={() => setIsMobileMenuOpen((prev) => !prev)}
          className="md:hidden inline-flex items-center justify-center p-2 rounded-md text-slate-200 hover:text-white hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 transition-colors"
          aria-label={isMobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={isMobileMenuOpen}
          aria-controls="mobile-nav-menu"
        >
          {isMobileMenuOpen ? (
            <X className="w-6 h-6 text-amber-300" aria-hidden="true" />
          ) : (
            <Menu className="w-6 h-6" aria-hidden="true" />
          )}
        </button>
      </div>

      {/* Mobile Navigation Drawer */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            id="mobile-nav-menu"
            ref={mobileMenuRef}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.18, ease: 'easeInOut' }}
            className="md:hidden border-t border-slate-800 bg-[#0a2342] px-4 pt-3 pb-5 shadow-2xl overflow-hidden"
          >
            <div className="flex flex-col gap-1.5">
              {isAuthenticated ? (
                <>
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs text-slate-300">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span className="font-semibold text-white">{displayName}</span>
                    </div>
                    <span className="text-[11px] text-blue-200">{user?.email}</span>
                  </div>

                  <NavLink
                    to="/dashboard"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-white/15 text-white font-semibold'
                          : 'text-slate-200 hover:bg-white/10 hover:text-white'
                      )
                    }
                  >
                    <LayoutDashboard className="w-4 h-4 text-blue-300" aria-hidden="true" />
                    <span>Dashboard</span>
                  </NavLink>

                  <NavLink
                    to="/recommendations"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-white/15 text-white font-semibold'
                          : 'text-slate-200 hover:bg-white/10 hover:text-white'
                      )
                    }
                  >
                    <Compass className="w-4 h-4 text-blue-300" aria-hidden="true" />
                    <span>Find Schemes</span>
                  </NavLink>

                  <NavLink
                    to="/saved-schemes"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-white/15 text-white font-semibold'
                          : 'text-slate-200 hover:bg-white/10 hover:text-white'
                      )
                    }
                  >
                    <Bookmark className="w-4 h-4 text-blue-300" aria-hidden="true" />
                    <span>Saved Schemes</span>
                  </NavLink>

                  <NavLink
                    to="/notifications"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-white/15 text-white font-semibold'
                          : 'text-slate-200 hover:bg-white/10 hover:text-white'
                      )
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Bell className="w-4 h-4 text-blue-300" aria-hidden="true" />
                      <span>Notifications</span>
                    </div>
                    {unreadCount > 0 && (
                      <span className="px-2 py-0.5 text-xs font-bold text-white bg-rose-600 rounded-full">
                        {unreadCount}
                      </span>
                    )}
                  </NavLink>

                  <NavLink
                    to="/chatbot"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-white/15 text-white font-semibold'
                          : 'text-slate-200 hover:bg-white/10 hover:text-white'
                      )
                    }
                  >
                    <Bot className="w-4 h-4 text-blue-300" aria-hidden="true" />
                    <span>Scheme Assistant</span>
                  </NavLink>

                  <NavLink
                    to="/profile"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-white/15 text-white font-semibold'
                          : 'text-slate-200 hover:bg-white/10 hover:text-white'
                      )
                    }
                  >
                    <User className="w-4 h-4 text-blue-300" aria-hidden="true" />
                    <span>Citizen Profile</span>
                  </NavLink>

                  <div className="pt-2 mt-2 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={handleLogout}
                      className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-semibold bg-rose-600/90 hover:bg-rose-700 text-white transition-colors cursor-pointer"
                    >
                      <LogOut className="w-4 h-4" aria-hidden="true" />
                      <span>Logout from Session</span>
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <NavLink
                    to="/login"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-white/15 text-white font-semibold'
                          : 'text-slate-200 hover:bg-white/10 hover:text-white'
                      )
                    }
                  >
                    <LogIn className="w-4 h-4 text-blue-300" aria-hidden="true" />
                    <span>Login</span>
                  </NavLink>

                  <NavLink
                    to="/register"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-semibold bg-amber-500 hover:bg-amber-600 text-slate-950 transition-colors mt-1"
                  >
                    <UserPlus className="w-4 h-4" aria-hidden="true" />
                    <span>Register New Citizen</span>
                  </NavLink>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
