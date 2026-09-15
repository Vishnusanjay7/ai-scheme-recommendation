-- ==============================================================================
-- AI-Powered Government Scheme Recommendation System
-- Complete PostgreSQL Database Schema (Supabase PostgreSQL + RLS)
-- ==============================================================================
-- 
-- Exactly 12 Application Tables:
--  1. users
--  2. user_profiles
--  3. states
--  4. districts
--  5. scheme_categories
--  6. schemes
--  7. scheme_eligibility
--  8. scheme_documents
--  9. scheme_sources
-- 10. saved_schemes
-- 11. notifications
-- 12. chat_history
--
-- ==============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Note: In Supabase, the `auth` schema and `auth.users` table are pre-existing and managed natively.

-- ==============================================================================
-- HELPER FUNCTIONS & TRIGGERS
-- ==============================================================================

-- Trigger function to automatically maintain updated_at timestamps
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- TABLE 1: users
-- ==============================================================================
-- Links directly to auth.users (Supabase Auth). No passwords stored here.
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- TABLE 2: states
-- ==============================================================================
-- Master reference for Indian States and Union Territories (all 36 entities)
CREATE TABLE IF NOT EXISTS public.states (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- TABLE 3: districts
-- ==============================================================================
-- District belongs to exactly one state
CREATE TABLE IF NOT EXISTS public.districts (
    id SERIAL PRIMARY KEY,
    state_id INTEGER NOT NULL REFERENCES public.states(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_state_district_name UNIQUE (state_id, name)
);

-- ==============================================================================
-- TABLE 4: user_profiles
-- ==============================================================================
-- 1:1 relationship with users table. Citizen demographic & financial attributes.
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    age INTEGER CHECK (age >= 0 AND age <= 150),
    gender VARCHAR(20) CHECK (gender IN ('MALE', 'FEMALE', 'TRANSGENDER', 'OTHER')),
    state_id INTEGER REFERENCES public.states(id) ON DELETE SET NULL,
    district_id INTEGER REFERENCES public.districts(id) ON DELETE SET NULL,
    annual_income NUMERIC(12, 2) CHECK (annual_income >= 0),
    occupation VARCHAR(100),
    education VARCHAR(100),
    category VARCHAR(50),
    disability_status BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- TABLE 5: scheme_categories
-- ==============================================================================
-- Master categories matching official Indian welfare sectors
CREATE TABLE IF NOT EXISTS public.scheme_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- TABLE 6: schemes
-- ==============================================================================
-- Central and State government welfare schemes.
CREATE TABLE IF NOT EXISTS public.schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_name VARCHAR(255) NOT NULL,
    description TEXT,
    government_level VARCHAR(20) NOT NULL CHECK (government_level IN ('CENTRAL', 'STATE')),
    state_id INTEGER REFERENCES public.states(id) ON DELETE SET NULL,
    category_id INTEGER REFERENCES public.scheme_categories(id) ON DELETE SET NULL,
    benefits TEXT,
    application_process TEXT,
    start_date DATE,
    last_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'EXPIRED')),
    official_url TEXT,
    source_url TEXT,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT chk_central_or_state_validity CHECK (
        (government_level = 'CENTRAL') OR
        (government_level = 'STATE' AND state_id IS NOT NULL)
    ),
    CONSTRAINT chk_scheme_dates CHECK (
        last_date IS NULL OR start_date IS NULL OR last_date >= start_date
    )
);

