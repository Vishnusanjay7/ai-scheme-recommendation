# Phase 7: Saved Schemes & Bookmarks

## Architecture Overview

The Saved Schemes subsystem enables authenticated citizens to bookmark welfare schemes for subsequent review. The feature strictly reuses the existing `saved_schemes` junction table and Row Level Security (RLS) policies established in Phase 1.

```
Citizen Interface (React)
    ├── SchemeCard ("Save Scheme" / "Saved ✓")
    ├── SchemeDetails ("Save Scheme" / "Saved to Bookmarks ✓")
    └── /saved-schemes (SavedSchemes.jsx)
           │
           ▼  Authorization: Bearer <auth.uid() token>
FastAPI Backend (/api/saved-schemes)
    ├── POST   /api/saved-schemes/{scheme_id}  (Idempotent Bookmark)
    ├── GET    /api/saved-schemes              (Live Activity Enriched List)
    ├── GET    /api/saved-schemes/{scheme_id}  (Check Bookmark State)
    └── DELETE /api/saved-schemes/{scheme_id}  (Remove Bookmark Only)
           │
           ▼  PostgreSQL (Supabase)
    Table: public.saved_schemes (user_id, scheme_id)
    RLS: auth.uid() = user_id
```

---

## Database Relationship

- **Table**: `public.saved_schemes`
- **Columns**:
  - `id`: `UUID PRIMARY KEY DEFAULT gen_random_uuid()`
  - `user_id`: `UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE`
  - `scheme_id`: `UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE`
  - `saved_at`: `TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())`
- **Constraints**:
  - `CONSTRAINT uq_user_saved_scheme UNIQUE (user_id, scheme_id)`
- **Indexes**:
  - `idx_saved_schemes_user_id ON public.saved_schemes(user_id)`
  - `idx_saved_schemes_scheme_id ON public.saved_schemes(scheme_id)`

---

## Row Level Security (RLS)

Citizen data isolation is enforced at the database level:
- **SELECT**: `CREATE POLICY "Users can view their saved schemes" ON public.saved_schemes FOR SELECT USING (auth.uid() = user_id);`
- **INSERT**: `CREATE POLICY "Users can bookmark schemes" ON public.saved_schemes FOR INSERT WITH CHECK (auth.uid() = user_id);`
- **DELETE**: `CREATE POLICY "Users can remove saved schemes" ON public.saved_schemes FOR DELETE USING (auth.uid() = user_id);`

No client can view, modify, or delete another citizen's saved records. The backend also enforces `auth.uid()` derivation directly from verified JWT tokens without accepting arbitrary client user IDs.

---

## API Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/saved-schemes/{scheme_id}` | Yes (`auth.uid()`) | Bookmark a scheme. Returns 200/201 with `{"status": "saved"}` or `{"status": "already_saved"}`. |
| `GET` | `/api/saved-schemes` | Yes (`auth.uid()`) | List citizen's bookmarked schemes with real-time deadline and activity metadata. |
| `GET` | `/api/saved-schemes/{scheme_id}` | Yes (`auth.uid()`) | Check if a specific scheme is bookmarked (`{"saved": true/false, ...}`). |
| `DELETE` | `/api/saved-schemes/{scheme_id}` | Yes (`auth.uid()`) | Remove scheme from bookmarks (`saved_schemes` row deleted; parent scheme untouched). |

---

## Save & Remove Flow

1. **Scheme Existence Verification**:
   - Before inserting a bookmark, the service verifies that `scheme_id` exists in `public.schemes`. Nonexistent schemes return `404 Not Found`.
2. **Duplicate Handling**:
   - The unique compound index `(user_id, scheme_id)` prevents duplicates.
   - If already bookmarked, the API responds idempotently with `{"status": "already_saved", "saved": true, "message": "Scheme already saved in your bookmarks."}` without creating duplicate rows or erroring.
3. **Safe Deletion**:
   - Calling `DELETE /api/saved-schemes/{scheme_id}` deletes strictly from `saved_schemes` where `user_id = auth.uid()` AND `scheme_id = scheme_id`.
   - The underlying welfare scheme in the `schemes` table is **never deleted**.

---

## Live Activity & Expired Saved Schemes

Saved schemes are bookmarks, not frozen eligibility evaluations.
When the citizen navigates to `/saved-schemes`:
- The backend retrieves the current scheme record and runs `get_scheme_activity(scheme)`.
- If a scheme's deadline has passed since it was bookmarked, `activity_status` is dynamically calculated as `"EXPIRED"`, and `deadline_status` as `"EXPIRED"`.
- The frontend renders the authoritative `"Expired"` badge, ensuring citizens are never misled into thinking a past-deadline scheme remains actionable.

---

## Frontend Behavior & Empty State

- **`SchemeCard.jsx`**:
  - Displays `"🔖 Save Scheme"` when unsaved.
  - Toggles to `"Saved ✓"` when saved.
  - In `/saved-schemes`, provides a dedicated `"🗑️ Remove"` button.
- **`SchemeDetails.jsx`**:
  - Includes a primary bookmark toggle in the details CTA bar (`"🔖 Save Scheme"` / `"Saved to Bookmarks ✓"`).
- **`SavedSchemes.jsx`**:
  - Displays saved schemes count and cards.
  - If the citizen has zero saved schemes, renders a clean, truthful empty state:
    > *"No saved schemes yet. Save government schemes you want to review later."*
    > Button: *"Find Government Schemes"* → navigates to `/recommendations`.
  - Zero fake schemes or mock data are used.
