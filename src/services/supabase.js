import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

let supabaseClient

if (supabaseUrl && supabaseAnonKey && supabaseUrl.startsWith('http')) {
  supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  })
} else {
  // Safe in-memory stub when external Supabase is not configured yet
  supabaseClient = {
    auth: {
      getSession: async () => ({ data: { session: null }, error: null }),
      onAuthStateChange: () => ({
        data: {
          subscription: {
            unsubscribe: () => {},
          },
        },
      }),
      signInWithPassword: async () => ({
        data: { session: null, user: null },
        error: new Error('Supabase project not connected. Using local instant demo session.'),
      }),
      signUp: async () => ({
        data: { session: null, user: null },
        error: new Error('Supabase project not connected. Using local instant demo session.'),
      }),
      signOut: async () => ({ error: null }),
    },
  }
}

export const supabase = supabaseClient
