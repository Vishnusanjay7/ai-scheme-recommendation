import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Languages,
  Square,
  Sparkles,
  Info,
  Send,
  RotateCcw,
  Bot,
  User,
  ExternalLink,
  Bookmark,
  CheckCircle2,
  AlertTriangle,
  Radio,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { sendChatMessage, fetchChatHistory, fetchVoiceTTS, saveScheme } from '../services/api'

const REGIONAL_LANGUAGES = [
  { code: 'ta', label: 'தமிழ் (Tamil)', speechCode: 'ta-IN', name: 'Tamil', script: 'தமிழ்' },
  { code: 'hi', label: 'हिन्दी (Hindi)', speechCode: 'hi-IN', name: 'Hindi', script: 'हिन्दी' },
  { code: 'en', label: 'English', speechCode: 'en-IN', name: 'English', script: 'English' },
  { code: 'te', label: 'తెలుగు (Telugu)', speechCode: 'te-IN', name: 'Telugu', script: 'తెలుగు' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)', speechCode: 'kn-IN', name: 'Kannada', script: 'ಕನ್ನಡ' },
  { code: 'ml', label: 'മലയാളം (Malayalam)', speechCode: 'ml-IN', name: 'Malayalam', script: 'മലയാളം' },
  { code: 'bn', label: 'বাংলা (Bengali)', speechCode: 'bn-IN', name: 'Bengali', script: 'বাংলা' },
  { code: 'mr', label: 'मराठी (Marathi)', speechCode: 'mr-IN', name: 'Marathi', script: 'मराठी' },
  { code: 'gu', label: 'ગુજરાતી (Gujarati)', speechCode: 'gu-IN', name: 'Gujarati', script: 'ગુજરાતી' },
]

