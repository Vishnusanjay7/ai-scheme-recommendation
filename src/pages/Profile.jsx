import { useEffect, useState } from 'react'
import { CheckCircle2, AlertCircle, User, ShieldCheck } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { fetchDistricts, fetchProfile, fetchStates, saveProfile } from '../services/api'

export default function Profile() {
  const { user, token } = useAuth()

  const [states, setStates] = useState([])
  const [districts, setDistricts] = useState([])
  const [loadingDistricts, setLoadingDistricts] = useState(false)

  const [fullName, setFullName] = useState('')
  const [age, setAge] = useState('')
  const [gender, setGender] = useState('')
  const [stateId, setStateId] = useState('')
  const [districtId, setDistrictId] = useState('')
  const [annualIncome, setAnnualIncome] = useState('')
  const [occupation, setOccupation] = useState('')
  const [education, setEducation] = useState('')
  const [category, setCategory] = useState('')
  const [disabilityStatus, setDisabilityStatus] = useState(false)

  const [pageLoading, setPageLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  useEffect(() => {
    let isMounted = true

    async function initializeProfile() {
      setPageLoading(true)
      setErrorMsg('')
      try {
        const statesData = await fetchStates()
        if (isMounted) setStates(statesData || [])

        if (token) {
          try {
            const currentProfile = await fetchProfile(token)
            if (isMounted && currentProfile) {
              setFullName(currentProfile.full_name || user?.user_metadata?.full_name || '')
              setAge(currentProfile.age !== null && currentProfile.age !== undefined ? currentProfile.age : '')
              setGender(currentProfile.gender || '')
              setStateId(currentProfile.state_id ? String(currentProfile.state_id) : '')
              setDistrictId(currentProfile.district_id ? String(currentProfile.district_id) : '')
              setAnnualIncome(
                currentProfile.annual_income !== null && currentProfile.annual_income !== undefined
                  ? currentProfile.annual_income
                  : ''
              )
              setOccupation(currentProfile.occupation || '')
              setEducation(currentProfile.education || '')
              setCategory(currentProfile.category || '')
              setDisabilityStatus(Boolean(currentProfile.disability_status))

              if (currentProfile.state_id) {
                const dists = await fetchDistricts(currentProfile.state_id)
                if (isMounted) setDistricts(dists || [])
              }
            }
          } catch (profileErr) {
            if (isMounted) {
              setFullName(user?.user_metadata?.full_name || '')
            }
          }
        }
      } catch (err) {
        if (isMounted) setErrorMsg('Failed to load profile reference data: ' + err.message)
      } finally {
        if (isMounted) setPageLoading(false)
      }
    }

    initializeProfile()
    return () => {
      isMounted = false
    }
  }, [token, user])

  const handleStateChange = async (newStateId) => {
    setStateId(newStateId)
    setDistrictId('')
    setDistricts([])

    if (!newStateId) return

    setLoadingDistricts(true)
    try {
      const dists = await fetchDistricts(Number(newStateId))
      setDistricts(dists || [])
    } catch (err) {
      console.error('Failed to load districts:', err)
    } finally {
      setLoadingDistricts(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')

    const parsedAge = age !== '' ? parseInt(age, 10) : null
    if (parsedAge !== null && (isNaN(parsedAge) || parsedAge < 0 || parsedAge > 150)) {
      setErrorMsg('Please enter a valid age between 0 and 150.')
      return
    }

    const parsedIncome = annualIncome !== '' ? parseFloat(annualIncome) : null
    if (parsedIncome !== null && (isNaN(parsedIncome) || parsedIncome < 0)) {
      setErrorMsg('Annual income must be a non-negative number.')
      return
    }

    const payload = {
      full_name: fullName.trim() || null,
      age: parsedAge,
      gender: gender || null,
      state_id: stateId ? parseInt(stateId, 10) : null,
      district_id: districtId ? parseInt(districtId, 10) : null,
      annual_income: parsedIncome,
      occupation: occupation || null,
      education: education || null,
      category: category || null,
      disability_status: Boolean(disabilityStatus),
    }

    setSubmitting(true)
    try {
      await saveProfile(payload, token)
      setSuccessMsg('Your citizen profile has been saved successfully! Scheme qualification rules are now updated.')
    } catch (err) {
      setErrorMsg(err.message || 'Failed to save profile. Please check your connection and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (pageLoading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-3 border-slate-300 border-t-blue-700 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500">Loading citizen profile parameters...</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-[#07172c] text-white rounded-xl p-6 sm:p-8 border border-slate-800 shadow-md space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
          <span>Statutory Eligibility Parameters</span>
          <span className="text-slate-400">·</span>
          <span className="text-slate-300">Confidential Matching</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Citizen Demographic Profile
        </h1>
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-xl">
          Provide your demographic details to receive strictly verified, legally qualified government scheme recommendations. Information is never shared with third parties.
        </p>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 shadow-xs space-y-6">
        {/* Identity & Account */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-200">
            Identity & Account Information
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label htmlFor="fullName" className="block text-xs font-semibold text-slate-700">
                Full Legal Name
              </label>
              <input
                id="fullName"
                type="text"
                placeholder="e.g. Priya Sharma"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={submitting}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="userEmail" className="block text-xs font-semibold text-slate-700">
                Account Email
              </label>
              <input
                id="userEmail"
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-3.5 py-2 bg-slate-100 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-500 cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        {/* Demographics & Residency */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-200">
            Demographics & Residency
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label htmlFor="age" className="block text-xs font-semibold text-slate-700">
                Age (Years)
              </label>
              <input
                id="age"
                type="number"
                min="0"
                max="150"
                placeholder="e.g. 24"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                disabled={submitting}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="gender" className="block text-xs font-semibold text-slate-700">
                Gender
              </label>
              <select
                id="gender"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                disabled={submitting}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white"
              >
                <option value="">Select Gender</option>
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="TRANSGENDER">Transgender</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label htmlFor="stateId" className="block text-xs font-semibold text-slate-700">
                Resident State / UT
              </label>
              <select
                id="stateId"
                value={stateId}
                onChange={(e) => handleStateChange(e.target.value)}
                disabled={submitting}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white"
              >
                <option value="">Select State / UT (Pan-India)</option>
                {states.map((st) => (
                  <option key={st.id} value={st.id}>
                    {st.name} ({st.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label htmlFor="districtId" className="block text-xs font-semibold text-slate-700">
                District
              </label>
              <select
                id="districtId"
                value={districtId}
                onChange={(e) => setDistrictId(e.target.value)}
                disabled={submitting || !stateId || loadingDistricts}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white disabled:opacity-50"
              >
                <option value="">
                  {loadingDistricts
                    ? 'Loading districts...'
                    : stateId
                    ? 'Select District'
                    : 'Select State first'}
                </option>
                {districts.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.full_display_name || d.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Socio-Economic & Occupation */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-200">
            Socio-Economic & Occupation Details
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label htmlFor="annualIncome" className="block text-xs font-semibold text-slate-700">
                Annual Household Income (₹ INR)
              </label>
              <input
                id="annualIncome"
                type="number"
                min="0"
                step="1000"
                placeholder="e.g. 180000"
                value={annualIncome}
                onChange={(e) => setAnnualIncome(e.target.value)}
                disabled={submitting}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white font-mono tabular-nums"
              />
              <span className="text-[11px] text-slate-400">Used for income ceiling eligibility thresholds.</span>
            </div>

            <div className="space-y-1">
              <label htmlFor="occupation" className="block text-xs font-semibold text-slate-700">
                Occupation
              </label>
              <select
                id="occupation"
                value={occupation}
                onChange={(e) => setOccupation(e.target.value)}
                disabled={submitting}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white"
              >
                <option value="">Select Occupation</option>
                <option value="Farmer">Farmer / Agriculture Worker</option>
                <option value="Student">Student / Research Scholar</option>
                <option value="Artisan">Artisan / Traditional Craftsman</option>
                <option value="Self-Employed">Self-Employed / MSME Entrepreneur</option>
                <option value="Daily Wage Laborer">Daily Wage Laborer / Construction Worker</option>
                <option value="Salaried Employee">Salaried / Private Employee</option>
                <option value="Government Employee">Government Employee</option>
                <option value="Unemployed">Unemployed</option>
                <option value="Retired">Retired / Senior Citizen</option>
                <option value="Homemaker">Homemaker</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label htmlFor="education" className="block text-xs font-semibold text-slate-700">
                Highest Education Level
              </label>
              <select
                id="education"
                value={education}
                onChange={(e) => setEducation(e.target.value)}
                disabled={submitting}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white"
              >
                <option value="">Select Education</option>
                <option value="None">None / Literate</option>
                <option value="Primary (1-5)">Primary (1st to 5th Std)</option>
                <option value="Middle (6-8)">Middle (6th to 8th Std)</option>
                <option value="Secondary (10th)">Secondary (10th Pass)</option>
                <option value="Higher Secondary (12th)">Higher Secondary (12th Pass)</option>
                <option value="Diploma / ITI">Diploma / ITI</option>
                <option value="Graduate / Bachelor's">Graduate / Bachelor's Degree</option>
                <option value="Post Graduate / Master's">Post Graduate / Master's</option>
                <option value="Doctorate (Ph.D)">Doctorate (Ph.D)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label htmlFor="category" className="block text-xs font-semibold text-slate-700">
                Social Category
              </label>
              <select
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                disabled={submitting}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white"
              >
                <option value="">Select Category</option>
                <option value="General">General (Unreserved)</option>
                <option value="OBC">Other Backward Class (OBC)</option>
                <option value="SC">Scheduled Caste (SC)</option>
                <option value="ST">Scheduled Tribe (ST)</option>
                <option value="EWS">Economically Weaker Section (EWS)</option>
              </select>
            </div>
          </div>

          <div className="pt-2">
            <label className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer">
              <input
                id="disabilityStatus"
                type="checkbox"
                checked={disabilityStatus}
                onChange={(e) => setDisabilityStatus(e.target.checked)}
                disabled={submitting}
                className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-semibold">Person with Benchmark Disability (PwD / Divyangjan)</span>
            </label>
            <span className="text-[11px] text-slate-400 block mt-1 pl-6.5">
              Check if you possess a government certified disability certificate (≥40%) to include specialized welfare benefits.
            </span>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4 border-t border-slate-200 flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2.5 bg-[#07172c] hover:bg-slate-800 text-white font-bold rounded-xl text-xs sm:text-sm transition-colors shadow-sm disabled:opacity-50"
          >
            {submitting ? 'Saving Profile...' : 'Save & Update Qualification'}
          </button>
        </div>
      </form>
    </div>
  )
}
