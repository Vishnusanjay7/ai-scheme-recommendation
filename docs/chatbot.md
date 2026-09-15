# Phase 9: AI/NLP Government Scheme Chatbot Documentation

## 1. Executive Summary & Architecture Overview

The **AI Government Scheme Chatbot** provides an intelligent, natural-language conversational interface for citizens seeking public welfare schemes. Built in strict accordance with the system's foundational security and architectural principles, **the LLM is NEVER used as the legal eligibility engine and cannot override statutory eligibility determinations**.

### Processing Pipeline

```
Citizen Natural Language Query (English or Tamil)
                  │
                  ▼
   1. Input Sanitization & Abuse Prevention (<= 2000 chars, non-empty)
                  │
                  ▼
   2. NLP Entity & Intent Extraction (OpenAI gpt-4o-mini / Deterministic Fallback)
      - Extracts: occupation, age, gender, state, disability, domain keywords
      - Explicit rule: Unstated attributes remain strictly NULL (no hallucination)
                  │
                  ▼
   3. Citizen Profile Merging
      - Authenticated: Server-side `user_profiles` is strictly AUTHORITATIVE
      - Query context provides temporary overrides only for missing/inquired fields
      - Database profile is NEVER mutated by chat queries
      - Guest: In-memory temporary query profile
                  │
                  ▼
   4. Phase 3: Deterministic Eligibility Engine
      - Statutory rules evaluated server-side
      - Criterion-by-criterion deterministic logic
      - Excludes NOT_ELIGIBLE schemes
                  │
                  ▼
   5. Phase 4: Active / Open Registration & Deadline Engine
      - Filters out INACTIVE, NOT_YET_OPEN, and EXPIRED schemes
      - Classifies urgency in Asia/Kolkata (IST) timezone
                  │
                  ▼
   6. Phase 5: AI Relevance Ranking Engine
      - Multi-factor contextual ranking (0–100)
      - Explicit invariant: Relevance Score is fit/priority, NOT eligibility
                  │
                  ▼
   7. Conversational Response Synthesis
      - Grounded strictly in factual scheme records from backend
      - Multilingual: Responds in English or Tamil matching user language
      - Truthful empty response when scheme records are 0
                  │
                  ▼
   8. Chat History Persistence
      - Persists to `public.chat_history` strictly for authenticated citizens
      - Isolated via `auth.uid() = user_id` Row-Level Security
```

---

## 2. NLP Entity Extraction & Structured Output

Natural language processing parses citizen queries into a strictly typed Pydantic model (`ChatIntent`):

| Attribute | Type | Description | Hallucination Constraint |
| :--- | :--- | :--- | :--- |
| `intent` | `str` | Classified user intent (`find_schemes`, `eligibility_query`, etc.) | Default: `find_schemes` |
| `query` | `str` | Normalized search terms | Preserves citizen intent |
| `language` | `str` | Detected language (`en` or `ta`) | Auto-detected from script / phrases |
| `age` | `Optional[int]` | Explicitly stated age in years | Must be `null` if unstated |
| `gender` | `Optional[str]` | Explicitly stated gender | Must be `null` if unstated |
| `state_name` | `Optional[str]` | Mentioned Indian state / UT | Normalized to official state |
| `occupation` | `Optional[str]` | Stated occupation (farmer, student, artisan, etc.) | Must be `null` if unstated |
| `disability_status` | `Optional[bool]`| Explicitly stated disability | Must be `null` if unstated |
| `keywords` | `List[str]` | Domain and need keywords | Extracted from message context |

### Fallback Deterministic Extractor
If OpenAI is unconfigured, rate-limited, times out, or returns invalid JSON, the service immediately invokes `_deterministic_extract_intent()`. This fallback uses regex and domain dictionaries to accurately extract numbers, occupations, states, and Tamil terms (`விவசாயி`, `மாணவர்`, `பெண்`, `தமிழ்நாடு`) without crashing or raising unhandled 500 errors.

---

## 3. Authoritative Profile Merge Rules

To prevent conversational context from corrupting official citizen records, explicit merge semantics are enforced:

1. **Authoritative Profile Supremacy**: If a citizen is authenticated, their server-side `user_profiles` record in Supabase is authoritative. If the stored profile has `age: 40, occupation: 'farmer'`, the chatbot prioritizes these values.
2. **Missing Field Completion**: Extracted entities from the chat message only populate fields that are currently `null` in the stored profile.
3. **Temporary Scoping Overrides**: If a citizen explicitly inquires about schemes in another state (e.g. *"I am inquiring about Karnataka schemes"*), the inquiry state is passed as a temporary search scope for that turn only.
4. **Zero Database Mutation**: The chat endpoint (`POST /api/chat`) performs read-only operations on `user_profiles`. It never invokes `update` or `insert` on citizen profile records.

---

## 4. Deterministic Eligibility & Deadline Integration

The chatbot directly delegates candidate retrieval and evaluation to the existing **Phase 5 Recommendation Engine**, which cascades through:
- **Phase 3 Deterministic Eligibility Engine**: Evaluates criteria (age bounds, gender, state jurisdiction, income ceiling, caste category, disability).
  - Schemes with `ELIGIBLE` status are presented as main recommendations.
  - Schemes with `POSSIBLY_ELIGIBLE` status are segregated under `verification_required` with an explicit notice.
  - Schemes with `NOT_ELIGIBLE` status are discarded.
