import { useEffect, useState } from 'react'
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

  // 1. Fetch reference states and existing profile on mount
  useEffect(() => {
    let isMounted = true

    async function initializeProfile() {
      setPageLoading(true)
      setErrorMsg('')
      try {
        // Fetch states list from backend
        const statesData = await fetchStates()
        if (isMounted) setStates(statesData || [])

        // Fetch current profile if token exists
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

              // If state exists, load its districts immediately
              if (currentProfile.state_id) {
                const dists = await fetchDistricts(currentProfile.state_id)
                if (isMounted) setDistricts(dists || [])
              }
            }
          } catch (profileErr) {
            console.info('No existing profile found yet:', profileErr.message)
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

  // 2. Dynamic district loading when state changes
  const handleStateChange = async (newStateId) => {
    setStateId(newStateId)
    // Clear previously selected district
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

  // 3. Form submission
  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')

    // Validation
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
      setSuccessMsg('Your profile has been saved successfully! Schemes will now be evaluated against this profile.')
    } catch (err) {
      setErrorMsg(err.message || 'Failed to save profile. Please check your network and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (pageLoading) {
    return (
      <div className="page-loading">
        <div className="spinner"></div>
        <p>Loading demographic reference data...</p>
      </div>
    )
  }

  return (
    <div className="profile-page">
      <div className="profile-container">
        <div className="page-header">
          <h2>Citizen Demographic Profile</h2>
          <p className="header-subtitle">
            Provide your attributes to receive verified, deterministically eligible government scheme recommendations.
            Information is strictly isolated and used solely for statutory rule matching.
          </p>
        </div>

        {errorMsg && (
          <div className="alert alert-danger" role="alert">
            <span className="alert-icon">⚠️</span>
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="alert alert-success" role="alert">
            <span className="alert-icon">✅</span>
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="profile-form">
          {/* Identity Info */}
          <div className="form-section">
            <h3 className="section-title">Identity & Account</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="fullName">Full Name</label>
                <input
                  id="fullName"
                  type="text"
                  className="form-control"
                  placeholder="e.g. Priya Sharma"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={submitting}
                />
              </div>
              <div className="form-group">
                <label htmlFor="userEmail">Registered Email</label>
                <input
                  id="userEmail"
                  type="email"
                  className="form-control"
                  value={user?.email || ''}
                  disabled
                />
                <small className="text-muted">Email is linked to your Supabase authentication identity.</small>
              </div>
            </div>
          </div>

          {/* Demographic Info */}
          <div className="form-section">
            <h3 className="section-title">Demographics & Residency</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="age">Age (Years)</label>
                <input
                  id="age"
                  type="number"
                  min="0"
                  max="150"
                  className="form-control"
                  placeholder="e.g. 28"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  disabled={submitting}
                />
              </div>

              <div className="form-group">
                <label htmlFor="gender">Gender</label>
                <select
                  id="gender"
                  className="form-control"
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  disabled={submitting}
                >
                  <option value="">Select Gender</option>
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
                  <option value="TRANSGENDER">Transgender</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="stateId">Resident State / UT</label>
                <select
                  id="stateId"
                  className="form-control"
                  value={stateId}
                  onChange={(e) => handleStateChange(e.target.value)}
                  disabled={submitting}
                >
                  <option value="">Select State / UT (Pan-India)</option>
                  {states.map((st) => (
                    <option key={st.id} value={st.id}>
                      {st.name} ({st.code})
                    </option>
                  ))}
                </select>
                <small className="text-muted">
                  Used to include state-specific welfare schemes. Other states are excluded.
                </small>
              </div>

              <div className="form-group">
                <label htmlFor="districtId">District</label>
                <select
                  id="districtId"
                  className="form-control"
                  value={districtId}
                  onChange={(e) => setDistrictId(e.target.value)}
                  disabled={submitting || !stateId || loadingDistricts}
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
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Socio-Economic & Occupation */}
          <div className="form-section">
            <h3 className="section-title">Socio-Economic & Occupation Details</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="annualIncome">Annual Household Income (₹ INR)</label>
                <input
                  id="annualIncome"
                  type="number"
                  min="0"
                  step="1000"
                  className="form-control"
                  placeholder="e.g. 180000"
                  value={annualIncome}
                  onChange={(e) => setAnnualIncome(e.target.value)}
                  disabled={submitting}
                />
                <small className="text-muted">Used to check income ceiling criteria.</small>
              </div>

              <div className="form-group">
                <label htmlFor="occupation">Occupation</label>
                <select
                  id="occupation"
                  className="form-control"
                  value={occupation}
                  onChange={(e) => setOccupation(e.target.value)}
                  disabled={submitting}
                >
                  <option value="">Select Occupation</option>
                  <option value="Farmer">Farmer / Agriculture Worker</option>
                  <option value="Student">Student</option>
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

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="education">Highest Education Level</label>
                <select
                  id="education"
                  className="form-control"
                  value={education}
                  onChange={(e) => setEducation(e.target.value)}
                  disabled={submitting}
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

              <div className="form-group">
                <label htmlFor="category">Social Category</label>
                <select
                  id="category"
                  className="form-control"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  disabled={submitting}
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

            <div className="form-group checkbox-group">
              <label className="checkbox-label" htmlFor="disabilityStatus">
                <input
                  id="disabilityStatus"
                  type="checkbox"
                  checked={disabilityStatus}
                  onChange={(e) => setDisabilityStatus(e.target.checked)}
                  disabled={submitting}
                />
                <span>Person with Benchmark Disability (PwD / Divyangjan)</span>
              </label>
              <small className="text-muted d-block">
                Check if you have a recognized disability certificate (≥40% disability) for targeted welfare schemes.
              </small>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary btn-lg" disabled={submitting}>
              {submitting ? 'Saving Profile...' : 'Save & Update Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
