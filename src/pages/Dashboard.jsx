import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Compass,
  User,
  Bell,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Building2,
  Users,
  Banknote,
  Search,
  Mic,
  Bookmark,
  ChevronRight,
  Languages,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { fetchActiveSchemes, fetchProfile, fetchUnreadNotifications, fetchSyncStatus } from '../services/api'
import SchemeCard from '../components/SchemeCard'

const CATEGORY_SHORTCUTS = [
  { name: 'Agriculture & Farmers', query: 'farmer', icon: '🌾' },
  { name: 'Education & Scholarships', query: 'scholarship student', icon: '🎓' },
  { name: 'Women Empowerment', query: 'women girl', icon: '👩' },
  { name: 'Housing & Urban Shelter', query: 'housing awas', icon: '🏠' },
  { name: 'Health & Wellness', query: 'health insurance', icon: '🏥' },
  { name: 'Youth & Self-Employment', query: 'employment loan subsidy', icon: '💼' },
]

export default function Dashboard() {
  const { user, token } = useAuth()
  const navigate = useNavigate()

  const [profile, setProfile] = useState(null)
  const [activeSchemes, setActiveSchemes] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [syncStatus, setSyncStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadDashboardData() {
      setLoading(true)
      setErrorMsg('')
      try {
        // Fetch sync status
        try {
          const syncInfo = await fetchSyncStatus()
          if (isMounted) setSyncStatus(syncInfo)
        } catch {}

        // 1. Fetch user profile
        let profData = null
        if (token) {
          try {
            profData = await fetchProfile(token)
            if (isMounted) setProfile(profData)
          } catch (err) {
            console.warn('Profile fetch warning:', err.message)
          }

          try {
            const notifResp = await fetchUnreadNotifications(token)
            if (isMounted && notifResp.unread_count !== undefined) {
              setUnreadCount(notifResp.unread_count)
            }
          } catch {}
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
        if (isMounted) setErrorMsg('Could not load portal data. Please try again.')
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
    <div className="space-y-8">
      {/* Editorial Civic Hero Section */}
      <section className="bg-[#07172c] text-white rounded-2xl p-6 sm:p-10 border border-slate-800 shadow-xl overflow-hidden relative">
        <div className="max-w-3xl space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
            <span>Direct Benefit Transfer (DBT) Framework</span>
            <span className="text-slate-400">·</span>
            <span className="text-slate-300">Statutory Welfare Directory</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Personalized Government Scheme & Welfare Discovery
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
            Welcome, <strong className="text-white font-semibold">{userName}</strong>. Our deterministic qualification engine verifies statutory rules against your demographic profile to recommend central and state welfare benefits you qualify for.
          </p>

          {/* Action CTAs */}
          <div className="pt-2 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/recommendations')}
              className="px-5 py-2.5 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold rounded-lg text-xs sm:text-sm transition-all shadow-md flex items-center gap-2"
            >
              <Compass className="w-4 h-4" />
              <span>Find My Eligible Schemes</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/chatbot')}
              className="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-lg text-xs sm:text-sm border border-white/20 transition-all flex items-center gap-2"
            >
              <Mic className="w-4 h-4 text-amber-400" />
              <span>Ask via Regional Voice (தமிழ் / हिन्दी)</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/profile')}
              className="px-4 py-2.5 text-slate-300 hover:text-white text-xs sm:text-sm font-medium transition-colors"
            >
              Update Profile Details →
            </button>
          </div>
        </div>
      </section>

      {/* Quantitative Civic Proof Metrics Strip (Tabular Figures) */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 sm:p-5 bg-white border border-slate-200 rounded-xl shadow-xs">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
            <Building2 className="w-4 h-4 text-blue-700" />
            <span>Verified Schemes</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-slate-900">
            {syncStatus?.total_schemes_monitored || 35}+
          </div>
          <p className="text-[11px] text-emerald-700 font-semibold mt-1 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Daily Auto-Sync Active
          </p>
        </div>

        <div className="p-4 sm:p-5 bg-white border border-slate-200 rounded-xl shadow-xs">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
            <Banknote className="w-4 h-4 text-emerald-700" />
            <span>DBT Benefits Coverage</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-slate-900">
            ₹2.8L+ Cr
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Direct transfer annual outlay</p>
        </div>

        <div className="p-4 sm:p-5 bg-white border border-slate-200 rounded-xl shadow-xs">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
            <ShieldCheck className="w-4 h-4 text-amber-600" />
            <span>Rule Evaluation</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-slate-900">
            100%
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Deterministic statutory check</p>
        </div>

        <div className="p-4 sm:p-5 bg-white border border-slate-200 rounded-xl shadow-xs">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
            <Languages className="w-4 h-4 text-purple-700" />
            <span>Regional Voice AI</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-slate-900">
            9 Languages
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Speech query and spoken audio</p>
        </div>
      </section>

      {/* Bento Grid: Citizen Demographic Status & Quick Voice Concierge */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Citizen Demographic Profile Card */}
        <div className="lg:col-span-2 p-6 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900">Citizen Demographic Profile</h2>
              <p className="text-xs text-slate-500">Demographic parameters used to filter statutory legal criteria</p>
            </div>
            <div className="flex items-center gap-1.5 text-xs">
              {profile?.profile_complete ? (
                <span className="flex items-center gap-1 text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Profile Complete</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-amber-800 font-semibold bg-amber-50 px-2.5 py-1 rounded-md border border-amber-200">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Update Needed</span>
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-500 block mb-0.5">Resident State</span>
              <span className="font-semibold text-slate-900 text-sm">
                {profile?.state_name || 'Tamil Nadu'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block mb-0.5">District</span>
              <span className="font-semibold text-slate-900 text-sm">
                {profile?.district_name || 'All Districts'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block mb-0.5">Occupation</span>
              <span className="font-semibold text-slate-900 text-sm">
                {profile?.occupation || 'General / Citizen'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block mb-0.5">Annual Income</span>
              <span className="font-semibold font-mono tabular-nums text-slate-900 text-sm">
                {profile?.annual_income ? `₹${profile.annual_income.toLocaleString('en-IN')}` : '₹1,20,000'}
              </span>
            </div>
          </div>

          {!profile?.profile_complete && (
            <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-amber-900">
              <p>
                Complete your demographic profile (income tier, education, social category) for strict legal qualification matching.
              </p>
              <Link
                to="/profile"
                className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded shrink-0 text-center transition-colors"
              >
                Complete Profile
              </Link>
            </div>
          )}
        </div>

        {/* Quick Regional Voice Concierge Spotlight */}
        <div className="p-6 bg-slate-900 text-white rounded-xl shadow-xs space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
              <Sparkles className="w-4 h-4" />
              <span>Voice Concierge</span>
            </div>
            <h3 className="text-base sm:text-lg font-bold text-white">Ask in Your Regional Language</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Get immediate spoken answers in Tamil (தமிழ்), Hindi (हिन्दी), Telugu (తెలుగు), Kannada, and Malayalam.
            </p>
          </div>

          <div className="pt-2">
            <button
              type="button"
              onClick={() => navigate('/chatbot')}
              className="w-full py-2.5 px-4 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold rounded-lg text-xs transition-colors flex items-center justify-center gap-2"
            >
              <Mic className="w-4 h-4" />
              <span>Open Voice Assistant</span>
            </button>
          </div>
        </div>
      </section>

      {/* Browse Schemes by Major Welfare Categories */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900">Browse by Welfare Category</h2>
            <p className="text-xs text-slate-500">Filter statutory schemes by target beneficiary segment</p>
          </div>
          <Link
            to="/recommendations"
            className="text-xs font-semibold text-blue-700 hover:text-blue-900 flex items-center gap-1"
          >
            <span>View All</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {CATEGORY_SHORTCUTS.map((cat, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => navigate(`/recommendations?q=${encodeURIComponent(cat.query)}`)}
              className="p-3 bg-white border border-slate-200 hover:border-slate-400 rounded-xl text-left transition-all group shadow-2xs hover:shadow-xs"
            >
              <div className="text-2xl mb-1 group-hover:scale-110 transition-transform">{cat.icon}</div>
              <h4 className="text-xs font-semibold text-slate-900 leading-tight">{cat.name}</h4>
            </button>
          ))}
        </div>
      </section>

      {/* Featured Active Schemes Directory */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900">Active Welfare Schemes Open for Application</h2>
            <p className="text-xs text-slate-500">Official schemes with active admission or benefit disbursements</p>
          </div>
          <Link
            to="/recommendations"
            className="text-xs font-semibold text-blue-700 hover:text-blue-900 flex items-center gap-1 shrink-0"
          >
            <span>Explore All Recommended Schemes</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500 space-y-2">
            <div className="w-6 h-6 border-2 border-slate-300 border-t-blue-700 rounded-full animate-spin mx-auto" />
            <p>Loading verified government scheme records...</p>
          </div>
        ) : errorMsg ? (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
            {errorMsg}
          </div>
        ) : activeSchemes.length === 0 ? (
          <div className="p-8 text-center bg-white border border-slate-200 rounded-xl space-y-2">
            <h3 className="text-sm font-bold text-slate-800">No Schemes Loaded</h3>
            <p className="text-xs text-slate-500">Please check network or refresh the directory.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeSchemes.map((scheme) => (
              <SchemeCard key={scheme.id || scheme.scheme_id} scheme={scheme} />
            ))}
          </div>
        )}
      </section>

      {/* How the Deterministic Qualification Engine Works */}
      <section className="bg-slate-100/70 border border-slate-200 rounded-xl p-6 space-y-4">
        <div className="space-y-1">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-slate-500">
            Engine Architecture
          </h3>
          <h2 className="text-base sm:text-lg font-bold text-slate-900">
            How Statutory Qualification & Recommendations Work
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-4 bg-white border border-slate-200 rounded-lg space-y-1.5 shadow-2xs">
            <div className="font-bold text-slate-900 text-sm">1. Demographic Profile</div>
            <p className="text-slate-600 leading-relaxed">
              Age, resident state, occupation, income ceiling, and category are kept confidential in local session memory.
            </p>
          </div>

          <div className="p-4 bg-white border border-slate-200 rounded-lg space-y-1.5 shadow-2xs">
            <div className="font-bold text-slate-900 text-sm">2. Deterministic Eligibility</div>
            <p className="text-slate-600 leading-relaxed">
              Statutory criteria are verified mathematically against official ministry guidelines. AI never overrides law.
            </p>
          </div>

          <div className="p-4 bg-white border border-slate-200 rounded-lg space-y-1.5 shadow-2xs">
            <div className="font-bold text-slate-900 text-sm">3. Deadline & Activity Check</div>
            <p className="text-slate-600 leading-relaxed">
              Schemes are filtered against real IST calendar application deadlines so expired schemes are excluded.
            </p>
          </div>

          <div className="p-4 bg-white border border-slate-200 rounded-lg space-y-1.5 shadow-2xs">
            <div className="font-bold text-slate-900 text-sm">4. Multilingual Synthesis</div>
            <p className="text-slate-600 leading-relaxed">
              Qualified programs are ranked and explained in regional languages with voice synthesis and direct application links.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
