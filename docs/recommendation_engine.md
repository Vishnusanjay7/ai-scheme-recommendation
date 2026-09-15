# AI Recommendation Engine

## 1. Overview & Architecture

The **AI Recommendation Engine** provides intelligent, multi-factor relevance ranking of government welfare schemes for Indian citizens. It connects citizen needs, occupations, demographic attributes, and query context with schemes that provide maximum tangible utility.

```
                    ┌───────────────────────────────┐
                    │      Government Schemes       │
                    │   (Central + Resident State)  │
                    └───────────────┬───────────────┘
                                    ↓
                    ┌───────────────────────────────┐
                    │ Deterministic Eligibility (P3)│
                    │   - Evaluate legal rules      │
                    │   - Discard NOT_ELIGIBLE      │
                    │   - Queue POSSIBLY_ELIGIBLE   │
                    └───────────────┬───────────────┘
                                    ↓
                         🟢 ELIGIBLE Candidates
                                    ↓
                    ┌───────────────────────────────┐
                    │  Activity & Deadlines (P4)    │
                    │   - Keep only OPEN schemes    │
                    │   - Discard EXPIRED/INACTIVE  │
                    └───────────────┬───────────────┘
                                    ↓
                         🟢 ACTIONABLE Candidates
                                    ↓
                    ┌───────────────────────────────┐
                    │ AI Recommendation Engine (P5) │
                    │   - OpenAI Structured Ranking │
                    │   - Explainable Fallback      │
                    └───────────────┬───────────────┘
                                    ↓
                         Ranked Recommendations
                         (Match Score: 0–100)
```

### Cardinal Invariant: Separation of Eligibility vs Relevance
The AI recommendation engine **never** determines legal qualification.
- **Eligibility (Phase 3 Engine)**: A binary/ternary legal determination (`ELIGIBLE`, `POSSIBLY_ELIGIBLE`, `NOT_ELIGIBLE`) computed deterministically from government guidelines.
- **Relevance Match Score (Phase 5 Engine)**: A prioritization metric (`0–100`) indicating how well an already-qualified scheme fits the user's specific context, stated needs, and urgency.

> [!IMPORTANT]
> A match score of `87` means **"Relevance Match: 87/100"**. It must **never** be presented as "87% Eligible".

---

## 2. Multi-Stage Pipeline Breakdown

### Stage 1: Geographic Pre-Filter
- Public schemes operate at either `CENTRAL` (pan-India) or `STATE` level.
- Candidate schemes retrieved are strictly:
  1. Central government schemes.
  2. Schemes belonging to the citizen's designated `state_id`.
- Schemes belonging to any other state are pruned immediately before rule evaluation.

### Stage 2: Deterministic Eligibility Pre-Filter
- Runs `DeterministicEligibilityEngine.evaluate_eligibility(profile, scheme, rules)`.
- Scheme candidates are categorized:
  - `ELIGIBLE`: Qualified to proceed to activity filtering.
  - `POSSIBLY_ELIGIBLE`: Pruned from main recommendations and placed into a separate `verification_required` response queue.
  - `NOT_ELIGIBLE`: Completely discarded.

### Stage 3: Registration Activity & Deadline Pre-Filter
- Runs `get_scheme_activity(scheme)` from the Phase 4 Deadline Engine.
- Checks actionability in Indian Standard Time (`Asia/Kolkata`):
  - `OPEN`: Proceed to ranking.
  - `EXPIRED`, `NOT_YET_OPEN`, `INACTIVE`, `UNKNOWN`: Strictly discarded.
- Expired schemes never appear in recommendations.

### Stage 4: Multi-Factor Relevance Ranking
The remaining candidate pool consists of schemes that are **both verified ELIGIBLE and currently OPEN**.
The engine ranks them via:
1. **OpenAI Structured Ranking** (primary when configured and available).
2. **Deterministic Fallback Ranking** (automatic fallback if OpenAI is unconfigured, times out, or errors).

---

## 3. OpenAI Integration & Security Controls

### Server-Side Isolation
- The OpenAI API key (`OPENAI_API_KEY`) is kept strictly server-side and never exposed to the frontend client or version control.
- Managed via `app.integrations.openai_service.OpenAIService`.

