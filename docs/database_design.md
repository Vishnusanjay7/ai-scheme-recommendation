# Database Design Specification

> **Phase:** 1 (Supabase Database + Row Level Security)  
> **Target Database Engine:** Supabase PostgreSQL 15+  
> **Schema File:** [`database/schema.sql`](file:///C:/Users/vishn/ai-gov-scheme-recommender/database/schema.sql)

---

## 1. Overview & Core Principles

The database architecture is designed with high data integrity, strict multi-tenant privacy via PostgreSQL Row Level Security (RLS), and support for both Central (Pan-India) and State-specific government welfare schemes.

### Fundamental Principles
1. **Strict Citizen Privacy:** All citizen demographic data, saved bookmarks, notification preferences, and chat interactions are protected by RLS tied to `auth.uid()`. Unauthenticated or unauthorized clients cannot read another citizen's records.
2. **Open Scheme Access:** Public government scheme details, structured eligibility rules, required documents, official source citations, categories, and geographic registries are publicly queryable.
3. **Deterministic Separation:** Eligibility criteria are structured into discrete columns (numerical ranges, boolean flags, enumerated demographics) rather than unstructured strings to enable deterministic rule evaluation.

---

## 2. Table Specifications (All 12 Application Tables)

```
                       ┌────────────────┐
                       │  auth.users    │
                       └───────┬────────┘
                               │ 1:1
                               ▼
┌──────────────────┐ 1:1 ┌──────────────┐ 1:N  ┌─────────────────┐
│  user_profiles   │◄────┤    users     ├─────►│  saved_schemes  │
└─────────┬────────┘     └──────┬───────┘      └────────┬────────┘
          │                     │ 1:N                   │ N:1
          │ 1:N (state/dist)    ├─────► notifications   │
          ▼                     │ 1:N                   ▼
┌──────────────────┐            └─────► chat_history   ┌─────────────────┐
│ states/districts │                                   │     schemes     │
└─────────┬────────┘                                   └────────┬────────┘
          │ 1:N (state schemes)                                 │ 1:N
          └─────────────────────────────────────────────────────┼──► scheme_eligibility
                                                                ├──► scheme_documents
                                                                └──► scheme_sources
```

---

### Table 1: `users`
Represents the citizen application user account. Synchronized automatically from `auth.users` upon signup. Passwords are never stored in this table.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `REFERENCES auth.users(id) ON DELETE CASCADE` | Supabase Auth UUID |
| `email` | `VARCHAR(255)` | `NOT NULL`, `UNIQUE` | Citizen email address |
| `full_name` | `VARCHAR(255)` | | Citizen full name |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Last update timestamp |

---

### Table 2: `user_profiles`
Citizen demographic, geographic, financial, and occupational details used by the deterministic eligibility engine.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Profile record identifier |
| `user_id` | `UUID` | `NOT NULL`, `UNIQUE`, `REFERENCES public.users(id) ON DELETE CASCADE` | 1:1 link to authenticated user |
| `age` | `INTEGER` | `CHECK (age >= 0 AND age <= 150)` | Citizen age |
| `gender` | `VARCHAR(20)` | `CHECK (gender IN ('MALE', 'FEMALE', 'TRANSGENDER', 'OTHER'))` | Citizen gender |
| `state_id` | `INTEGER` | `REFERENCES public.states(id) ON DELETE SET NULL` | Citizen resident state |
| `district_id` | `INTEGER` | `REFERENCES public.districts(id) ON DELETE SET NULL` | Citizen resident district |
| `annual_income` | `NUMERIC(12, 2)` | `CHECK (annual_income >= 0)` | Family annual income in INR |
| `occupation` | `VARCHAR(100)` | | Occupation (Farmer, Student, Artisan, etc.) |
| `education` | `VARCHAR(100)` | | Educational qualification level |
| `category` | `VARCHAR(50)` | | Social category (General, OBC, SC, ST, EWS) |
| `disability_status` | `BOOLEAN` | `NOT NULL`, `DEFAULT FALSE` | Disability status flag |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Profile creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Profile last updated |

---

### Table 3: `states`
Master reference registry of all 28 Indian States and 8 Union Territories.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Unique numeric identifier |
| `name` | `VARCHAR(100)` | `NOT NULL`, `UNIQUE` | State or UT name (e.g. 'Tamil Nadu') |
| `code` | `VARCHAR(10)` | `NOT NULL`, `UNIQUE` | ISO 3166-2:IN code (e.g. 'TN', 'DL') |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Timestamp |

---

### Table 4: `districts`
Master reference registry of districts across Indian states. Each district belongs to exactly one state.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Unique numeric identifier |
| `state_id` | `INTEGER` | `NOT NULL`, `REFERENCES public.states(id) ON DELETE CASCADE` | Parent state foreign key |
| `name` | `VARCHAR(100)` | `NOT NULL` | District name (e.g. 'Chennai') |
| `code` | `VARCHAR(20)` | | District code (e.g. 'CHN') |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Timestamp |
| *Constraint* | `UNIQUE (state_id, name)` | | Enforces uniqueness within each state |

---

### Table 5: `scheme_categories`
Classification sectors matching official welfare domain standards (e.g., Agriculture, Health, Education).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Unique category identifier |
| `name` | `VARCHAR(100)` | `NOT NULL`, `UNIQUE` | Official category name |
| `description` | `TEXT` | | Category scope and description |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Timestamp |

---

### Table 6: `schemes`
Master registry for Central and State government welfare schemes.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Unique scheme identifier |
| `scheme_name` | `VARCHAR(255)` | `NOT NULL` | Official name of welfare scheme |
| `description` | `TEXT` | | High-level summary of the scheme |
| `government_level`| `VARCHAR(20)` | `NOT NULL`, `CHECK (government_level IN ('CENTRAL', 'STATE'))` | Administrative jurisdiction |
| `state_id` | `INTEGER` | `REFERENCES public.states(id) ON DELETE SET NULL` | State FK (NULL for Central schemes) |
| `category_id` | `INTEGER` | `REFERENCES public.scheme_categories(id) ON DELETE SET NULL` | Welfare category FK |
| `benefits` | `TEXT` | | Monetary or non-monetary assistance |
| `application_process` | `TEXT` | | Step-by-step application instructions |
| `start_date` | `DATE` | | Opening date of scheme applications |
| `last_date` | `DATE` | | Application deadline |
| `status` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'ACTIVE'`, `CHECK (status IN ('ACTIVE', 'INACTIVE', 'EXPIRED'))` | Current administrative status |
| `official_url` | `TEXT` | | Official portal/application URL |
| `source_url` | `TEXT` | | Data source citation URL |
| `last_updated` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Date verified with official source |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Last record update timestamp |

---

### Table 7: `scheme_eligibility`
Normalized, structured criteria evaluated deterministically by the backend rule engine.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Eligibility record identifier |
| `scheme_id` | `UUID` | `NOT NULL`, `REFERENCES public.schemes(id) ON DELETE CASCADE` | Scheme foreign key |
| `min_age` | `INTEGER` | `CHECK (min_age >= 0)` | Minimum qualifying age |
| `max_age` | `INTEGER` | `CHECK (max_age IS NULL OR min_age IS NULL OR max_age >= min_age)` | Maximum qualifying age |
| `max_income` | `NUMERIC(12, 2)` | `CHECK (max_income >= 0)` | Maximum annual income cap in INR |
| `gender` | `VARCHAR(20)` | `CHECK (gender IN ('ALL', 'MALE', 'FEMALE', 'TRANSGENDER', 'OTHER') OR gender IS NULL)` | Target gender filter |
| `occupation` | `VARCHAR(100)` | | Qualifying profession/occupation |
| `education` | `VARCHAR(100)` | | Qualifying educational qualification |
| `category` | `VARCHAR(50)` | | Qualifying caste/social category |
| `disability_required` | `BOOLEAN` | `NOT NULL`, `DEFAULT FALSE` | Must be a Person with Disability (PwD) |
| `state_restriction` | `INTEGER` | `REFERENCES public.states(id) ON DELETE SET NULL` | Required domicile state |
| `district_restriction`| `INTEGER` | `REFERENCES public.districts(id) ON DELETE SET NULL` | Required domicile district |
| `other_conditions` | `JSONB` | `DEFAULT '{}'::jsonb` | Extensible criteria (e.g. land holding) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Last record update timestamp |

---

### Table 8: `scheme_documents`
Specific documentation needed by a citizen to submit a valid application.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Document record ID |
| `scheme_id` | `UUID` | `NOT NULL`, `REFERENCES public.schemes(id) ON DELETE CASCADE` | Target scheme foreign key |
| `document_name` | `VARCHAR(255)` | `NOT NULL` | Document title (e.g. Aadhaar, Income Cert) |
| `mandatory` | `BOOLEAN` | `NOT NULL`, `DEFAULT TRUE` | Mandatory vs optional supporting proof |
| `description` | `TEXT` | | Specific guidelines on issuer or format |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Timestamp |

---

### Table 9: `scheme_sources`
Official government gazettes, portal links, and verification provenance.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Source record ID |
| `scheme_id` | `UUID` | `NOT NULL`, `REFERENCES public.schemes(id) ON DELETE CASCADE` | Target scheme foreign key |
| `source_url` | `TEXT` | `NOT NULL` | Official source link or gazette URL |
| `source_type` | `VARCHAR(50)` | | Source type (OFFICIAL_PORTAL, GAZETTE, MYSCHEME) |
| `last_checked` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Timestamp when crawler last verified |
| `last_updated` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Timestamp when content was updated |

---

### Table 10: `saved_schemes`
Junction table tracking citizen bookmarks and saved schemes.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Bookmark record ID |
| `user_id` | `UUID` | `NOT NULL`, `REFERENCES public.users(id) ON DELETE CASCADE` | Citizen foreign key |
| `scheme_id` | `UUID` | `NOT NULL`, `REFERENCES public.schemes(id) ON DELETE CASCADE` | Scheme foreign key |
| `saved_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Timestamp when saved |
| *Constraint* | `UNIQUE (user_id, scheme_id)` | | Prevents duplicate bookmarks |

---

### Table 11: `notifications`
Citizen reminders, deadline notifications, and scheme updates.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Notification record ID |
| `user_id` | `UUID` | `NOT NULL`, `REFERENCES public.users(id) ON DELETE CASCADE` | Recipient citizen foreign key |
| `scheme_id` | `UUID` | `REFERENCES public.schemes(id) ON DELETE SET NULL` | Linked scheme (if applicable) |
| `message` | `TEXT` | `NOT NULL` | Notification body text |
| `notification_type` | `VARCHAR(50)` | `NOT NULL` | Type (DEADLINE_ALERT, NEW_SCHEME, SYSTEM) |
| `scheduled_at` | `TIMESTAMPTZ` | | Time when notification was queued |
| `sent_at` | `TIMESTAMPTZ` | | Time when notification was delivered |
| `status` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'PENDING'`, `CHECK in ('PENDING', 'SENT', 'FAILED', 'CANCELLED')` | Delivery status |
| `is_read` | `BOOLEAN` | `NOT NULL`, `DEFAULT FALSE` | Read status |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Record creation timestamp |

---

### Table 12: `chat_history`
Conversational interactions between the citizen and the AI Scheme Assistant.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Interaction ID |
| `user_id` | `UUID` | `NOT NULL`, `REFERENCES public.users(id) ON DELETE CASCADE` | Citizen user foreign key |
| `user_message` | `TEXT` | `NOT NULL` | Citizen query input |
| `bot_response` | `TEXT` | `NOT NULL` | Assistant answer |
| `language` | `VARCHAR(10)` | `NOT NULL`, `DEFAULT 'en'` | Interaction language code (e.g. 'en', 'ta', 'hi') |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `DEFAULT now()` | Timestamp |

---

## 3. Relationships Summary

| Relationship | Cardinality | Enforcing Constraint |
| :--- | :--- | :--- |
| `users` ➔ `user_profiles` | **1 : 1** | `user_profiles.user_id UNIQUE REFERENCES users(id)` |
| `states` ➔ `districts` | **1 : N** | `districts.state_id REFERENCES states(id)` |
| `states` ➔ `user_profiles` | **1 : N** | `user_profiles.state_id REFERENCES states(id)` |
| `states` ➔ `schemes` | **1 : N** | `schemes.state_id REFERENCES states(id)` |
| `scheme_categories` ➔ `schemes` | **1 : N** | `schemes.category_id REFERENCES scheme_categories(id)` |
| `schemes` ➔ `scheme_eligibility` | **1 : N** | `scheme_eligibility.scheme_id REFERENCES schemes(id)` |
| `schemes` ➔ `scheme_documents` | **1 : N** | `scheme_documents.scheme_id REFERENCES schemes(id)` |
| `schemes` ➔ `scheme_sources` | **1 : N** | `scheme_sources.scheme_id REFERENCES schemes(id)` |
| `users` ➔ `schemes` | **N : M** | Junction table `saved_schemes (user_id, scheme_id)` |
| `users` ➔ `notifications` | **1 : N** | `notifications.user_id REFERENCES users(id)` |
| `schemes` ➔ `notifications` | **1 : N** | `notifications.scheme_id REFERENCES schemes(id)` |
| `users` ➔ `chat_history` | **1 : N** | `chat_history.user_id REFERENCES users(id)` |

---

## 4. Central vs State Scheme Design

Government welfare in India operates on two administrative tiers:
1. **Central Schemes:** Sponsored directly by the Union Government and open to citizens nationwide (e.g., *PM-Kisan*, *Ayushman Bharat*).
2. **State Schemes:** Initiated and funded by specific state governments for residents of that state (e.g., *Kalaignar Magalir Urimai* in Tamil Nadu).

### Database Constraint Implementation:
```sql
CONSTRAINT chk_central_or_state_validity CHECK (
    (government_level = 'CENTRAL') OR
    (government_level = 'STATE' AND state_id IS NOT NULL)
)
```
- When `government_level = 'CENTRAL'`, `state_id` can be `NULL` (indicating pan-India applicability).
- When `government_level = 'STATE'`, `state_id` **must be non-NULL**, directly referencing the applicable state from the `states` registry.

---

## 5. Structured Eligibility Data Model

To strictly prevent hallucination and guarantee factual compliance, scheme eligibility is stored in discrete, queryable attributes in `scheme_eligibility`:

- **Numerical Criteria:** `min_age`, `max_age`, `max_income`.
- **Demographic Filters:** `gender`, `category` (General, OBC, SC, ST, EWS).
- **Special Status:** `disability_required` (boolean).
- **Geographic Bounds:** `state_restriction` and `district_restriction`.
- **Extensible Conditions:** `other_conditions` (`JSONB`) for parameters such as landholding size or rural/urban status.

Deterministic Rule Evaluation Logic:
$$\text{Eligible} \iff \text{All mandatory criteria match user profile}$$
$$\text{Possibly Eligible} \iff \text{Matching criteria met, but user profile lacks data for some non-critical fields}$$
$$\text{Not Eligible} \iff \text{At least one mandatory condition is violated}$$

---

## 6. Row Level Security (RLS) Strategy

Row Level Security is enabled on **all 12 tables** (`ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;`).

### Public Reference Tables (`SELECT` allowed for all):
- `states`, `districts`, `scheme_categories`, `schemes`, `scheme_eligibility`, `scheme_documents`, `scheme_sources`
- Governed by policy: `USING (true)` for `SELECT` operations only. Write operations are restricted to admin/service roles.

### Private Citizen Data Tables:
- `users`, `user_profiles`, `saved_schemes`, `notifications`, `chat_history`
- Strictly governed by `auth.uid() = user_id` (or `auth.uid() = id` for `users`).
- **Zero leakage:** Insecure wildcard policies (`USING (true)`) are strictly forbidden on private tables.

---

## 7. Performance Indexes

The schema creates 17 targeted indexes to optimize query performance across foreign key joins, citizen lookups, and scheme search:

```sql
CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX idx_user_profiles_state_id ON public.user_profiles(state_id);
CREATE INDEX idx_user_profiles_district_id ON public.user_profiles(district_id);
CREATE INDEX idx_districts_state_id ON public.districts(state_id);
CREATE INDEX idx_schemes_state_id ON public.schemes(state_id);
CREATE INDEX idx_schemes_government_level ON public.schemes(government_level);
CREATE INDEX idx_schemes_category_id ON public.schemes(category_id);
CREATE INDEX idx_schemes_status ON public.schemes(status);
CREATE INDEX idx_schemes_last_date ON public.schemes(last_date);
CREATE INDEX idx_scheme_eligibility_scheme_id ON public.scheme_eligibility(scheme_id);
CREATE INDEX idx_scheme_documents_scheme_id ON public.scheme_documents(scheme_id);
CREATE INDEX idx_scheme_sources_scheme_id ON public.scheme_sources(scheme_id);
CREATE INDEX idx_saved_schemes_user_id ON public.saved_schemes(user_id);
CREATE INDEX idx_saved_schemes_scheme_id ON public.saved_schemes(scheme_id);
CREATE INDEX idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX idx_notifications_scheme_id ON public.notifications(scheme_id);
CREATE INDEX idx_chat_history_user_id ON public.chat_history(user_id);
```
