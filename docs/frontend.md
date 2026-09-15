# Phase 6: Citizen Frontend Dashboard & Government Scheme UI

## Architecture Overview

The citizen frontend is built using **React 19**, **Vite**, **React Router v7**, and plain, accessible **CSS**. It connects directly to the authenticated FastAPI backend and Supabase Auth.

```
Citizen Browser (React 19 + Vite)
    ├── Supabase Client (Browser Auth Session / JWT)
    └── Backend REST Client (/api)
           ├── Bearer Token Auth (Validated with Supabase auth.uid())
           ├── GET /api/states & GET /api/districts?state_id=...
           ├── GET & PUT /api/profile (user_profiles schema)
           ├── POST /api/recommendations (Phase 5 Deterministic + AI Ranking)
           └── GET /api/schemes/active & GET /api/schemes/{id} (Phase 4 Active Schemes)
```

---

## Page Structure

| Path | Component | Auth Required | Description |
|---|---|---|---|
| `/login` | `Login.jsx` | No (Redirects if auth) | Citizen email/password login via Supabase Auth |
| `/register` | `Register.jsx` | No (Redirects if auth) | Citizen registration with full name & credentials |
| `/dashboard` | `Dashboard.jsx` | Yes (`ProtectedRoute`) | Overview of state/district, profile status, featured open schemes, system explainer |
| `/profile` | `Profile.jsx` | Yes (`ProtectedRoute`) | Demographic form matching `user_profiles` table, state dropdown, cascading district selector |
| `/recommendations` | `Recommendations.jsx` | Yes (`ProtectedRoute`) | Natural-language query search, recommendations list (Eligible + Open), separate verification section |
| `/schemes/:id` | `SchemeDetails.jsx` | Yes (`ProtectedRoute`) | Deep view of benefits, documents, eligibility criteria, application process, and official external portal link |

---

## Authentication Flow

1. **Sign Up (`Register.jsx`)**:
   - Calls `supabase.auth.signUp({ email, password, options: { data: { full_name } } })`.
   - On success, prompts the citizen to sign in or checks for active session.
2. **Sign In (`Login.jsx`)**:
   - Calls `supabase.auth.signInWithPassword({ email, password })`.
   - Stores session securely in browser storage managed by `@supabase/supabase-js`.
   - Injects the authenticated token into backend requests via `Authorization: Bearer <session.access_token>`.
3. **Route Protection (`ProtectedRoute.jsx`)**:
   - Checks `useAuth()`. If loading, renders a clean loading spinner.
   - If unauthenticated, safely redirects to `/login`.
4. **Sign Out (`Navbar.jsx`)**:
   - Calls `supabase.auth.signOut()` and resets React state, redirecting to `/login`.

---

## Reference Data & Profile API Integration

- **States & Districts**:
  - `GET /api/states`: Returns all 36 Indian states and union territories from the authoritative database `states` table.
  - `GET /api/districts?state_id={id}`: Dynamically filters districts when the citizen selects or changes their state. If the selected district no longer belongs to the newly chosen state, it is automatically cleared.
- **Profile Management**:
  - `GET /api/profile`: Retrieves the citizen's demographic record from `user_profiles` based strictly on `auth.uid()`.
  - `PUT /api/profile`: Validates and persists age, gender, state, district, annual income, occupation, education, category, and disability status. Client-side ID spoofing is prohibited; the backend extracts identity directly from the verified JWT.

---

## Recommendation & Scheme Display Flow

1. Citizen enters an optional natural-language request (e.g., *"I am a small farmer looking for financial assistance"*).
2. Frontend issues `POST /api/recommendations` with the citizen's bearer token.
3. Backend runs:
   - Profile verification.
   - Deterministic eligibility check (`Phase 3`).
   - Active deadline verification (`Phase 4`).
   - AI semantic scoring and ranking (`Phase 5`).
4. Frontend displays returned cards:
   - **Relevance / Match Score**: Displayed as `Relevance Match: X/100` (strictly never displayed as an "eligibility score").
   - **Eligibility Badge**: `🟢 Eligible` or `🟡 Eligibility Needs Verification` (displayed in a dedicated verification section).
   - **Deadline Badge**: Authoritative deadline status (`Closing Today`, `Urgent — X days remaining`, `Approaching — X days remaining`, `Open — No Deadline`).
   - **Official Application Portal**: Outbound link with `target="_blank" rel="noopener noreferrer"` directing the citizen to the verified government portal URL. The system makes it explicit that application submission happens on the official portal, not internally.

---

## Empty Database Handling

If the connected database contains 0 active government schemes (as authorized official pipeline ingestion is pending), the UI explicitly and truthfully communicates this:

> *"No government schemes are currently available in the connected scheme database. The official-source acquisition pipeline is ready, but no live scheme records are currently loaded."*

- **Zero Fake Schemes**: The frontend contains no mock cards or hardcoded schemes.
- **Truthful Status**: The interface never reports "No schemes match your profile" when the database itself is empty.

---

## Security Considerations

1. **No Sensitive Keys in Frontend**:
   - `OPENAI_API_KEY` and `SUPABASE_SERVICE_ROLE_KEY` remain strictly server-side.
   - Only `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are accessed by the Vite frontend.
2. **Authoritative Backend**:
   - Eligibility is never calculated in React.
   - Relevance scoring is never calculated in React.
   - The citizen cannot submit an arbitrary `eligibility_status` or manipulate scheme verification.
3. **Safe Outbound Navigation**:
   - All external application and official source links open in new tabs with `rel="noopener noreferrer"`.
