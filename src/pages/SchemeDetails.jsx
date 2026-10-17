import { useEffect, useState, useRef } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Building2,
  Calendar,
  ExternalLink,
  Bookmark,
  ArrowLeft,
  Volume2,
  Square,
  FileCheck2,
  FileText,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Languages,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import {
  checkSchemeSaved,
  fetchSchemeDetails,
  removeSavedScheme,
  saveScheme,
  fetchVoiceTTS,
} from '../services/api'
import DeadlineBadge from '../components/DeadlineBadge'
import DocumentRequirementBadge from '../components/DocumentRequirementBadge'

const REGIONAL_SPEECH_OPTIONS = [
  { code: 'ta', label: 'தமிழ் (Tamil)', speechCode: 'ta-IN' },
  { code: 'hi', label: 'हिन्दी (Hindi)', speechCode: 'hi-IN' },
  { code: 'en', label: 'English', speechCode: 'en-IN' },
  { code: 'te', label: 'తెలుగు (Telugu)', speechCode: 'te-IN' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)', speechCode: 'kn-IN' },
  { code: 'ml', label: 'മലയാളം (Malayalam)', speechCode: 'ml-IN' },
]

export default function SchemeDetails() {
  const { id } = useParams()
  const { session, isAuthenticated } = useAuth()

  const [scheme, setScheme] = useState(null)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [isSaved, setIsSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveFeedback, setSaveFeedback] = useState('')

  // Regional Voice Readout State
  const [voiceLang, setVoiceLang] = useState('ta')
  const [isPlayingVoice, setIsPlayingVoice] = useState(false)
  const audioRef = useRef(null)

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
          } catch {}
        }
      } catch (err) {
        if (isMounted) {
          setErrorMsg(err.message || 'Scheme details could not be loaded.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadScheme()
    return () => {
      isMounted = false
      stopVoice()
    }
  }, [id, isAuthenticated, session])

  const stopVoice = () => {
    if (audioRef.current) {
      try {
        audioRef.current.pause()
        audioRef.current.currentTime = 0
      } catch {}
      audioRef.current = null
    }
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
    setIsPlayingVoice(false)
  }

  const handlePlayVoiceSummary = async () => {
    if (isPlayingVoice) {
      stopVoice()
      return
    }

    if (!scheme) return
    setIsPlayingVoice(true)

    const textToSpeak = `${scheme.scheme_name}. ${scheme.description || ''}. Key Benefits: ${scheme.benefits || ''}.`

    // 1. Try server Gemini TTS
    try {
      const res = await fetchVoiceTTS(textToSpeak, voiceLang)
      if (res && res.audioBase64) {
        const audio = new Audio(`data:audio/wav;base64,${res.audioBase64}`)
        audioRef.current = audio
        audio.onended = () => {
          setIsPlayingVoice(false)
          audioRef.current = null
        }
        audio.onerror = () => fallbackReadout(textToSpeak)
        await audio.play()
        return
      }
    } catch {}

    // 2. Browser Web Speech fallback
    fallbackReadout(textToSpeak)
  }

  const fallbackReadout = (text) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      setIsPlayingVoice(false)
      return
    }

    const clean = text.replace(/[*#•_-]/g, ' ').slice(0, 400)
    const utterance = new SpeechSynthesisUtterance(clean)
    const langObj = REGIONAL_SPEECH_OPTIONS.find((l) => l.code === voiceLang)
    const code = langObj ? langObj.speechCode : 'ta-IN'
    utterance.lang = code
    utterance.rate = 0.95

    const voices = window.speechSynthesis.getVoices()
    const match = voices.find(
      (v) => v.lang.toLowerCase() === code.toLowerCase() || v.lang.startsWith(voiceLang)
    )
    if (match) utterance.voice = match

    utterance.onend = () => setIsPlayingVoice(false)
    utterance.onerror = () => setIsPlayingVoice(false)

    window.speechSynthesis.speak(utterance)
  }

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
        setSaveFeedback('Removed from saved bookmarks')
      } else {
        await saveScheme(id, session.access_token)
        setIsSaved(true)
        setSaveFeedback('Saved to your bookmarks!')
      }
    } catch (err) {
      setSaveFeedback(err.message || 'Action failed')
    } finally {
      setSaving(false)
      setTimeout(() => setSaveFeedback(''), 2500)
    }
  }

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-3 border-slate-300 border-t-blue-700 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500">Loading statutory scheme guidelines...</p>
      </div>
    )
  }

  if (errorMsg || !scheme) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 max-w-lg mx-auto text-center space-y-3">
        <h2 className="text-base font-bold text-slate-900">Scheme Not Found</h2>
        <p className="text-xs text-slate-600">{errorMsg || 'The requested scheme could not be retrieved.'}</p>
        <Link
          to="/recommendations"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-bold"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Recommendations</span>
        </Link>
      </div>
    )
  }

  const activity = scheme.activity || {}
  const officialUrl = scheme.official_url || scheme.source_url
  const documents = scheme.documents || []

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb Trail */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Link to="/recommendations" className="hover:text-slate-900 font-medium">
          Recommendations
        </Link>
        <span>/</span>
        <span className="text-slate-900 font-semibold truncate max-w-md">{scheme.scheme_name}</span>
      </div>

      {/* Main Dossier Header Banner */}
      <div className="bg-[#07172c] text-white rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center gap-2 flex-wrap text-xs font-semibold">
          <span className="text-amber-400 uppercase tracking-wider">
            {scheme.government_level === 'CENTRAL' ? 'Central Ministry Scheme' : 'State Welfare Scheme'}
          </span>
          <span className="text-slate-500">·</span>
          <span className="text-slate-300">
            {scheme.state_name || (scheme.government_level === 'CENTRAL' ? 'All India' : 'Tamil Nadu')}
          </span>
          {scheme.category && (
            <>
              <span className="text-slate-500">·</span>
              <span className="text-slate-300">{scheme.category}</span>
            </>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white leading-tight">
          {scheme.scheme_name}
        </h1>

        {scheme.description && (
          <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
            {scheme.description}
          </p>
        )}

        {/* Voice Readout Toolbar */}
        <div className="pt-2 flex flex-wrap items-center gap-2 sm:gap-3 border-t border-white/10">
          <div className="flex items-center gap-1.5 text-xs text-slate-300">
            <Languages className="w-4 h-4 text-amber-400" />
            <span>Spoken Voice Readout:</span>
          </div>

          <select
            value={voiceLang}
            onChange={(e) => {
              stopVoice()
              setVoiceLang(e.target.value)
            }}
            className="px-2.5 py-1 bg-white/10 border border-white/20 rounded text-xs font-medium text-white focus:outline-none"
          >
            {REGIONAL_SPEECH_OPTIONS.map((opt) => (
              <option key={opt.code} value={opt.code} className="bg-slate-900 text-white">
                {opt.label}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={handlePlayVoiceSummary}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-bold transition-colors ${
              isPlayingVoice
                ? 'bg-rose-600 text-white hover:bg-rose-700'
                : 'bg-amber-400 hover:bg-amber-500 text-slate-950 shadow-sm'
            }`}
          >
            {isPlayingVoice ? (
              <>
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Stop Voice</span>
              </>
            ) : (
              <>
                <Volume2 className="w-3.5 h-3.5" />
                <span>Listen in Regional Voice</span>
              </>
            )}
          </button>
        </div>

        {/* Action Buttons: Apply, Bookmark */}
        <div className="pt-2 flex flex-wrap items-center gap-3">
          {officialUrl ? (
            <a
              href={officialUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2.5 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold rounded-xl text-xs sm:text-sm transition-all shadow-md flex items-center gap-2"
            >
              <span>Apply on Official Portal</span>
              <ExternalLink className="w-4 h-4" />
            </a>
          ) : (
            <span className="text-xs text-slate-400">Official online link not listed</span>
          )}

          {isAuthenticated && (
            <button
              type="button"
              onClick={handleToggleSave}
              disabled={saving}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all flex items-center gap-2 border ${
                isSaved
                  ? 'bg-white text-slate-900 border-white'
                  : 'bg-white/10 text-white hover:bg-white/20 border-white/20'
              }`}
            >
              <Bookmark className="w-4 h-4" />
              <span>{isSaved ? 'Saved in Bookmarks' : 'Save Scheme'}</span>
            </button>
          )}

          <Link
            to="/recommendations"
            className="px-4 py-2.5 text-xs sm:text-sm font-medium text-slate-300 hover:text-white"
          >
            ← Back to Recommendations
          </Link>
        </div>

        {saveFeedback && (
          <div className="text-xs font-semibold text-emerald-400">
            {saveFeedback}
          </div>
        )}
      </div>

      {/* Grid: Scheme Details & Requirements */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Benefits, Procedure, Documents */}
        <div className="lg:col-span-2 space-y-6">
          {/* Key Benefits Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs space-y-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span className="text-lg">🎁</span>
              <span>Statutory Welfare Benefits</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal">
              {scheme.benefits || 'Financial disbursements, welfare allowances, or asset subsidies provided as per departmental norms.'}
            </p>
          </div>

          {/* Application Procedure Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs space-y-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span className="text-lg">📋</span>
              <span>Application Procedure & Verification</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed whitespace-pre-line font-normal">
              {scheme.application_procedure ||
                '1. Visit the verified official ministry or state department portal.\n2. Register citizen account with Aadhaar number and OTP verification.\n3. Fill in demographic eligibility details and upload certified documents.\n4. Link your Aadhaar-seeded bank account for Direct Benefit Transfer (DBT) disbursement.'}
            </p>
          </div>

          {/* Mandatory Documents Checklist */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileCheck2 className="w-5 h-5 text-blue-700" />
                <span>Required Documentation Checklist</span>
              </h2>
              <span className="text-xs font-mono tabular-nums text-slate-500">
                {documents.length} Records Verified
              </span>
            </div>

            {documents.length > 0 ? (
              <div className="space-y-3">
                {documents.map((doc, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-xs sm:text-sm font-bold text-slate-900">
                        {doc.document_name}
                      </h4>
                      <DocumentRequirementBadge doc={doc} />
                    </div>
                    {doc.description && (
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {doc.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">
                Standard identity documentation required: Aadhaar Card, Resident Certificate, Income Certificate, and Bank Account Passbook.
              </p>
            )}
          </div>
        </div>

        {/* Right Sidebar: Timeline & Verification Metadata */}
        <div className="space-y-6">
          {/* Timeline Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-slate-500">
              Application Timeline
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Registration Status</span>
                <span className="font-bold text-slate-900">
                  {activity.status ? activity.status.replace(/_/g, ' ') : 'ACTIVE'}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Application Deadline</span>
                <span className="font-bold text-slate-900 font-mono tabular-nums">
                  {scheme.last_date || 'Rolling / No Closing Deadline'}
                </span>
              </div>

              {activity.days_remaining !== null && activity.days_remaining !== undefined && (
                <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Days Remaining</span>
                  <span className="font-mono tabular-nums font-bold text-amber-700">
                    {activity.days_remaining} Days
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-500">Official Timezone</span>
                <span className="font-medium text-slate-800">IST (UTC+05:30)</span>
              </div>
            </div>
          </div>

          {/* Verification Authority Card */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 space-y-3 text-xs text-slate-700">
            <div className="flex items-center gap-2 font-bold text-slate-900">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Direct Benefit Transfer Mandate</span>
            </div>
            <p className="leading-relaxed text-slate-600">
              Government subsidies and grants are deposited directly into bank accounts linked with Aadhaar. Never pay intermediaries or agents for government welfare benefits.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
