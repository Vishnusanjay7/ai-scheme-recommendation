import { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Languages,
  Square,
  X,
  Bot,
  ExternalLink,
  ChevronUp,
  RotateCcw,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { sendChatMessage, fetchVoiceTTS } from '../services/api'

const REGIONAL_LANGS = [
  { code: 'ta', label: 'தமிழ் (Tamil)', speechCode: 'ta-IN', name: 'Tamil' },
  { code: 'hi', label: 'हिन्दी (Hindi)', speechCode: 'hi-IN', name: 'Hindi' },
  { code: 'en', label: 'English', speechCode: 'en-IN', name: 'English' },
  { code: 'te', label: 'తెలుగు (Telugu)', speechCode: 'te-IN', name: 'Telugu' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)', speechCode: 'kn-IN', name: 'Kannada' },
  { code: 'ml', label: 'മലയാളം (Malayalam)', speechCode: 'ml-IN', name: 'Malayalam' },
  { code: 'bn', label: 'বাংলা (Bengali)', speechCode: 'bn-IN', name: 'Bengali' },
  { code: 'mr', label: 'मराठी (Marathi)', speechCode: 'mr-IN', name: 'Marathi' },
  { code: 'gu', label: 'ગુજરાતી (Gujarati)', speechCode: 'gu-IN', name: 'Gujarati' },
]

export default function FloatingVoiceAssistant() {
  const location = useLocation()
  const { session } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const [selectedLanguage, setSelectedLanguage] = useState('ta')
  const [isListening, setIsListening] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [autoSpeak, setAutoSpeak] = useState(true)
  const [queryText, setQueryText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [lastResponse, setLastResponse] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  const recognitionRef = useRef(null)
  const audioRef = useRef(null)

  // Don't show floating widget if already on the dedicated /chatbot page
  if (location.pathname === '/chatbot') {
    return null
  }

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
    setIsPlaying(false)
  }

  const playVoice = async (text, langCode) => {
    stopVoice()
    setIsPlaying(true)

    // 1. Try Gemini TTS audio from backend
    try {
      const res = await fetchVoiceTTS(text, langCode || selectedLanguage)
      if (res && res.audioBase64) {
        const audio = new Audio(`data:audio/wav;base64,${res.audioBase64}`)
        audioRef.current = audio
        audio.onended = () => {
          setIsPlaying(false)
          audioRef.current = null
        }
        audio.onerror = () => fallbackSpeech(text, langCode)
        await audio.play()
        return
      }
    } catch {}

    // 2. Web Speech API fallback
    fallbackSpeech(text, langCode)
  }

  const fallbackSpeech = (text, langCode) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      setIsPlaying(false)
      return
    }

    const clean = text.replace(/[*#•_-]/g, ' ').slice(0, 350)
    const utterance = new SpeechSynthesisUtterance(clean)
    const langObj = REGIONAL_LANGS.find((l) => l.code === (langCode || selectedLanguage))
    const code = langObj ? langObj.speechCode : 'ta-IN'
    utterance.lang = code
    utterance.rate = 0.95

    const voices = window.speechSynthesis.getVoices()
    const match = voices.find(
      (v) => v.lang.toLowerCase() === code.toLowerCase() || v.lang.startsWith(langCode || selectedLanguage)
    )
    if (match) utterance.voice = match

    utterance.onend = () => setIsPlaying(false)
    utterance.onerror = () => setIsPlaying(false)

    window.speechSynthesis.speak(utterance)
  }

  const toggleMic = () => {
    if (isListening) {
      if (recognitionRef.current) recognitionRef.current.stop()
      setIsListening(false)
      return
    }

    stopVoice()
    setErrorMsg('')

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setErrorMsg('Voice input is not supported in this browser. Please type or use Chrome/Safari.')
      return
    }

    try {
      const recognition = new SpeechRecognition()
      recognitionRef.current = recognition
      const langObj = REGIONAL_LANGS.find((l) => l.code === selectedLanguage)
      recognition.lang = langObj ? langObj.speechCode : 'ta-IN'
      recognition.continuous = false
      recognition.interimResults = true

      recognition.onstart = () => setIsListening(true)
      recognition.onresult = (event) => {
        let transcript = ''
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript
        }
        setQueryText(transcript)
      }
      recognition.onerror = (event) => {
        if (event.error !== 'no-speech') {
          setErrorMsg(`Microphone error: ${event.error}`)
        }
        setIsListening(false)
      }
      recognition.onend = () => {
        setIsListening(false)
      }

      recognition.start()
    } catch (err) {
      setErrorMsg(`Could not start voice recognition: ${err.message}`)
      setIsListening(false)
    }
  }

  const handleSendQuery = async (customQuery) => {
    const text = (customQuery || queryText).trim()
    if (!text || isProcessing) return

    stopVoice()
    setErrorMsg('')
    setIsProcessing(true)

    try {
      const res = await sendChatMessage(text, session?.access_token || null, selectedLanguage)
      setLastResponse(res)
      setQueryText('')

      if (autoSpeak && res.message) {
        setTimeout(() => {
          playVoice(res.message, res.language || selectedLanguage)
        }, 200)
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to get voice answer.')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end print:hidden">
      {/* Expanded Voice Assistant Dialog */}
      {isOpen && (
        <div className="w-[360px] sm:w-[420px] max-h-[560px] mb-3 bg-white border border-slate-200 rounded-xl shadow-2xl flex flex-col overflow-hidden text-slate-800 animate-in fade-in slide-in-from-bottom-4 duration-150">
          {/* Header */}
          <div className="px-4 py-3 bg-[#07172c] text-white flex items-center justify-between gap-3 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold tracking-tight leading-tight">SchemeSetu Voice</h3>
                <p className="text-[11px] text-slate-300 leading-none mt-0.5">Regional Language Assistant</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  stopVoice()
                  setAutoSpeak(!autoSpeak)
                }}
                className={`p-1.5 rounded transition-colors ${
                  autoSpeak ? 'text-emerald-400 bg-white/10' : 'text-slate-400 hover:text-white'
                }`}
                title={autoSpeak ? 'Auto-Voice Playback is ON' : 'Auto-Voice Playback is MUTED'}
              >
                {autoSpeak ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </button>
              <button
                type="button"
                onClick={() => {
                  stopVoice()
                  setIsOpen(false)
                }}
                className="text-slate-400 hover:text-white p-1 rounded"
                aria-label="Close voice assistant"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Language Selector Bar */}
          <div className="px-3 py-2 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-1.5 text-slate-600 font-medium">
              <Languages className="w-3.5 h-3.5 text-blue-600" />
              <span>Language:</span>
            </div>
            <select
              value={selectedLanguage}
              onChange={(e) => {
                stopVoice()
                setSelectedLanguage(e.target.value)
              }}
              className="px-2 py-1 bg-white border border-slate-300 rounded text-xs font-semibold text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              {REGIONAL_LANGS.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.label}
                </option>
              ))}
            </select>
          </div>

          {/* Content Area */}
          <div className="p-4 flex-1 overflow-y-auto space-y-3 min-h-[220px]">
            {/* If no response yet: Welcome Prompt */}
            {!lastResponse && (
              <div className="text-center py-6 space-y-3">
                <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
                  <Mic className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">Ask via Voice in Your Regional Language</h4>
                  <p className="text-xs text-slate-500 max-w-xs mx-auto mt-1">
                    Press the microphone to ask about farmer subsidies, student scholarships, or women welfare.
                  </p>
                </div>
              </div>
            )}

            {/* Error Message */}
            {errorMsg && (
              <div className="p-2.5 bg-rose-50 border border-rose-200 rounded text-xs text-rose-700">
                {errorMsg}
              </div>
            )}

            {/* Active Response Card */}
            {lastResponse && (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-700 border-b border-slate-200 pb-1.5">
                  <span>Assistant Answer ({REGIONAL_LANGS.find((l) => l.code === lastResponse.language)?.name || 'Answer'})</span>
                  <button
                    type="button"
                    onClick={() => {
                      if (isPlaying) stopVoice()
                      else playVoice(lastResponse.message, lastResponse.language)
                    }}
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                      isPlaying
                        ? 'bg-rose-600 text-white'
                        : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {isPlaying ? <Square className="w-3 h-3" /> : <Volume2 className="w-3 h-3" />}
                    <span>{isPlaying ? 'Stop' : 'Listen'}</span>
                  </button>
                </div>

                <p className="text-xs text-slate-800 leading-relaxed whitespace-pre-line">
                  {lastResponse.message}
                </p>

                {/* Recommendations Carousel / Quick Links */}
                {lastResponse.recommendations && lastResponse.recommendations.length > 0 && (
                  <div className="pt-2 border-t border-slate-200 space-y-1.5">
                    <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wide">
                      Matching Welfare Schemes ({lastResponse.recommendations.length}):
                    </span>
                    <div className="space-y-1">
                      {lastResponse.recommendations.slice(0, 2).map((scheme) => (
                        <div
                          key={scheme.id || scheme.scheme_id}
                          className="p-2 bg-white border border-slate-200 rounded flex items-center justify-between gap-2"
                        >
                          <div className="min-w-0">
                            <h5 className="text-xs font-semibold text-slate-900 truncate">
                              {scheme.scheme_name}
                            </h5>
                            <p className="text-[11px] text-slate-500 truncate">{scheme.benefits}</p>
                          </div>
                          <Link
                            to={`/schemes/${scheme.id || scheme.scheme_id}`}
                            onClick={() => setIsOpen(false)}
                            className="text-xs font-medium text-blue-700 hover:underline shrink-0"
                          >
                            Details →
                          </Link>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Active Listening Visualizer Banner */}
          {isListening && (
            <div className="px-4 py-2 bg-rose-50 border-t border-rose-200 flex items-center justify-between text-xs text-rose-800">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-600 animate-ping" />
                <span className="font-semibold">
                  Listening in {REGIONAL_LANGS.find((l) => l.code === selectedLanguage)?.label}...
                </span>
              </div>
              <button
                type="button"
                onClick={toggleMic}
                className="text-xs font-bold underline hover:text-rose-950"
              >
                Done
              </button>
            </div>
          )}

          {/* Input & Mic Toolbar */}
          <div className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
            <button
              type="button"
              onClick={toggleMic}
              className={`p-2.5 rounded-lg font-medium transition-all ${
                isListening
                  ? 'bg-rose-600 text-white animate-pulse'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
              title={isListening ? 'Stop recording voice query' : 'Click to speak query in regional language'}
              aria-label="Toggle voice input"
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5 text-blue-700" />}
            </button>

            <input
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleSendQuery()
                }
              }}
              placeholder="Speak or type your question..."
              className="flex-1 px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600"
              disabled={isProcessing}
            />

            <button
              type="button"
              onClick={() => handleSendQuery()}
              disabled={isProcessing || !queryText.trim()}
              className="px-3 py-2 bg-[#07172c] hover:bg-slate-800 text-white rounded-lg text-xs font-semibold disabled:opacity-40 transition-colors"
            >
              {isProcessing ? '...' : 'Ask'}
            </button>
          </div>

          {/* Footer Action to Full Chat Page */}
          <div className="px-3 py-1.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
            <span>Powered by SchemeSetu Multilingual AI</span>
            <Link
              to="/chatbot"
              onClick={() => setIsOpen(false)}
              className="font-medium text-blue-700 hover:underline flex items-center gap-1"
            >
              <span>Full Screen Chat</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>
      )}

      {/* Primary Floating Trigger Button */}
      <button
        type="button"
        onClick={() => {
          if (isOpen) stopVoice()
          setIsOpen(!isOpen)
        }}
        className="group flex items-center gap-2 px-4 py-3 bg-[#07172c] hover:bg-slate-800 text-white rounded-full shadow-xl hover:shadow-2xl transition-all duration-150 border border-slate-700/80 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2"
        aria-label="Open Regional Voice Assistant"
      >
        <div className="w-7 h-7 rounded-full bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300 group-hover:scale-105 transition-transform">
          <Mic className="w-4 h-4 text-amber-400" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-xs font-bold tracking-tight text-white flex items-center gap-1">
            Voice Assistant
            <span className="text-[10px] font-normal text-amber-300">தமிழ்/हिन्दी/English</span>
          </span>
          <span className="text-[10px] text-slate-300 font-medium">Ask welfare schemes by voice</span>
        </div>
      </button>
    </div>
  )
}
