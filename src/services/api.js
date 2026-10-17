/**
 * Backend API Client
 * ------------------
 * Interacts with FastAPI backend endpoints:
 *   - /api/states
 *   - /api/districts
 *   - /api/profile
 *   - /api/recommendations
 *   - /api/schemes
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'An unexpected server error occurred.'
    try {
      const errorJson = await response.json()
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail)
      } else if (errorJson.message) {
        errorDetail = errorJson.message
      }
    } catch {
      errorDetail = `Request failed with status ${response.status} (${response.statusText})`
    }
    const error = new Error(errorDetail)
    error.status = response.status
    throw error
  }
  return response.json()
}

export async function fetchStates() {
  const res = await fetch(`${API_BASE}/api/states`, {
    headers: { 'Accept': 'application/json' },
  })
  return handleResponse(res)
}

export async function fetchDistricts(stateId = null, query = null) {
  const params = new URLSearchParams()
  if (stateId) params.append('state_id', stateId)
  if (query) params.append('q', query)
  const qs = params.toString() ? `?${params.toString()}` : ''
  const res = await fetch(`${API_BASE}/api/districts${qs}`, {
    headers: { 'Accept': 'application/json' },
  })
  return handleResponse(res)
}

export async function fetchProfile(token) {
  const res = await fetch(`${API_BASE}/api/profile`, {
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function saveProfile(profileData, token) {
  const res = await fetch(`${API_BASE}/api/profile`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(profileData),
  })
  return handleResponse(res)
}

export async function fetchRecommendations(query = null, token = null, limit = 50, offset = 0, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const payload = {
    query: query || null,
    limit,
    offset,
    sort: options.sort || 'match',
    level: options.level || null,
    category: options.category || null,
    state_id: options.state_id || null,
    profile: options.profile || null,
  }

  const res = await fetch(`${API_BASE}/api/recommendations`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  })
  return handleResponse(res)
}

export async function fetchSyncStatus() {
  const res = await fetch(`${API_BASE}/api/schemes/sync-status`, {
    headers: { 'Accept': 'application/json' },
  })
  return handleResponse(res)
}

export async function triggerManualSync() {
  const res = await fetch(`${API_BASE}/api/schemes/sync-now`, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  })
  return handleResponse(res)
}

export async function fetchSchemeDetails(schemeId) {
  const res = await fetch(`${API_BASE}/api/schemes/${encodeURIComponent(schemeId)}`, {
    headers: { 'Accept': 'application/json' },
  })
  return handleResponse(res)
}

export async function fetchActiveSchemes(limit = 50, offset = 0) {
  const res = await fetch(`${API_BASE}/api/schemes/active?limit=${limit}&offset=${offset}`, {
    headers: { 'Accept': 'application/json' },
  })
  return handleResponse(res)
}

export async function fetchSavedSchemes(token) {
  const res = await fetch(`${API_BASE}/api/saved-schemes`, {
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function checkSchemeSaved(schemeId, token) {
  const res = await fetch(`${API_BASE}/api/saved-schemes/${encodeURIComponent(schemeId)}`, {
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function saveScheme(schemeId, token) {
  const res = await fetch(`${API_BASE}/api/saved-schemes/${encodeURIComponent(schemeId)}`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function removeSavedScheme(schemeId, token) {
  const res = await fetch(`${API_BASE}/api/saved-schemes/${encodeURIComponent(schemeId)}`, {
    method: 'DELETE',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function fetchNotifications(token, limit = 50) {
  const res = await fetch(`${API_BASE}/api/notifications?limit=${limit}`, {
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function fetchUnreadNotifications(token) {
  const res = await fetch(`${API_BASE}/api/notifications/unread`, {
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function markNotificationRead(notificationId, token) {
  const res = await fetch(`${API_BASE}/api/notifications/${encodeURIComponent(notificationId)}/read`, {
    method: 'PATCH',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function markAllNotificationsRead(token) {
  const res = await fetch(`${API_BASE}/api/notifications/read-all`, {
    method: 'PATCH',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function sendChatMessage(message, token = null, language = null) {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const payload = {
    message,
    language: language || null,
  }

  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  })
  return handleResponse(res)
}

export async function fetchChatHistory(token, limit = 50) {
  const res = await fetch(`${API_BASE}/api/chat/history?limit=${limit}`, {
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  return handleResponse(res)
}

export async function fetchVoiceTTS(text, language = 'en') {
  const res = await fetch(`${API_BASE}/api/chat/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ text, language }),
  })
  return handleResponse(res)
}