const REGIONAL_QUICK_PROMPTS = {
  ta: [
    { label: '🌾 விவசாயி உதவி திட்டங்கள்', prompt: 'நான் ஒரு விவசாயி. எனக்கு என்ன அரசு உதவி மற்றும் மானிய திட்டங்கள் உள்ளன?' },
    { label: '🎓 கல்லூரி மாணவிகள் உதவி (புதுமைப் பெண்)', prompt: 'கல்லூரி மாணவிகளுக்கான புதுமைப் பெண் மற்றும் கல்வி உதவி திட்டங்கள் என்ன?' },
    { label: '👩 மகளிர் உரிமைத் திட்டம் (KMUT)', prompt: 'கலைஞர் மகளிர் உரிமைத் திட்டம் மற்றும் பெண்களுக்கான திட்டங்களை சொல்லுங்கள்.' },
    { label: '💼 இளைஞர் தொழில் கடன் (UYEGP)', prompt: 'படித்த வேலைவாய்ப்பற்ற இளைஞர்களுக்கான தொழில் கடன் மானிய திட்டம் என்ன?' },
  ],
  hi: [
    { label: '🌾 किसान सम्मान निधि और कृषि सब्सिडी', prompt: 'किसानों के लिए सरकारी सब्सिडी और पीएम किसान योजना की पूरी जानकारी दें।' },
    { label: '🎓 उच्च शिक्षा और छात्रवृत्ति योजनाएं', prompt: 'छात्रों के लिए छात्रवृत्ति और उच्च शिक्षा वित्तीय सहायता योजनाएं क्या हैं?' },
    { label: '🏠 प्रधानमंत्री आवास योजना (PMAY)', prompt: 'प्रधानमंत्री आवास योजना के तहत घर निर्माण के लिए कैसे आवेदन करें?' },
    { label: '👩 महिला स्वयं सहायता और स्वरोजगार', prompt: 'महिलाओं के लिए स्वयं सहायता समूह और व्यवसाय ऋण सहायता योजनाएं बताएं।' },
  ],
  en: [
    { label: '🌾 Farmers Income & Equipment Support', prompt: 'Find welfare and subsidy schemes for small and marginal farmers.' },
    { label: '🎓 Higher Education Scholarships', prompt: 'What education scholarships and monthly stipends am I eligible for?' },
    { label: '👩 Women Welfare & Empowerment', prompt: 'Show welfare schemes for women heads of family and girl children.' },
    { label: '💼 Youth Self-Employment (UYEGP)', prompt: 'What micro-enterprise and business loan subsidies are available for educated youth?' },
  ],
  te: [
    { label: '🌾 రైతు సంక్షేమ పథకాలు & సబ్సిడీలు', prompt: 'రైతుల కోసం అందుబాటులో ఉన్న ముఖ్యమైన ప్రభుత్వ సంక్షేమ పథకాలు ఏమిటి?' },
    { label: '🎓 విద్యార్థి ఉపకార వేతనాలు', prompt: 'విద్యార్థుల కోసం ఉన్న ప్రభుత్వ స్కాలర్‌షిప్ పథకాలను తెలియజేయండి.' },
    { label: '👩 మహిళా సాధికారత పథకాలు', prompt: 'మహిళల కోసం ఉన్న స్వయం ఉపాధి మరియు ఆర్థిక సహాయ పథకాలను చెప్పండి.' },
  ],
  kn: [
    { label: '🌾 ರೈತ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳು & ಸಹಾಯಧನ', prompt: 'ರೈತರಿಗೆ ಲಭ್ಯವಿರುವ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಮತ್ತು ಸಬ್ಸಿಡಿಗಳು ಯಾವುವು?' },
    { label: '🎓 ವಿದ್ಯಾರ್ಥಿವೇತನ ಯೋಜನೆಗಳು', prompt: 'ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಉನ್ನತ ಶಿಕ್ಷಣಕ್ಕಾಗಿ ಇರುವ ಸರ್ಕಾರದ ಯೋಜನೆಗಳನ್ನು ತಿಳಿಸಿ.' },
    { label: '👩 ಮಹಿಳಾ ಸ್ವಯಂ ಉದ್ಯೋಗ ಯೋಜನೆಗಳು', prompt: 'ಮಹಿಳೆಯರಿಗಾಗಿ ಇರುವ ಸ್ವಯಂ ಉದ್ಯೋಗ ಮತ್ತು ಕಲ್ಯಾಣ ಯೋಜನೆಗಳನ್ನು ತಿಳಿಸಿ.' },
  ],
  ml: [
    { label: '🌾 കർഷക ക്ഷേമ പദ്ധതികൾ & സബ്സിഡി', prompt: 'കർഷകർക്കായി ലഭ്യമായ സർക്കാർ ധനസഹായ പദ്ധതികൾ ഏതൊക്കെയാണ്?' },
    { label: '🎓 വിദ്യാർത്ഥി സ്കോളർഷിപ്പുകൾ', prompt: 'വിദ്യാർത്ഥികൾക്കുള്ള സ്കോളർഷിപ്പുകളും വിദ്യാഭ്യാസ സഹായ പദ്ധതികളും അറിയിക്കുക.' },
    { label: '👩 വനിതാ ക്ഷേമ പദ്ധതികൾ', prompt: 'വനിതകൾക്കായി ലഭ്യമായ സർക്കാർ ക്ഷേമ പദ്ധതികളെക്കുറിച്ച് പറയുക.' },
  ],
  bn: [
    { label: '🌾 কৃষক কল্যাণ ও কৃষি ভর্তুকি', prompt: 'কৃষকদের জন্য সরকারি অনুদান ও কৃষক বন্ধু প্রকল্পের বিবরণ দিন।' },
    { label: '🎓 পড়ুয়াদের স্কলারশিপ ও অনুদান', prompt: 'ছাত্রছাত্রীদের জন্য উচ্চশিক্ষার স্কলারশিপ প্রকল্পগুলি কী কী?' },
    { label: '👩 মহিলা স্বনির্ভরতা প্রকল্প', prompt: 'মহিলাদের স্বনির্ভর দল এবং ব্যবসায়িক সহায়তা প্রকল্পগুলি জানান।' },
  ],
  mr: [
    { label: '🌾 शेतकरी सन्मान व कृषी योजना', prompt: 'शेतकऱ्यांसाठी उपलब्ध सरकारी अनुदान व योजनांची माहिती द्या.' },
    { label: '🎓 उच्च शिक्षण शिष्यवृत्ती योजना', prompt: 'विद्यार्थ्यांसाठी उपलब्ध सरकारी शिष्यवृत्ती योजना कोणत्या आहेत?' },
    { label: '👩 महिला सक्षमीकरण व उद्योग योजना', prompt: 'महिलांसाठी स्वयंरोजगार व आर्थिक साहाय्य योजनांची माहिती सांगा.' },
  ],
  gu: [
    { label: '🌾 ખેડૂત કલ્યાણ અને સબસિડી યોજના', prompt: 'ખેડૂતો માટે ઉપલબ્ધ સરકારી યોજનાઓ અને સબસિડીની વિગત આપો.' },
    { label: '🎓 વિદ્યાર્થી શિષ્યવૃત્તિ યોજના', prompt: 'વિદ્યાર્થીઓ માટે ઉપલબ્ધ સરકારી સ્કોલરશિપ યોજનાઓ જણાવો.' },
    { label: '👩 મહિલા આત્મનિર્ભરતા યોજના', prompt: 'મહિલાઓ માટેના સ્વરોજગાર અને કલ્યાણકારી સહાય વિશે જણાવો.' },
  ],
}

