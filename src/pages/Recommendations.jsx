import { useEffect, useState, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Search,
  Mic,
  MicOff,
  Filter,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Building2,
  Compass,
  RefreshCw,
  Clock,
  Calendar,
  Layers,
  MapPin,
  SlidersHorizontal,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import {
  fetchRecommendations,
  fetchStates,
  fetchDistricts,
  fetchSyncStatus,
  triggerManualSync,
} from '../services/api'
import SchemeCard from '../components/SchemeCard'

const QUICK_FILTERS = [
  { label: 'All Schemes', query: '' },
  { label: '🌾 Farmers & Agriculture', query: 'farmer agriculture crop' },
  { label: '🎓 Students & Education', query: 'student scholarship college' },
  { label: '👩 Women Welfare', query: 'women girl mother' },
  { label: '💼 Youth & Employment', query: 'unemployed business loan' },
  { label: '🏠 Housing & Shelter', query: 'housing awas' },
  { label: '☀️ Solar & Energy', query: 'solar rooftop bijli' },
  { label: '🏥 Healthcare', query: 'health ayushman hospital' },
]

const CATEGORY_OPTIONS = [
  { value: '', label: 'All Categories' },
  { value: 'Agriculture & Farmers Welfare', label: 'Agriculture & Farmers Welfare' },
  { value: 'Education & Scholarships', label: 'Education & Scholarships' },
  { value: 'Women & Child Development', label: 'Women & Child Development' },
  { value: 'Skills & Employment', label: 'Skills & Employment' },
  { value: 'Health & Wellness', label: 'Health & Wellness' },
  { value: 'Housing & Shelter', label: 'Housing & Shelter' },
  { value: 'Banking & Financial Services', label: 'Banking & Financial Services' },
  { value: 'Renewable Energy & Utilities', label: 'Renewable Energy & Utilities' },
  { value: 'Social Welfare & Pensions', label: 'Social Welfare & Pensions' },
]

export default function Recommendations() {
  const { token } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialQuery = searchParams.get('q') || ''

  const [query, setQuery] = useState(initialQuery)
  const [recommendations, setRecommendations] = useState([])
  const [verificationRequired, setVerificationRequired] = useState([])
  const [rankingMethod, setRankingMethod] = useState('DETERMINISTIC_HYBRID_MULTIFACTOR')
  const [totalCandidates, setTotalCandidates] = useState(0)

  // Filter & Sort State
  const [levelFilter, setLevelFilter] = useState('ALL') // ALL, CENTRAL, STATE
  const [categoryFilter, setCategoryFilter] = useState('')
  const [sortBy, setSortBy] = useState('match') // match, deadline, popular

  // Location Filters
  const [states, setStates] = useState([])
  const [districts, setDistricts] = useState([])
  const [selectedStateId, setSelectedStateId] = useState('')
  const [selectedDistrictId, setSelectedDistrictId] = useState('')
  const [loadingDistricts, setLoadingDistricts] = useState(false)

  // Sync Engine State
  const [syncData, setSyncData] = useState(null)
  const [isSyncing, setIsSyncing] = useState(false)
  const [syncFeedback, setSyncFeedback] = useState('')

  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [isListening, setIsListening] = useState(false)

  const recognitionRef = useRef(null)

  // Load States reference data and Daily Sync status
  useEffect(() => {
    let mounted = true
    async function loadInitialData() {
      try {
        const [statesList, syncStatus] = await Promise.allSettled([
          fetchStates(),
          fetchSyncStatus(),
        ])
        if (mounted) {
          if (statesList.status === 'fulfilled') setStates(statesList.value || [])
          if (syncStatus.status === 'fulfilled') setSyncData(syncStatus.value)
        }
      } catch (err) {
        console.error('Failed to load filter metadata:', err)
      }
    }
    loadInitialData()
    return () => {
      mounted = false
    }
  }, [])

  // When selectedStateId changes, load districts for that state
  const handleStateFilterChange = async (newStateId) => {
    setSelectedStateId(newStateId)
    setSelectedDistrictId('')
    setDistricts([])

    if (!newStateId) return

    setLoadingDistricts(true)
    try {
      const dists = await fetchDistricts(newStateId)
      setDistricts(dists || [])
    } catch (err) {
      console.error('Failed to load districts:', err)
    } finally {
      setLoadingDistricts(false)
    }
  }

  // Execute recommendation search with current query and filters
  const executeSearch = async (searchQuery = null, overrideOptions = {}) => {
    setErrorMsg('')
    setSearching(true)

    const opts = {
      sort: overrideOptions.sortBy || sortBy,
      level: overrideOptions.levelFilter !== undefined ? overrideOptions.levelFilter : (levelFilter === 'ALL' ? null : levelFilter),
      category: overrideOptions.categoryFilter !== undefined ? overrideOptions.categoryFilter : (categoryFilter || null),
      state_id: overrideOptions.stateId !== undefined ? overrideOptions.stateId : (selectedStateId || null),
    }

    try {
      const data = await fetchRecommendations(searchQuery !== null ? searchQuery : query, token, 60, 0, opts)
      setRecommendations(data.recommendations || [])
      setVerificationRequired(data.verification_required || [])
      setRankingMethod(data.ranking_method || 'DETERMINISTIC_HYBRID_MULTIFACTOR')
      setTotalCandidates(data.total_candidates || 0)
    } catch (err) {
      setErrorMsg(err.message || 'Failed to retrieve recommendations. Please check your network and try again.')
      setRecommendations([])
      setVerificationRequired([])
    } finally {
      setSearching(false)
    }
  }

  useEffect(() => {
    let ignore = false

    async function fetchInitialRecommendations() {
      try {
        const data = await fetchRecommendations(initialQuery || null, token, 60, 0, {
          sort: sortBy,
          level: levelFilter === 'ALL' ? null : levelFilter,
          category: categoryFilter || null,
          state_id: selectedStateId || null,
        })
        if (!ignore) {
          setRecommendations(data.recommendations || [])
          setVerificationRequired(data.verification_required || [])
          setRankingMethod(data.ranking_method || 'DETERMINISTIC_HYBRID_MULTIFACTOR')
          setTotalCandidates(data.total_candidates || 0)
          setLoading(false)
        }
      } catch (err) {
        if (!ignore) {
          setErrorMsg(err.message || 'Failed to retrieve recommendations.')
          setRecommendations([])
          setVerificationRequired([])
          setLoading(false)
        }
      }
    }

    fetchInitialRecommendations()
    return () => {
      ignore = true
      if (recognitionRef.current) recognitionRef.current.stop()
    }
  }, [token, initialQuery])

  // Manual Trigger for Daily Scheme Synchronization
  const handleTriggerSync = async () => {
    setIsSyncing(true)
    setSyncFeedback('')
    try {
      const res = await triggerManualSync()
      setSyncFeedback(`Sync complete! ${res.schemes_updated || 0} schemes verified.`)
      const updatedStatus = await fetchSyncStatus()
      setSyncData(updatedStatus)
      // Refresh recommendations list
      await executeSearch()
    } catch (err) {
      setSyncFeedback(err.message || 'Sync failed')
    } finally {
      setIsSyncing(false)
      setTimeout(() => setSyncFeedback(''), 4000)
    }
  }

  // Voice Search via Web Speech API
  const toggleVoiceSearch = () => {
    if (isListening) {
      if (recognitionRef.current) recognitionRef.current.stop()
      setIsListening(false)
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setErrorMsg('Voice input not supported in this browser. Please use Chrome or Safari.')
      return
    }

    try {
      const rec = new SpeechRecognition()
      recognitionRef.current = rec
      rec.lang = 'en-IN'
      rec.continuous = false
      rec.interimResults = false

      rec.onstart = () => setIsListening(true)
      rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        setQuery(transcript)
        executeSearch(transcript)
      }
      rec.onerror = () => setIsListening(false)
      rec.onend = () => setIsListening(false)

      rec.start()
    } catch {
      setIsListening(false)
    }
  }

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    executeSearch(query.trim() || null)
  }

  const handleClearSearch = () => {
    setQuery('')
    setSearchParams({})
    setLevelFilter('ALL')
    setCategoryFilter('')
    setSelectedStateId('')
    setSelectedDistrictId('')
    executeSearch('', { levelFilter: null, categoryFilter: null, stateId: null })
  }

  // Filter recommendations by Government Level and District if selected
  const filteredRecommendations = recommendations.filter((item) => {
    if (levelFilter !== 'ALL' && item.government_level !== levelFilter) return false
    if (categoryFilter && item.category !== categoryFilter) return false
    if (selectedStateId && item.government_level === 'STATE' && Number(item.state_id) !== Number(selectedStateId)) return false
    return true
  })

  const filteredVerification = verificationRequired.filter((item) => {
    if (levelFilter !== 'ALL' && item.government_level !== levelFilter) return false
    if (categoryFilter && item.category !== categoryFilter) return false
    if (selectedStateId && item.government_level === 'STATE' && Number(item.state_id) !== Number(selectedStateId)) return false
    return true
  })

  // Format Sync Timestamp
  const formatSyncTime = (isoString) => {
    if (!isoString) return 'Today at 00:00 UTC'
    try {
      const d = new Date(isoString)
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' })
    } catch {
      return 'Today'
    }
  }

  return (
    <div className="space-y-6">
      {/* Daily Automated Synchronization Ribbon */}
      <div className="bg-slate-900 text-slate-200 border border-slate-800 rounded-xl px-4 py-2.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs shadow-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1.5 font-bold text-amber-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Daily Automated Sync Engine Active
          </span>
          <span className="text-slate-500">·</span>
          <span className="text-slate-300">
            Last Updated:{' '}
            <strong className="font-mono text-white">
              {formatSyncTime(syncData?.last_synced_at)}
            </strong>
          </span>
          <span className="text-slate-500">·</span>
          <span className="text-slate-400">
            {syncData?.total_schemes_monitored || totalCandidates} Live Central & State Schemes
          </span>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          {syncFeedback && (
            <span className="text-emerald-400 font-semibold text-xs animate-fade-in">
              {syncFeedback}
            </span>
          )}
          <button
            type="button"
            onClick={handleTriggerSync}
            disabled={isSyncing}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 transition-colors font-medium text-xs disabled:opacity-50"
            title="Force immediate daily synchronization check"
          >
            <RefreshCw className={`w-3 h-3 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>{isSyncing ? 'Synchronizing...' : 'Sync Now'}</span>
          </button>
        </div>
      </div>

      {/* Header and Natural Language Search Banner */}
      <div className="bg-[#07172c] text-white rounded-xl p-6 sm:p-8 shadow-md border border-slate-800 space-y-4">
        <div className="max-w-3xl space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
            <span>High-Precision Qualification Engine</span>
            <span className="text-slate-400">·</span>
            <span className="text-slate-300">Pan-India Coverage (All States & UTs)</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Welfare Scheme Recommendations
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Every scheme is evaluated with multi-factor scoring against your age, state, district, income tier, occupation, category, and active application deadlines. Express queries by voice in regional languages or filter by district.
          </p>
        </div>

        {/* Natural Language Search Input with Voice Microphone */}
        <form onSubmit={handleSearchSubmit} className="pt-2 flex flex-col sm:flex-row gap-2 max-w-3xl">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. 'farmer subsidy', 'scholarship for college', 'solar rooftop', 'women monthly income'"
              className="w-full pl-10 pr-20 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-xs sm:text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent transition-all"
              disabled={searching}
            />

            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
              {query && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="text-slate-400 hover:text-white text-xs px-1.5 py-0.5 rounded"
                  title="Clear"
                >
                  ✕
                </button>
              )}
              <button
                type="button"
                onClick={toggleVoiceSearch}
                className={`p-1.5 rounded-lg transition-colors ${
                  isListening
                    ? 'bg-rose-600 text-white animate-pulse'
                    : 'text-amber-400 hover:text-amber-300 hover:bg-white/10'
                }`}
                title={isListening ? 'Listening...' : 'Voice Search in Indian English / Regional'}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={searching}
            className="px-5 py-2.5 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold rounded-xl text-xs sm:text-sm transition-colors flex items-center justify-center gap-1.5 shrink-0 shadow-sm"
          >
            {searching ? 'Evaluating...' : 'Find Matches'}
          </button>
        </form>

        {/* Quick Search Categories */}
        <div className="pt-1 flex flex-wrap gap-1.5 text-xs">
          <span className="text-slate-400 text-xs self-center mr-1">Suggested:</span>
          {QUICK_FILTERS.map((qf, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setQuery(qf.query)
                executeSearch(qf.query || null)
              }}
              className="px-2.5 py-1 rounded-md text-xs font-medium bg-white/10 hover:bg-white/20 text-slate-200 transition-colors"
            >
              {qf.label}
            </button>
          ))}
        </div>
      </div>

      {/* Advanced Filter Toolbar: Geography, Category & Sorting */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3 text-xs">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100 flex-wrap gap-2">
          <div className="flex items-center gap-2 font-bold text-slate-900">
            <SlidersHorizontal className="w-4 h-4 text-slate-600" />
            <span>Targeting & Location Filters</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500 font-medium">Sort By:</span>
            <select
              value={sortBy}
              onChange={(e) => {
                const newSort = e.target.value
                setSortBy(newSort)
                executeSearch(query || null, { sortBy: newSort })
              }}
              className="px-2.5 py-1 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 text-xs font-medium focus:ring-2 focus:ring-blue-600"
            >
              <option value="match">Highest Match Score (Default)</option>
              <option value="deadline">Approaching Deadline (Closing Soonest)</option>
              <option value="popular">Most Popular / High Impact</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {/* Government Level */}
          <div className="space-y-1">
            <label className="block text-[11px] font-semibold text-slate-600">Scheme Jurisdiction</label>
            <select
              value={levelFilter}
              onChange={(e) => {
                const val = e.target.value
                setLevelFilter(val)
                executeSearch(query || null, { levelFilter: val === 'ALL' ? null : val })
              }}
              className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 text-xs focus:ring-2 focus:ring-blue-600"
            >
              <option value="ALL">All Levels (Central & State)</option>
              <option value="CENTRAL">Central Schemes (Pan-India)</option>
              <option value="STATE">State Government Schemes</option>
            </select>
          </div>

          {/* State Selector */}
          <div className="space-y-1">
            <label className="block text-[11px] font-semibold text-slate-600">State / Union Territory</label>
            <select
              value={selectedStateId}
              onChange={(e) => {
                handleStateFilterChange(e.target.value)
                executeSearch(query || null, { stateId: e.target.value || null })
              }}
              className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 text-xs focus:ring-2 focus:ring-blue-600"
            >
              <option value="">All States / UTs</option>
              {states.map((st) => (
                <option key={st.id} value={st.id}>
                  {st.name} ({st.code})
                </option>
              ))}
            </select>
          </div>

          {/* District Selector */}
          <div className="space-y-1">
            <label className="block text-[11px] font-semibold text-slate-600">District / City</label>
            <select
              value={selectedDistrictId}
              onChange={(e) => setSelectedDistrictId(e.target.value)}
              disabled={!selectedStateId || loadingDistricts}
              className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 text-xs focus:ring-2 focus:ring-blue-600 disabled:opacity-50"
            >
              <option value="">
                {loadingDistricts
                  ? 'Loading districts...'
                  : selectedStateId
                  ? 'All Districts in State'
                  : 'Select State First'}
              </option>
              {districts.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.full_display_name || d.name}
                </option>
              ))}
            </select>
          </div>

          {/* Category Filter */}
          <div className="space-y-1">
            <label className="block text-[11px] font-semibold text-slate-600">Beneficiary Sector</label>
            <select
              value={categoryFilter}
              onChange={(e) => {
                const cat = e.target.value
                setCategoryFilter(cat)
                executeSearch(query || null, { categoryFilter: cat || null })
              }}
              className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 text-xs focus:ring-2 focus:ring-blue-600"
            >
              {CATEGORY_OPTIONS.map((c, i) => (
                <option key={i} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Meta Filter & Stats Bar */}
      {!loading && !errorMsg && (
        <div className="bg-white border border-slate-200 rounded-xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-2xs">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-bold text-slate-900">
              <span className="font-mono tabular-nums text-sm text-blue-700">{filteredRecommendations.length}</span> Verified Schemes Available
            </span>
            <span className="text-slate-300">·</span>
            <span className="text-slate-500">
              Evaluated across <span className="font-mono tabular-nums font-semibold text-slate-700">{totalCandidates}</span> Live Catalog Items
            </span>
            {filteredVerification.length > 0 && (
              <>
                <span className="text-slate-300">·</span>
                <span className="text-amber-800 font-semibold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  {filteredVerification.length} Require Document Verification
                </span>
              </>
            )}
          </div>

          {(selectedStateId || categoryFilter || levelFilter !== 'ALL' || query) && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="text-slate-500 hover:text-slate-900 font-medium underline self-start sm:self-auto"
            >
              Reset All Filters
            </button>
          )}
        </div>
      )}

      {/* Error Message */}
      {errorMsg && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between gap-3">
          <span>{errorMsg}</span>
          <button
            type="button"
            onClick={() => executeSearch(query || null)}
            className="px-3 py-1 bg-rose-600 text-white rounded font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading ? (
        <div className="py-16 text-center space-y-3">
          <div className="w-8 h-8 border-3 border-slate-300 border-t-blue-700 rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500 font-medium">
            Running multi-factor eligibility engine, verifying deadlines, and ranking benefits...
          </p>
        </div>
      ) : filteredRecommendations.length === 0 && filteredVerification.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-10 text-center space-y-3 max-w-lg mx-auto">
          <Compass className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-900">No Matching Schemes Found</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            No live schemes matched your specific filters. Try expanding your search criteria or resetting filters to browse all verified central and state welfare programs.
          </p>
          <button
            type="button"
            onClick={handleClearSearch}
            className="px-4 py-2 bg-slate-900 text-white text-xs font-bold rounded-lg hover:bg-slate-800"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Main Eligible Recommendations Grid */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-800">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Verified Eligible Schemes ({filteredRecommendations.length})</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredRecommendations.map((scheme) => (
                <SchemeCard key={scheme.scheme_id || scheme.id} scheme={scheme} />
              ))}
            </div>
          </div>

          {/* Verification Required Section */}
          {filteredVerification.length > 0 && (
            <div className="space-y-3 pt-6 border-t border-slate-200">
              <div className="p-4 bg-amber-50/80 border border-amber-200 rounded-xl space-y-1 text-xs">
                <div className="flex items-center gap-1.5 font-bold text-amber-900">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span>Schemes Requiring Demographic Verification ({filteredVerification.length})</span>
                </div>
                <p className="text-amber-800 leading-relaxed">
                  You qualify for these programs pending specific documentation (such as income certificate, student enrollment, or landholding document). Visit your{' '}
                  <Link to="/profile" className="font-bold underline text-amber-950">
                    Citizen Profile
                  </Link>{' '}
                  to update parameters.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredVerification.map((scheme) => (
                  <SchemeCard
                    key={scheme.scheme_id || scheme.id}
                    scheme={scheme}
                    isVerificationRequired={true}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
