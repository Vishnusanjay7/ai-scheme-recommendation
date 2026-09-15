import { createClient } from '@supabase/supabase-js'

// Safe client-side Supabase credentials
// NEVER put secret service-role keys or OpenAI keys here
const supabaseUrl =
  import.meta.env.VITE_SUPABASE_URL ||
  'https://rqqzjmmsrjhhmqbtokzh.supabase.co'

const supabaseAnonKey =
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ||
  'sb_publishable_OiUD5XaiJMSBCBn_4uzFXg_iPEPm7L4'

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})