const GREETINGS = {
  ta: 'வணக்கம்! நான் SchemeSetu அரசு நலத்திட்ட உதவியாளர். உங்கள் வயது, கல்வி, மாவட்டம், தொழில் மற்றும் வருமான விவரங்களின்படி தகுதியான அரசு திட்டங்களை கண்டறிய உதவ முடியும். நீங்கள் தமிழில் பேசவோ அல்லது தட்டச்சு செய்யவோ முடியும்.',
  hi: 'नमस्ते! मैं SchemeSetu सरकारी कल्याणकारी योजना सहायक हूँ। आपकी आयु, राज्य, पेशा और आय के अनुसार पात्र योजनाओं की जानकारी दे सकता हूँ। आप हिंदी में बोलकर या लिखकर सवाल पूछ सकते हैं।',
  en: 'Welcome! I am SchemeSetu, your official Government Welfare Assistant. I can evaluate your eligibility and find tailored central and state government welfare schemes. You can ask queries by voice or type in any regional language.',
  te: 'నమస్కారం! నేను SchemeSetu ప్రభుత్వ సంక్షేమ సహాయకుడిని. మీ అర్హతలను పరిశీలించి తగిన ప్రభుత్వ పథకాలను సిఫార్సు చేస్తాను. మీరు తెలుగులో మాట్లాడవచ్చు లేదా టైప్ చేయవచ్చు.',
  kn: 'ನಮಸ್ಕಾರ! ನಾನು SchemeSetu ಸರ್ಕಾರದ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳ ಸಹಾಯಕ. ನಿಮ್ಮ ಅರ್ಹತೆಗೆ ತಕ್ಕಂತೆ ಸೂಕ್ತ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು ನಾನು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ. ನೀವು ಧ್ವನಿ ಮೂಲಕ ಮಾತನಾಡಬಹುದು ಅಥವಾ ಟೈಪ್ ಮಾಡಬಹುದು.',
  ml: 'നമസ്കാരം! ഞാൻ SchemeSetu സർക്കാർ ക്ഷേമപദ്ധതി സഹായിയാണ്. നിങ്ങളുടെ യോഗ്യതയ്ക്കനുസരിച്ചുള്ള പദ്ധതികൾ കണ്ടെത്താൻ സഹായിക്കാം. നിങ്ങൾക്ക് ശബ്ദത്തിലൂടെയോ ടൈപ്പ് ചെയ്തോ ചോദിക്കാം.',
  bn: 'নমস্কার! আমি SchemeSetu সরকারি কল্যাণ প্রকল্প সহায়ক। আপনার প্রোফাইল অনুযায়ী যোগ্য সরকারি প্রকল্পগুলি জানাতে পারি। আপনি ভয়েসে বলতে পারেন বা বাংলায় টাইপ করতে পারেন।',
  mr: 'नमस्कार! मी SchemeSetu शासकीय कल्याणकारी योजना सहाय्यक आहे. तुमच्या पात्रतेनुसार शासकीय योजना शोधण्यासाठी मी मदत करू शकतो. तुम्ही आवाजात बोलू शकता किंवा लिहू शकता.',
  gu: 'નમસ્તે! હું SchemeSetu સરકારી કલ્યાણ યોજના સહાયક છું. તમારી પાત્રતા અનુસાર યોજનાઓ શોધવામાં મદદ કરી શકું છું. તમે અવાજ દ્વારા પૂછી શકો છો અથવા ટાઈપ કરી શકો છો.',
}

