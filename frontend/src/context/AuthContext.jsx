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