### Data Minimization
To protect citizen privacy, private identifiable information is stripped before sending context to the model:
- **Included**: Age, state name, district name, occupation, education, social category, disability status, and user query string.
- **Excluded**: Citizen user ID, database primary keys, passwords, authentication tokens, contact numbers, family records, and internal schema identifiers.

### System Prompt Safety
The model receives explicit boundaries:
```
1. Eligibility has ALREADY been legally determined by a deterministic legal rule engine.
   Every single candidate scheme is 100% ELIGIBLE and OPEN.
2. DO NOT evaluate or alter eligibility. Your sole job is to rank these already-eligible schemes.
3. Score each scheme from 0 to 100 based on fit, utility, and expressed need.
4. Only rank schemes from the provided candidate list. Never invent external schemes.
5. Never hallucinate scheme details, benefits, application URLs, or deadlines.
6. Return only valid structured JSON.
```

### Structured Output Validation
The LLM response is parsed and validated against the `AIRankingOutput` Pydantic model:
- Any `scheme_id` not in the candidate set is discarded.
- Scores outside `[0, 100]` are safely clamped.
- Repeated scheme IDs are deduplicated.
- If the AI omits any candidate schemes, the engine automatically supplements them with deterministic fallback scores.

---

## 4. Deterministic Fallback Ranking

When OpenAI is unavailable, the platform seamlessly uses `DeterministicFallbackRanker`:

| Factor | Weight | Evaluation Criteria |
|---|---|---|
| **Base Qualified Score** | 35 pts | Awarded to all schemes confirmed ELIGIBLE and OPEN |
| **Query Keyword Match** | Up to 25 pts | Matches between user search terms and scheme name, summary, and benefits |
| **Occupation Alignment** | Up to 15 pts | Scheme provisions matching citizen's occupation (e.g. Farmer, Student, Artisan) |
| **Demographic Inclusivity** | Up to 10 pts | Targeted provisions for citizen's category (SC/ST/OBC) or disability status |
| **Geographic Specificity** | Up to 10 pts | State-specific programs tailored to the citizen (+10) vs Central schemes (+5) |
| **Deadline Urgency** | Up to 10 pts | `CLOSING_TODAY` (+10), `URGENT` (+8), `APPROACHING` (+4) |

### Transparent Explanations
Fallback justifications are composed from real facts:
- *"Highly relevant to your occupation (Farmer)"*
- *"Matches your search interest in 'subsidy, loan'"*
- *"State-specific program tailored for your resident state"*
- *"Application deadline is urgent (3 day(s) remaining)"*

---

## 5. Security & Authentication Architecture

In strict alignment with the Phase 3 security audit:
- Authenticated requests resolve citizen identity via `auth.uid()`.
- **Cross-user isolation**: Requesting another user's recommendations via `user_id` returns `403 Forbidden`.
- **Profile override prevention**: Authenticated users cannot submit arbitrary profile overrides in the request body or query params; profile data is always loaded server-side from `user_profiles`.
- **Guest requests**: Unauthenticated requests may provide in-memory demographic attributes, but attempting to supply a `user_id` returns `401 Unauthorized`.
- Client-supplied scores, eligibility statuses, or ranks are never trusted.

---

## 6. API Reference

### `POST /api/recommendations`
**Request:**
```json
{
  "query": "I am a farmer looking for financial assistance with crop seeds",
  "limit": 10,
  "offset": 0
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "scheme_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "scheme_name": "PM Kisan Samman Nidhi",
      "eligibility_status": "ELIGIBLE",
      "relevance_score": 94,
      "relevance_reason": "Highly relevant to your occupation (Farmer). Matches your search interest in 'farmer, financial'. Central government pan-India program.",
      "activity_status": "OPEN",
      "deadline_status": "NO_DEADLINE",
      "days_remaining": null,
      "benefits": "₹6,000 per year direct income support in three equal installments",
      "official_url": "https://pmkisan.gov.in",
      "government_level": "CENTRAL",
      "state_id": null
    }
  ],
  "verification_required": [],
  "total_candidates": 1,
  "ranking_method": "DETERMINISTIC_FALLBACK",
  "query_used": "I am a farmer looking for financial assistance with crop seeds"
}
```