export default function ChatbotPage() {
  const { session, isAuthenticated } = useAuth()
  const [selectedLanguage, setSelectedLanguage] = useState('ta')
  const [isListening, setIsListening] = useState(false)
  const [speechError, setSpeechError] = useState('')
  const [autoSpeak, setAutoSpeak] = useState(true)
  const [speechSpeed, setSpeechSpeed] = useState(0.95)
  const [playingMessageId, setPlayingMessageId] = useState(null)
  const [savedSchemeIds, setSavedSchemeIds] = useState(new Set())

  const [messages, setMessages] = useState([
    {
      id: 'initial-greeting',
      sender: 'bot',
      text: GREETINGS.ta,
      language: 'ta',
      recommendations: [],
      verification_required: [],
      created_at: new Date().toISOString(),
    },
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [loadingHistory, setLoadingHistory] = useState(false)

  const messagesEndRef = useRef(null)
  const messageCountRef = useRef(1)
  const recognitionRef = useRef(null)
  const currentAudioRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, sending])

  // Change initial greeting if language is changed on an untouched session
  const handleLanguageChange = (newLang) => {
    stopVoiceResponse()
    setSelectedLanguage(newLang)
    if (messages.length === 1 && messages[0].id === 'initial-greeting') {
      setMessages([
        {
          id: 'initial-greeting',
          sender: 'bot',
          text: GREETINGS[newLang] || GREETINGS.en,
          language: newLang,
          recommendations: [],
          verification_required: [],
          created_at: new Date().toISOString(),
        },
      ])
    }
  }

  // Stop active speech playback
  const stopVoiceResponse = () => {
    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause()
        currentAudioRef.current.currentTime = 0
      } catch {}
      currentAudioRef.current = null
    }
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
    setPlayingMessageId(null)
  }

  // Play voice response in regional language
  const playVoiceResponse = async (msg) => {
    if (playingMessageId === msg.id) {
      stopVoiceResponse()
      return
    }

    stopVoiceResponse()
    setPlayingMessageId(msg.id)

    // 1. If message already has Gemini TTS WAV audio base64, play it directly
    if (msg.audioBase64) {
      try {
        const audio = new Audio(`data:audio/wav;base64,${msg.audioBase64}`)
        currentAudioRef.current = audio
        audio.playbackRate = speechSpeed
        audio.onended = () => {
          setPlayingMessageId(null)
          currentAudioRef.current = null
        }
        audio.onerror = () => {
          fallbackSpeechSynthesis(msg)
        }
        await audio.play()
        return
      } catch (err) {
        console.warn('Audio playback error, falling back to speech synthesis:', err)
      }
    }

    // 2. Try fetching TTS audio from server
    try {
      const res = await fetchVoiceTTS(msg.text, msg.language || selectedLanguage)
      if (res && res.audioBase64) {
        msg.audioBase64 = res.audioBase64
        const audio = new Audio(`data:audio/wav;base64,${res.audioBase64}`)
        currentAudioRef.current = audio
        audio.playbackRate = speechSpeed
        audio.onended = () => {
          setPlayingMessageId(null)
          currentAudioRef.current = null
        }
        await audio.play()
        return
      }
    } catch {}

    // 3. Fallback to browser SpeechSynthesis API in regional language
    fallbackSpeechSynthesis(msg)
  }

  const fallbackSpeechSynthesis = (msg) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      setPlayingMessageId(null)
      return
    }

    const cleanText = msg.text
      .replace(/[*#•_-]/g, ' ')
      .replace(/https?:\/\/\S+/g, '')
      .replace(/\s+/g, ' ')
      .trim()

    const utterance = new SpeechSynthesisUtterance(cleanText)
    const langObj = REGIONAL_LANGUAGES.find((l) => l.code === (msg.language || selectedLanguage))
    const speechCode = langObj ? langObj.speechCode : 'ta-IN'
    utterance.lang = speechCode
    utterance.rate = speechSpeed

    const voices = window.speechSynthesis.getVoices()
    const targetVoice = voices.find(
      (v) => v.lang.toLowerCase() === speechCode.toLowerCase() || v.lang.startsWith(msg.language || selectedLanguage)
    )
    if (targetVoice) {
      utterance.voice = targetVoice
    }

    utterance.onend = () => {
      setPlayingMessageId(null)
    }
    utterance.onerror = () => {
      setPlayingMessageId(null)
    }

    window.speechSynthesis.speak(utterance)
  }

  // Web Speech API Voice Recognition (Speech-to-Text in Regional Language)
  const toggleSpeechRecognition = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
      setIsListening(false)
      return
    }

    setSpeechError('')
    stopVoiceResponse()

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      setSpeechError(
        'Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari to use microphone input.'
      )
      return
    }

    try {
      const recognition = new SpeechRecognition()
      recognitionRef.current = recognition
      const langObj = REGIONAL_LANGUAGES.find((l) => l.code === selectedLanguage)
      recognition.lang = langObj ? langObj.speechCode : 'ta-IN'
      recognition.continuous = false
      recognition.interimResults = true

      recognition.onstart = () => {
        setIsListening(true)
      }

      recognition.onresult = (event) => {
        let transcript = ''
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript
        }
        setInputMessage(transcript)
      }

      recognition.onerror = (event) => {
        if (event.error !== 'no-speech') {
          setSpeechError(`Voice error: ${event.error}. Please try speaking again.`)
        }
        setIsListening(false)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognition.start()
    } catch (err) {
      setSpeechError('Could not start voice recognition: ' + err.message)
      setIsListening(false)
    }
  }

  // Load authenticated citizen chat history
  useEffect(() => {
    let isMounted = true

    async function loadHistory() {
      if (!isAuthenticated || !session?.access_token) return
      setLoadingHistory(true)
      try {
        const res = await fetchChatHistory(session.access_token, 20)
        if (isMounted && res && res.history && res.history.length > 0) {
          const historicalMessages = []
          const sorted = [...res.history].reverse()
          sorted.forEach((item) => {
            historicalMessages.push({
              id: `user-${item.id}`,
              sender: 'user',
              text: item.user_message,
              created_at: item.created_at,
            })
            historicalMessages.push({
              id: `bot-${item.id}`,
              sender: 'bot',
              text: item.bot_response,
              language: item.language,
              recommendations: [],
              verification_required: [],
              created_at: item.created_at,
            })
          })
          setMessages((prev) => [prev[0], ...historicalMessages])
        }
      } catch {
      } finally {
        if (isMounted) setLoadingHistory(false)
      }
    }

    loadHistory()
    return () => {
      isMounted = false
      stopVoiceResponse()
    }
  }, [isAuthenticated, session?.access_token])

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputMessage).trim()
    if (!text || sending) return

    stopVoiceResponse()
    setErrorMsg('')
    setSpeechError('')
    const count = messageCountRef.current++
    const userMsg = {
      id: `user-msg-${count}`,
      sender: 'user',
      text,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInputMessage('')
    setSending(true)

    try {
      const token = session?.access_token || null
      const response = await sendChatMessage(text, token, selectedLanguage)

      const botCount = messageCountRef.current++
      const botMsg = {
        id: `bot-msg-${botCount}`,
        sender: 'bot',
        text: response.message,
        language: response.language || selectedLanguage,
        audioBase64: response.audioBase64 || null,
        intent: response.intent,
        recommendations: response.recommendations || [],
        verification_required: response.verification_required || [],
        created_at: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, botMsg])

      // Auto-speak response if enabled
      if (autoSpeak) {
        setTimeout(() => {
          playVoiceResponse(botMsg)
        }, 300)
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to process message. Please try again.')
    } finally {
      setSending(false)
    }
  }

  const handleBookmarkScheme = async (schemeId) => {
    if (!session?.access_token) return
    try {
      await saveScheme(schemeId, session.access_token)
      setSavedSchemeIds((prev) => new Set([...prev, schemeId]))
    } catch (err) {
      console.warn('Bookmark failed:', err)
    }
  }

  const handleResetChat = () => {
    stopVoiceResponse()
    setMessages([
      {
        id: `initial-greeting-${Date.now()}`,
        sender: 'bot',
        text: GREETINGS[selectedLanguage] || GREETINGS.en,
        language: selectedLanguage,
        recommendations: [],
        verification_required: [],
        created_at: new Date().toISOString(),
      },
    ])
  }

  const activeQuickPrompts =
    REGIONAL_QUICK_PROMPTS[selectedLanguage] || REGIONAL_QUICK_PROMPTS.en

  const currentLangObj =
    REGIONAL_LANGUAGES.find((l) => l.code === selectedLanguage) || REGIONAL_LANGUAGES[0]

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      {/* Editorial Header Banner */}
      <div className="bg-[#07172c] text-white rounded-xl p-5 sm:p-6 shadow-md border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">
                National Citizen Voice AI
              </span>
              <span className="text-slate-400">·</span>
              <span className="text-xs text-slate-300">9 Official Regional Languages</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              Multilingual Scheme Assistant
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Ask questions by voice in your native regional language. SchemeSetu evaluates statutory criteria and answers with spoken voice synthesis and verified benefit links.
            </p>
          </div>

          {/* Controls: Audio Toggle & Reset */}
          <div className="flex items-center gap-2 shrink-0 self-start md:self-center">
            <button
              type="button"
              onClick={() => {
                if (autoSpeak) stopVoiceResponse()
                setAutoSpeak(!autoSpeak)
              }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                autoSpeak
                  ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                  : 'bg-white/10 text-slate-300 hover:bg-white/20'
              }`}
              title={autoSpeak ? 'Auto-voice response is ON' : 'Auto-voice response is MUTED'}
            >
              {autoSpeak ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
              <span>{autoSpeak ? 'Voice Enabled' : 'Voice Muted'}</span>
            </button>

            {/* Speech Rate Cycle */}
            <button
              type="button"
              onClick={() => {
                const nextSpeed = speechSpeed === 0.95 ? 1.15 : speechSpeed === 1.15 ? 0.8 : 0.95
                setSpeechSpeed(nextSpeed)
              }}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-white/10 hover:bg-white/20 text-slate-300 transition-colors tabular-nums"
              title="Voice Speech Speed"
            >
              {speechSpeed === 0.95 ? '1.0x Speed' : speechSpeed === 1.15 ? '1.2x Speed' : '0.8x Speed'}
            </button>

            <button
              type="button"
              onClick={handleResetChat}
              className="p-1.5 rounded-lg text-xs font-medium bg-white/10 hover:bg-white/20 text-slate-300 transition-colors"
              title="Reset Conversation"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Regional Language Interactive Pill Bar */}
        <div className="mt-5 pt-4 border-t border-white/10">
          <div className="flex items-center gap-2 mb-2 text-xs font-medium text-slate-300">
            <Languages className="w-3.5 h-3.5 text-amber-400" />
            <span>Select Your Preferred Regional Language:</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {REGIONAL_LANGUAGES.map((lang) => {
              const isActive = selectedLanguage === lang.code
              return (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => handleLanguageChange(lang.code)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-amber-400 text-slate-950 font-bold shadow-sm ring-2 ring-white/30'
                      : 'bg-white/10 text-slate-200 hover:bg-white/20 hover:text-white'
                  }`}
                >
                  <span>{lang.script}</span>
                  <span className="opacity-75 text-[10px] ml-1">({lang.name})</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col">
        {/* Messages Stream Container */}
        <div
          className="p-4 sm:p-6 space-y-4 max-h-[600px] min-h-[380px] overflow-y-auto"
          role="log"
          aria-live="polite"
        >
          {loadingHistory && (
            <div className="text-center py-2 text-xs text-slate-500">
              Loading verified conversation history...
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'bot' && (
                <div className="w-8 h-8 rounded-lg bg-[#07172c] text-amber-400 flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-xl p-4 text-xs sm:text-sm leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-[#07172c] text-white rounded-tr-none'
                    : 'bg-slate-50 border border-slate-200 text-slate-900 rounded-tl-none shadow-sm'
                }`}
              >
                {/* Bot Message Header: Voice Player Bar */}
                {msg.sender === 'bot' && (
                  <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-slate-200/80 text-xs">
                    <div className="flex items-center gap-1.5 text-slate-600 font-medium">
                      <span>SchemeSetu Voice Guidance</span>
                      <span className="text-slate-400">·</span>
                      <span className="text-[11px] text-slate-500">
                        {REGIONAL_LANGUAGES.find((l) => l.code === (msg.language || selectedLanguage))?.name || 'Regional'}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => playVoiceResponse(msg)}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold transition-colors ${
                        playingMessageId === msg.id
                          ? 'bg-rose-600 text-white'
                          : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 hover:text-slate-950'
                      }`}
                      title={playingMessageId === msg.id ? 'Stop voice playback' : 'Listen to voice in regional language'}
                    >
                      {playingMessageId === msg.id ? (
                        <>
                          <Square className="w-3 h-3 fill-current" />
                          <span>Stop Voice</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3.5 h-3.5 text-blue-700" />
                          <span>Listen Voice</span>
                        </>
                      )}
                    </button>
                  </div>
                )}

                {/* Animated Speech Equalizer Bar when actively speaking */}
                {playingMessageId === msg.id && (
                  <div className="flex items-center justify-between p-2 mb-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs font-medium animate-pulse">
                    <div className="flex items-center gap-2">
                      <Radio className="w-3.5 h-3.5 text-emerald-600 animate-spin" />
                      <span>Speaking aloud in {REGIONAL_LANGUAGES.find((l) => l.code === (msg.language || selectedLanguage))?.label}...</span>
                    </div>
                    <div className="flex items-center gap-0.5 h-3">
                      <span className="w-0.5 h-3 bg-emerald-600 animate-pulse" />
                      <span className="w-0.5 h-2 bg-emerald-600 animate-pulse delay-75" />
                      <span className="w-0.5 h-3.5 bg-emerald-600 animate-pulse delay-150" />
                      <span className="w-0.5 h-2 bg-emerald-600 animate-pulse delay-100" />
                    </div>
                  </div>
                )}

                {/* Body Text */}
                <p className="whitespace-pre-line text-slate-800 font-normal">{msg.text}</p>

                {/* Embedded Scheme Recommendation Cards */}
                {msg.recommendations && msg.recommendations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-200 space-y-2">
                    <div className="flex items-center gap-1 text-xs font-bold text-emerald-800 uppercase tracking-wider">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Verified Eligible Schemes ({msg.recommendations.length})</span>
                    </div>

                    <div className="grid grid-cols-1 gap-2">
                      {msg.recommendations.map((scheme) => {
                        const schemeId = scheme.id || scheme.scheme_id || scheme.slug
                        const isSaved = savedSchemeIds.has(schemeId)
                        return (
                          <div
                            key={schemeId}
                            className="p-3 bg-white border border-slate-200 rounded-lg space-y-2 shadow-xs"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <h4 className="text-xs sm:text-sm font-bold text-slate-900 leading-snug">
                                {scheme.scheme_name}
                              </h4>
                              {scheme.match_score !== undefined && (
                                <span className="text-[11px] font-mono tabular-nums font-semibold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200 shrink-0">
                                  {scheme.match_score}% Match
                                </span>
                              )}
                            </div>

                            {scheme.benefits && (
                              <p className="text-xs text-slate-600 line-clamp-2">
                                <strong className="text-slate-800">Benefit:</strong> {scheme.benefits}
                              </p>
                            )}

                            <div className="flex items-center justify-between pt-1 text-xs gap-2">
                              <div className="flex items-center gap-2">
                                <Link
                                  to={`/schemes/${schemeId}`}
                                  className="font-semibold text-blue-700 hover:text-blue-900 hover:underline"
                                >
                                  View Details →
                                </Link>
                                {isAuthenticated && (
                                  <button
                                    type="button"
                                    onClick={() => handleBookmarkScheme(schemeId)}
                                    className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded border ${
                                      isSaved
                                        ? 'bg-amber-50 border-amber-300 text-amber-800'
                                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                                    }`}
                                  >
                                    <Bookmark className="w-3 h-3" />
                                    <span>{isSaved ? 'Saved' : 'Save'}</span>
                                  </button>
                                )}
                              </div>

                              {scheme.official_url && (
                                <a
                                  href={scheme.official_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#07172c] hover:bg-slate-800 text-white rounded font-medium text-xs transition-colors"
                                >
                                  <span>Apply Officially</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* Verification Required Alert */}
                {msg.verification_required && msg.verification_required.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-200 space-y-2">
                    <div className="flex items-center gap-1 text-xs font-bold text-amber-800 uppercase tracking-wider">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                      <span>Criteria Verification Needed ({msg.verification_required.length})</span>
                    </div>
                    <div className="p-2.5 bg-amber-50/70 border border-amber-200 rounded-lg text-xs text-amber-900 space-y-1">
                      <p>
                        Some schemes require confirming your income certificate or district residency before legal eligibility is finalized.
                      </p>
                      <Link
                        to="/profile"
                        className="font-bold underline text-amber-900 hover:text-amber-950 inline-block"
                      >
                        Complete Profile Details →
                      </Link>
                    </div>
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-lg bg-[#07172c] text-amber-400 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-xl rounded-tl-none p-3.5 text-xs text-slate-600 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
                <span>
                  Synthesizing verified welfare response in {currentLangObj.name}...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Live Speech Recognition Waveform Banner */}
        {isListening && (
          <div className="px-4 py-3 bg-rose-50 border-t border-b border-rose-200 flex items-center justify-between text-xs text-rose-900">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <span className="w-1 h-3 bg-rose-600 animate-pulse" />
                <span className="w-1 h-5 bg-rose-600 animate-pulse delay-75" />
                <span className="w-1 h-2 bg-rose-600 animate-pulse delay-150" />
                <span className="w-1 h-6 bg-rose-600 animate-pulse delay-100" />
                <span className="w-1 h-3 bg-rose-600 animate-pulse delay-200" />
              </div>
              <div>
                <span className="font-bold">
                  Listening in {currentLangObj.label}...
                </span>
                <span className="text-rose-700 ml-1.5 hidden sm:inline">
                  Speak your question naturally into the microphone.
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={toggleSpeechRecognition}
              className="px-2.5 py-1 bg-rose-600 text-white rounded text-xs font-semibold hover:bg-rose-700 transition-colors"
            >
              Stop Mic
            </button>
          </div>
        )}

        {/* Error / Feedback Bar */}
        {(speechError || errorMsg) && (
          <div className="px-4 py-2.5 bg-rose-50 border-t border-rose-200 flex items-center justify-between text-xs text-rose-800">
            <span>{speechError || errorMsg}</span>
            <button
              type="button"
              onClick={() => {
                setErrorMsg('')
                setSpeechError('')
              }}
              className="font-bold underline text-rose-900"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Quick Regional Voice Prompt Chips */}
        <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-200 flex items-center gap-2 overflow-x-auto text-xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider shrink-0">
            Suggested Prompts:
          </span>
          <div className="flex gap-1.5 shrink-0">
            {activeQuickPrompts.map((qp, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendMessage(qp.prompt)}
                disabled={sending}
                className="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-300 rounded text-xs text-slate-700 font-medium whitespace-nowrap transition-colors disabled:opacity-50"
              >
                {qp.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar with Voice Input (Mic) & Send */}
        <form onSubmit={(e) => { e.preventDefault(); handleSendMessage() }} className="p-3 sm:p-4 bg-white border-t border-slate-200 flex items-center gap-2">
          {/* Microphone Voice Button */}
          <button
            type="button"
            onClick={toggleSpeechRecognition}
            disabled={sending}
            className={`p-3 rounded-xl font-medium transition-all shrink-0 ${
              isListening
                ? 'bg-rose-600 text-white ring-4 ring-rose-200 animate-pulse'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300'
            }`}
            title={isListening ? 'Stop recording voice' : `Click to Speak in ${currentLangObj.label}`}
            aria-label="Toggle regional voice input"
          >
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5 text-blue-700" />}
          </button>

          {/* Text Input */}
          <input
            type="text"
            className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
            placeholder={
              selectedLanguage === 'ta'
                ? 'குரல் வழியே கேட்க மைக் அழுத்தவும் அல்லது தமிழில் தட்டச்சு செய்யவும்...'
                : selectedLanguage === 'hi'
                ? 'आवाज में पूछने के लिए माइक दबाएं या हिंदी में लिखें...'
                : selectedLanguage === 'te'
                ? 'వాయిస్ ద్వారా అడగడానికి మైక్ నొక్కండి లేదా తెలుగులో టైప్ చేయండి...'
                : `Ask a welfare query by voice or type in ${currentLangObj.name}...`
            }
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={sending}
            maxLength={2000}
            autoComplete="off"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={sending || !inputMessage.trim()}
            className="px-4 py-2.5 bg-[#07172c] hover:bg-slate-800 disabled:opacity-40 text-white rounded-xl text-xs sm:text-sm font-semibold transition-colors flex items-center gap-1.5 shrink-0"
          >
            <span>Ask</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Footer Disclaimer */}
        <div className="px-4 py-2 bg-slate-50 border-t border-slate-200 text-[11px] text-slate-500 flex items-center gap-1.5">
          <Info className="w-3 h-3 text-slate-400 shrink-0" />
          <span>
            SchemeSetu AI Assistant evaluates statutory guidelines deterministically. Applications must be submitted through verified state and central portals.
          </span>
        </div>
      </div>
    </div>
  )
}