-- ==============================================================================
-- TABLE 7: scheme_eligibility
-- ==============================================================================
-- Structured criteria for deterministic eligibility evaluation
CREATE TABLE IF NOT EXISTS public.scheme_eligibility (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE,
    min_age INTEGER CHECK (min_age >= 0),
    max_age INTEGER CHECK (max_age IS NULL OR (min_age IS NULL OR max_age >= min_age)),
    max_income NUMERIC(12, 2) CHECK (max_income >= 0),
    gender VARCHAR(20) CHECK (gender IN ('ALL', 'MALE', 'FEMALE', 'TRANSGENDER', 'OTHER') OR gender IS NULL),
    occupation VARCHAR(100),
    education VARCHAR(100),
    category VARCHAR(50),
    disability_required BOOLEAN NOT NULL DEFAULT FALSE,
    state_restriction INTEGER REFERENCES public.states(id) ON DELETE SET NULL,
    district_restriction INTEGER REFERENCES public.districts(id) ON DELETE SET NULL,
    other_conditions JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- TABLE 8: scheme_documents
-- ==============================================================================
-- Documents required to apply for a scheme
CREATE TABLE IF NOT EXISTS public.scheme_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE,
    document_name VARCHAR(255) NOT NULL,
    mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- TABLE 9: scheme_sources
-- ==============================================================================
-- Official provenance and audit trail for scheme details
CREATE TABLE IF NOT EXISTS public.scheme_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    source_type VARCHAR(50),
    last_checked TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- TABLE 10: saved_schemes
-- ==============================================================================
-- Citizen bookmarked schemes (N:M through unique compound index)
CREATE TABLE IF NOT EXISTS public.saved_schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_user_saved_scheme UNIQUE (user_id, scheme_id)
);

