import { useEffect, useState } from 'react'
import { supabase } from '../services/supabase'
import { AuthContext } from './authContextInstance'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [authError, setAuthError] = useState(null)

  useEffect(() => {
    // 1. Check existing active session on mount
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (error) {
        setAuthError(error.message)
      } else if (session) {
        setSession(session)
        setUser(session.user)
      }
      setLoading(false)
    })

    // 2. Subscribe to auth state updates
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session ? session.user : null)
      setLoading(false)
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const login = async (email, password) => {
    setAuthError(null)
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) {
      setAuthError(error.message)
      throw error
    }
    setSession(data.session)
    setUser(data.user)
    return data
  }

  const register = async (email, password, fullName) => {
    setAuthError(null)

    // 1. Try server-side admin provisioning first (bypasses Supabase email rate limits & auto-confirms)
    try {
      const resp = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName }),
      })

      if (resp.ok) {
        // Automatically establish session via instant login
        const loginData = await supabase.auth.signInWithPassword({
          email,
          password,
        })
        if (loginData.data?.session) {
          setSession(loginData.data.session)
          setUser(loginData.data.user)
          return loginData.data
        }
        const createdUser = (await resp.json()).user
        return { user: createdUser, session: null }
      } else if (resp.status === 400) {
        const errJson = await resp.json().catch(() => ({}))
        const error = new Error(errJson.detail || 'An account with this email already exists.')
        setAuthError(error.message)
        throw error
      }
    } catch (err) {
      if (
        err.message?.includes('already exists') ||
        err.message?.includes('Please login') ||
        err.message?.includes('Please sign in')
      ) {
        throw err
      }
      // If backend is unreachable or returns error, fall back to direct Supabase signup
    }

    // 2. Direct Supabase client signup fallback
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    })
    if (error) {
      setAuthError(error.message)
      throw error
    }
    return data
  }

  const logout = async () => {
    setAuthError(null)
    const { error } = await supabase.auth.signOut()
    if (error) {
      setAuthError(error.message)
      throw error
    }
    setUser(null)
    setSession(null)
  }

  const token = session ? session.access_token : null

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        token,
        loading,
        authError,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}