- **Phase 4 Activity Engine**: Filters out non-actionable schemes, ensuring only `OPEN`, `EXTENDED`, and `ALWAYS_OPEN` opportunities are returned.

### Match / Relevance Score Distinction
- Displayed strictly as: `Match/Relevance Score: {score}/100`.
- The system **never** displays `92% eligible` or `92% chance of eligibility`.

---

## 5. Multilingual Support (English & Tamil)

The chatbot provides native bilingual support:
- **Language Detection**: Automatically inspects Unicode character ranges for Tamil script (`\u0b80` – `\u0bff`) and language indicators.
- **Tamil Query Support**: Seamlessly recognizes Tamil queries such as:
  - `"நான் ஒரு விவசாயி. எனக்கு அரசு உதவி திட்டங்கள் என்ன?"`
  - `"தமிழ்நாட்டில் மாணவர்களுக்கு என்ன அரசு திட்டங்கள் உள்ளன?"`
- **Grounded Translation**: Official scheme titles, statutory rules, and government URLs remain unaltered. Conversational greetings and explanations adapt to the citizen's detected language.

---

## 6. Truthful Handling of Zero Scheme Records

Because live official government source ingestion remains pending authorization, the connected database may contain zero live scheme records.

Under this scenario, the chatbot truthfully informs the citizen:
> *"Hello! I couldn't find any government scheme records in the connected database right now. The official-source acquisition pipeline is ready, but live scheme records are currently pending ingestion. Please check back soon."*

The LLM is barred from fabricating fake schemes (e.g., hallucinating PM Kisan details or imaginary state subsidies) to fill the void.

---

## 7. Data Minimization & Privacy Safeguards

The chatbot respects strict data minimization guidelines:
- Passwords, access tokens, and JWT credentials are **never** included in LLM prompts.
- Internal database primary keys are stripped from prompt contexts.
- Only the specific demographic fields required for query relevance (e.g., occupation, state name, age) are passed into OpenAI calls.

---

## 8. Chat History & Row-Level Security (RLS)

- **Persistence Table**: `public.chat_history` (`id`, `user_id`, `user_message`, `bot_response`, `language`, `created_at`).
- **Owner Enforcement**: Every stored conversation is tagged with `user_id = auth.uid()`.
- **Cross-User Protection**:
  - `GET /api/chat/history` enforces that queries filter strictly by `auth.uid()`.
  - Supabase Row-Level Security policies on `public.chat_history` reject cross-user SELECT, INSERT, and DELETE attempts.
- **Guest Conversations**: Interactions without authentication operate in-memory and are not persisted to the database.

---

## 9. API Specification

### `POST /api/chat`
Submits a conversational citizen question.

**Request Payload**:
```json
{
  "message": "I am a 24 year old farmer from Tamil Nadu. What schemes can I get?",
  "language": "en"
}
```

**Response Payload (`200 OK`)**:
```json
{
  "message": "Based on your background as a farmer in Tamil Nadu, I evaluated official schemes and found...",
  "language": "en",
  "intent": {
    "intent": "find_schemes",
    "query": "I am a 24 year old farmer from Tamil Nadu",
    "language": "en",
    "age": 24,
    "gender": null,
    "state_name": "Tamil Nadu",
    "occupation": "farmer",
    "keywords": ["agriculture", "farmer", "crop", "tamil nadu"]
  },
  "recommendations": [
    {
      "scheme_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "scheme_name": "PM Kisan Samman Nidhi",
      "eligibility_status": "ELIGIBLE",
      "relevance_score": 95,
      "relevance_reason": "Matches farmer demographic and agricultural focus",
      "activity_status": "OPEN",
      "deadline_status": "APPROACHING",
      "days_remaining": 14,
      "official_url": "https://pmkisan.gov.in"
    }
  ],
  "verification_required": [],
  "total_eligible_found": 1
}
```

### `GET /api/chat/history`
Retrieves previous conversational turns for the authenticated citizen.

**Headers**:
- `Authorization: Bearer <jwt_token>`

**Response Payload (`200 OK`)**:
```json
{
  "user_id": "d3b07384-d113-4672-8877-c335a09ad733",
  "total_messages": 2,
  "history": [
    {
      "id": "e4f80123-5678-4321-9876-abcdef012345",
      "user_id": "d3b07384-d113-4672-8877-c335a09ad733",
      "user_message": "Find schemes for students",
      "bot_response": "Here are schemes matching students...",
      "language": "en",
      "created_at": "2026-09-12T12:00:00Z"
    }
  ]
}
```

---

## 10. Verification & Test Coverage

- **Backend Pytest Suite**: 221 tests passing (197 previous + 24 Phase 9 tests), 0 failures.
- **Frontend Linter (`oxlint`)**: 0 warnings, 0 errors.
- **Frontend Build (`vite build`)**: Clean production bundle generated.
- **Database Schema**: Zero modifications to `database/schema.sql` (schema frozen).