-- ==============================================================================
-- TABLE 11: notifications
-- ==============================================================================
-- In-app notifications & deadline alerts for citizens
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    scheme_id UUID REFERENCES public.schemes(id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    scheduled_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SENT', 'FAILED', 'CANCELLED')),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- TABLE 12: chat_history
-- ==============================================================================
-- Citizen conversational assistant queries and responses
CREATE TABLE IF NOT EXISTS public.chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- AUTO-UPDATE TIMESTAMP TRIGGERS
-- ==============================================================================
DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_user_profiles_updated_at ON public.user_profiles;
CREATE TRIGGER trg_user_profiles_updated_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_schemes_updated_at ON public.schemes;
CREATE TRIGGER trg_schemes_updated_at
    BEFORE UPDATE ON public.schemes
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_scheme_eligibility_updated_at ON public.scheme_eligibility;
CREATE TRIGGER trg_scheme_eligibility_updated_at
    BEFORE UPDATE ON public.scheme_eligibility
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ==============================================================================
-- SUPABASE AUTH SYNCHRONIZATION TRIGGER
-- ==============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name, created_at, updated_at)
    VALUES (
        NEW.id,
        COALESCE(NEW.email, ''),
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', ''),
        timezone('utc'::text, now()),
        timezone('utc'::text, now())
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        full_name = EXCLUDED.full_name,
        updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();

-- ==============================================================================
-- DATABASE INDEXES (PART E)
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_state_id ON public.user_profiles(state_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_district_id ON public.user_profiles(district_id);

CREATE INDEX IF NOT EXISTS idx_districts_state_id ON public.districts(state_id);

CREATE INDEX IF NOT EXISTS idx_schemes_state_id ON public.schemes(state_id);
CREATE INDEX IF NOT EXISTS idx_schemes_government_level ON public.schemes(government_level);
CREATE INDEX IF NOT EXISTS idx_schemes_category_id ON public.schemes(category_id);
CREATE INDEX IF NOT EXISTS idx_schemes_status ON public.schemes(status);
CREATE INDEX IF NOT EXISTS idx_schemes_last_date ON public.schemes(last_date);

CREATE INDEX IF NOT EXISTS idx_scheme_eligibility_scheme_id ON public.scheme_eligibility(scheme_id);
CREATE INDEX IF NOT EXISTS idx_scheme_documents_scheme_id ON public.scheme_documents(scheme_id);
CREATE INDEX IF NOT EXISTS idx_scheme_sources_scheme_id ON public.scheme_sources(scheme_id);

CREATE INDEX IF NOT EXISTS idx_saved_schemes_user_id ON public.saved_schemes(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_schemes_scheme_id ON public.saved_schemes(scheme_id);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_scheme_id ON public.notifications(scheme_id);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON public.chat_history(user_id);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES (PART D)
-- ==============================================================================

-- Enable RLS across all 12 tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.districts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheme_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.schemes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheme_eligibility ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheme_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheme_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_schemes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- Public/Reference Data Policies: Publicly readable by all citizens
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Allow public read access on states" ON public.states;
CREATE POLICY "Allow public read access on states"
    ON public.states FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow public read access on districts" ON public.districts;
CREATE POLICY "Allow public read access on districts"
    ON public.districts FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow public read access on scheme_categories" ON public.scheme_categories;
CREATE POLICY "Allow public read access on scheme_categories"
    ON public.scheme_categories FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow public read access on schemes" ON public.schemes;
CREATE POLICY "Allow public read access on schemes"
    ON public.schemes FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow public read access on scheme_eligibility" ON public.scheme_eligibility;
CREATE POLICY "Allow public read access on scheme_eligibility"
    ON public.scheme_eligibility FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow public read access on scheme_documents" ON public.scheme_documents;
CREATE POLICY "Allow public read access on scheme_documents"
    ON public.scheme_documents FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow public read access on scheme_sources" ON public.scheme_sources;
CREATE POLICY "Allow public read access on scheme_sources"
    ON public.scheme_sources FOR SELECT
    USING (true);

-- ------------------------------------------------------------------------------
-- Private Citizen Data Policies: Strictly isolated using auth.uid()
-- ------------------------------------------------------------------------------

-- users: Citizen can only view and update their own record
DROP POLICY IF EXISTS "Users can view their own record" ON public.users;
CREATE POLICY "Users can view their own record"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update their own record" ON public.users;
CREATE POLICY "Users can update their own record"
    ON public.users FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert their own record" ON public.users;
CREATE POLICY "Users can insert their own record"
    ON public.users FOR INSERT
    WITH CHECK (auth.uid() = id);

-- user_profiles: Citizen can manage only their own profile
DROP POLICY IF EXISTS "Users can view their own profile" ON public.user_profiles;
CREATE POLICY "Users can view their own profile"
    ON public.user_profiles FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own profile" ON public.user_profiles;
CREATE POLICY "Users can insert their own profile"
    ON public.user_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own profile" ON public.user_profiles;
CREATE POLICY "Users can update their own profile"
    ON public.user_profiles FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own profile" ON public.user_profiles;
CREATE POLICY "Users can delete their own profile"
    ON public.user_profiles FOR DELETE
    USING (auth.uid() = user_id);

-- saved_schemes: Citizen can view, bookmark, and remove their saved schemes
DROP POLICY IF EXISTS "Users can view their saved schemes" ON public.saved_schemes;
CREATE POLICY "Users can view their saved schemes"
    ON public.saved_schemes FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can bookmark schemes" ON public.saved_schemes;
CREATE POLICY "Users can bookmark schemes"
    ON public.saved_schemes FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can remove saved schemes" ON public.saved_schemes;
CREATE POLICY "Users can remove saved schemes"
    ON public.saved_schemes FOR DELETE
    USING (auth.uid() = user_id);

-- notifications: Citizen can view, mark read, and delete their own notifications
DROP POLICY IF EXISTS "Users can view their notifications" ON public.notifications;
CREATE POLICY "Users can view their notifications"
    ON public.notifications FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their notifications" ON public.notifications;
CREATE POLICY "Users can update their notifications"
    ON public.notifications FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their notifications" ON public.notifications;
CREATE POLICY "Users can delete their notifications"
    ON public.notifications FOR DELETE
    USING (auth.uid() = user_id);

-- chat_history: Citizen can view, record, and delete their own chat interactions
DROP POLICY IF EXISTS "Users can view their chat history" ON public.chat_history;
CREATE POLICY "Users can view their chat history"
    ON public.chat_history FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert chat messages" ON public.chat_history;
CREATE POLICY "Users can insert chat messages"
    ON public.chat_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their chat history" ON public.chat_history;
CREATE POLICY "Users can delete their chat history"
    ON public.chat_history FOR DELETE
    USING (auth.uid() = user_id);

-- ==============================================================================
-- REFERENCE DATA (PART F)
-- ==============================================================================

-- 1. All 28 Indian States and 8 Union Territories (Official ISO 3166-2:IN standard)
INSERT INTO public.states (name, code) VALUES
    -- 28 States
    ('Andhra Pradesh', 'AP'),
    ('Arunachal Pradesh', 'AR'),
    ('Assam', 'AS'),
    ('Bihar', 'BR'),
    ('Chhattisgarh', 'CG'),
    ('Goa', 'GA'),
    ('Gujarat', 'GJ'),
    ('Haryana', 'HR'),
    ('Himachal Pradesh', 'HP'),
    ('Jharkhand', 'JH'),
    ('Karnataka', 'KA'),
    ('Kerala', 'KL'),
    ('Madhya Pradesh', 'MP'),
    ('Maharashtra', 'MH'),
    ('Manipur', 'MN'),
    ('Meghalaya', 'ML'),
    ('Mizoram', 'MZ'),
    ('Nagaland', 'NL'),
    ('Odisha', 'OD'),
    ('Punjab', 'PB'),
    ('Rajasthan', 'RJ'),
    ('Sikkim', 'SK'),
    ('Tamil Nadu', 'TN'),
    ('Telangana', 'TS'),
    ('Tripura', 'TR'),
    ('Uttar Pradesh', 'UP'),
    ('Uttarakhand', 'UK'),
    ('West Bengal', 'WB'),
    -- 8 Union Territories
    ('Andaman and Nicobar Islands', 'AN'),
    ('Chandigarh', 'CH'),
    ('Dadra and Nagar Haveli and Daman and Diu', 'DN'),
    ('Delhi', 'DL'),
    ('Jammu and Kashmir', 'JK'),
    ('Ladakh', 'LA'),
    ('Lakshadweep', 'LD'),
    ('Puducherry', 'PY')
ON CONFLICT (name) DO UPDATE SET code = EXCLUDED.code;

-- 2. Official Government Scheme Categories (myScheme.gov.in standard)
INSERT INTO public.scheme_categories (name, description) VALUES
    ('Agriculture, Rural & Environment', 'Farming subsidies, crop insurance, rural development, and environmental welfare'),
    ('Banking, Financial Services and Insurance', 'Financial inclusion, micro-loans, pension funds, and life/health insurance'),
    ('Business & Entrepreneurship', 'Startups, MSME assistance, industrial credit, and self-employment initiatives'),
    ('Education & Learning', 'Scholarships, student coaching, education loans, and academic grants'),
    ('Health & Wellness', 'Public health insurance, medical subsidies, maternal healthcare, and critical illness support'),
    ('Housing & Shelter', 'Affordable rural and urban housing schemes, subsidies, and construction support'),
    ('Public Safety, Law & Justice', 'Legal aid, victim compensation, and citizen grievance assistance'),
    ('Science, IT & Communications', 'Research fellowships, technology innovation, and digital empowerment schemes'),
    ('Skills & Employment', 'Vocational training, apprenticeship programs, job placement, and skill certification'),
    ('Social Welfare & Empowerment', 'Assistance for senior citizens, SC/ST/OBC communities, and marginalized groups'),
    ('Sports & Culture', 'Athletic training grants, national sports awards, and cultural heritage support'),
    ('Transport & Infrastructure', 'Rural road development, transport subsidies, and infrastructure connectivity'),
    ('Travel & Tourism', 'Pilgrimage subsidies, eco-tourism initiatives, and travel assistance'),
    ('Women and Child Development', 'Girl child protection, nutrition programs, and maternal welfare benefits')
ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;

-- 3. Representative District Structure
-- Note: The complete official national dataset of 780+ districts will be loaded
-- via the automated data pipeline in Phase 2.
INSERT INTO public.districts (state_id, name, code)
SELECT s.id, d.name, d.code
FROM (
    VALUES
        ('TN', 'Chennai', 'CHN'),
        ('TN', 'Coimbatore', 'CBE'),
        ('TN', 'Madurai', 'MDU'),
        ('DL', 'New Delhi', 'NDL'),
        ('DL', 'Central Delhi', 'CDL'),
        ('MH', 'Mumbai City', 'MUM'),
        ('MH', 'Pune', 'PUN'),
        ('KA', 'Bengaluru Urban', 'BLR'),
        ('KA', 'Mysuru', 'MYS'),
        ('UP', 'Lucknow', 'LKO'),
        ('UP', 'Varanasi', 'VNS')
) AS d(state_code, name, code)
JOIN public.states s ON s.code = d.state_code
ON CONFLICT (state_id, name) DO NOTHING;
