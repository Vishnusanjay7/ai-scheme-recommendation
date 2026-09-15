# Deterministic Scheme Eligibility Engine Specification

> **Phase:** 3 (Deterministic Eligibility Engine & Assessment API)  
> **Core Principle:** Strict Rule-Based Logic with Zero AI/LLM Hallucination  
> **Engine Location:** [`backend/app/services/eligibility_engine.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/services/eligibility_engine.py)  
> **Service Location:** [`backend/app/services/eligibility_service.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/services/eligibility_service.py)  
> **API Location:** [`backend/app/routes/eligibility_routes.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/routes/eligibility_routes.py)

---

## 1. Overview & Core Philosophy

The **Deterministic Scheme Eligibility Engine** evaluates citizen demographic, geographic, and socio-economic profiles against statutory government scheme criteria.

### Fundamental Non-Negotiable Rules
1. **Zero LLM Dependency:** Eligibility is a legal and factual determination. The system **never** prompts an LLM or neural network to decide if a citizen qualifies for government benefits.
2. **Three-State Criterion Logic:** Every mandatory criterion is evaluated to exactly one of three states:
   - `PASS`: The citizen meets or exceeds the criterion.
   - `FAIL`: The citizen explicitly violates the criterion.
   - `UNKNOWN`: The citizen profile lacks required information to determine compliance.
3. **No Match Percentage:** The system **never** outputs percentages like *"72% eligible"*. A citizen is either legally eligible, potentially eligible pending information, or ineligible. (A future Phase recommendation engine may calculate a separate relevance/interest score, which will never override legal eligibility).
4. **Reproducibility:** Given identical inputs (Citizen Profile + Scheme Criteria), the engine always produces the exact same verdict and itemized explanation.

---

## 2. Core Eligibility Statuses

Every scheme evaluation aggregates into exactly one of three statuses:

| Status | Display Symbol | Meaning | Aggregation Condition |
| :--- | :--- | :--- | :--- |
| `ELIGIBLE` | 🟢 **Eligible** | The citizen qualifies for the scheme. | **All** mandatory criteria evaluate to `PASS`. |
| `POSSIBLY_ELIGIBLE` | 🟡 **Possibly Eligible** | The citizen satisfies all known rules, but lacks some data. | **Zero** criteria evaluate to `FAIL`, and **$\ge 1$** criterion evaluates to `UNKNOWN`. |
| `NOT_ELIGIBLE` | 🔴 **Not Eligible** | The citizen does not qualify. | **$\ge 1$** mandatory criterion evaluates to `FAIL`. |

---

## 3. Decision Logic by Criterion

```
                         Citizen Profile + Scheme Rules
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        Individual Criterion Check             Individual Criterion Check
          (e.g., Age, Income, State)           (e.g., Category, Gender)
                    │                                     │
         ┌──────────┼──────────┐               ┌──────────┼──────────┐
         ▼          ▼          ▼               ▼          ▼          ▼
        PASS       FAIL     UNKNOWN           PASS       FAIL     UNKNOWN
         │          │          │               │          │          │
         └──────────┼──────────┴───────────────┴──────────┼──────────┘
                    │                                     │
                    ▼                                     ▼
       Does ANY Criterion FAIL? ────────► YES ────► NOT_ELIGIBLE (🔴)
                    │
                    NO
                    │
       Is ANY Criterion UNKNOWN? ───────► YES ────► POSSIBLY_ELIGIBLE (🟡)
                    │
                    NO
                    │
                    ▼
               ELIGIBLE (🟢)
```

### 3.1 Age Constraints (`min_age`, `max_age`)
- If `min_age` exists:
  - `user_age < min_age` $\rightarrow$ `FAIL`
  - `user_age >= min_age` $\rightarrow$ `PASS`
  - `user_age is None` $\rightarrow$ `UNKNOWN`
- If `max_age` exists:
  - `user_age > max_age` $\rightarrow$ `FAIL`
  - `user_age <= max_age` $\rightarrow$ `PASS`
  - `user_age is None` $\rightarrow$ `UNKNOWN`
- If both exist, both bounds must pass for `PASS`.

### 3.2 Income Ceiling (`max_income`)
- If `max_income` exists:
  - `user_income > max_income` $\rightarrow$ `FAIL`
  - `user_income <= max_income` $\rightarrow$ `PASS`
  - `user_income is None` $\rightarrow$ `UNKNOWN`
- Note: No arbitrary minimum income is inferred unless explicitly mandated.

### 3.3 Gender Restriction (`gender`)
- Schemes specifying `"ALL"`, `"ANY"`, or `NULL` impose no restriction (`PASS`).
- Schemes specifying a gender (e.g. `"FEMALE"`):
  - `user_gender == required_gender` $\rightarrow$ `PASS`
  - `user_gender != required_gender` $\rightarrow$ `FAIL`
  - `user_gender is None` $\rightarrow$ `UNKNOWN`

### 3.4 Disability Requirement (`disability_required`)
- If `disability_required == False`: No restriction (`PASS`).
- If `disability_required == True`:
  - `user_disability == True` $\rightarrow$ `PASS`
  - `user_disability == False` $\rightarrow$ `FAIL`
  - `user_disability is None` $\rightarrow$ `UNKNOWN`

### 3.5 State / Geographic Restrictions (`government_level`, `state_id`, `state_restriction`)
- **Central Schemes (`government_level == 'CENTRAL'`):**
  - Applicable across all Indian States & UTs (`PASS`), unless a specific `state_restriction` is attached.
- **State Schemes (`government_level == 'STATE'`):**
  - `user_state_id == scheme_state_id` $\rightarrow$ `PASS`
  - `user_state_id != scheme_state_id` $\rightarrow$ `FAIL`
  - `user_state_id is None` $\rightarrow$ `UNKNOWN`

### 3.6 District Restrictions (`district_restriction`)
- If `district_restriction is None`: No district filter is applied (`PASS`).
- If `district_restriction` is set:
  - `user_district_id == district_restriction` $\rightarrow$ `PASS`
  - `user_district_id != district_restriction` $\rightarrow$ `FAIL`
  - `user_district_id is None` $\rightarrow$ `UNKNOWN`

### 3.7 Social Category (`category`)
- Matches against normalized Indian welfare categories (`SC`, `ST`, `OBC`, `EWS`, `GENERAL`, `MBC`).
- Recognizes aliases (e.g. *"Scheduled Caste"* $\rightarrow$ `SC`, *"Other Backward Classes"* $\rightarrow$ `OBC`).
- Supports multi-category mandates (e.g. `SC, ST` allows either SC or ST).
- Missing category yields `UNKNOWN`.

### 3.8 Occupation Constraints (`occupation`)
- Normalized case-insensitive matching across agricultural, artisanal, and professional designations (e.g., *"Farmer"*, *"Artisan"*, *"Student"*).
- Missing occupation yields `UNKNOWN`.

### 3.9 Education Hierarchy (`education`)
A strict, ordinal tier scale (0–8) is enforced:

| Tier | Level | Standard Aliases / Equivalents |
| :---: | :--- | :--- |
| **0** | None / Illiterate | `none`, `illiterate`, `no formal education` |
| **1** | Primary | `primary`, `5th pass`, `class 5` |
| **2** | Middle / Upper Primary | `middle`, `8th pass`, `class 8` |
| **3** | Secondary | `10th`, `10th pass`, `matric`, `matriculation`, `sslc`, `high school` |
| **4** | Higher Secondary | `12th`, `12th pass`, `intermediate`, `plus two`, `+2`, `hsc` |
| **5** | Diploma / ITI | `diploma`, `polytechnic`, `iti`, `vocational` |
| **6** | Graduate / Bachelor's | `graduate`, `graduation`, `bachelor`, `bachelors`, `ug`, `b.a`, `b.sc`, `b.com`, `b.tech` |
| **7** | Postgraduate / Master's| `postgraduate`, `master`, `masters`, `pg`, `m.a`, `m.sc`, `m.com`, `m.tech`, `mba` |
| **8** | Doctorate / PhD | `doctorate`, `phd`, `ph.d`, `m.phil` |

- Where a scheme specifies minimum education (e.g. `GRADUATE`):
  - Citizen with `POSTGRADUATE` (Tier 7 $\ge$ 6) $\rightarrow$ `PASS`
  - Citizen with `PRIMARY` (Tier 1 < 6) $\rightarrow$ `FAIL`
  - Citizen with unspecified education $\rightarrow$ `UNKNOWN`

### 3.10 Other Conditions JSONB (`other_conditions`)
Structured conditions modeled deterministically:
- `marital_status`: Validates against `SINGLE`, `MARRIED`, `WIDOWED`, `DIVORCED`.
- `bpl_card`: Validates boolean Below Poverty Line cardholder status.
- `max_landholding_hectares`: Validates numerical landholding ceilings.
- **Unmodeled / Free-form Keys:** If an unknown key exists, it strictly evaluates to `UNKNOWN` with a clear notice: *"Condition requires manual verification or has an unsupported structure."* AI guessing is strictly prohibited.

---

## 4. Explanation Output Format

Every evaluation returns an itemized audit trail:

```json
{
  "scheme_id": "8f3b2c1a-5d4e-4f3a-9b8c-1e2d3c4b5a6f",
  "scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
  "government_level": "CENTRAL",
  "evaluation": {
    "status": "ELIGIBLE",
    "display_status": "🟢 Eligible",
    "summary": "All mandatory eligibility criteria are fully satisfied.",
    "criteria": [
      {
        "criterion": "age",
        "result": "PASS",
        "user_value": 35,
        "required": ">=18",
        "reason": "Citizen age (35) satisfies the age requirement (>=18)."
      },
      {
        "criterion": "occupation",
        "result": "PASS",
        "user_value": "Farmer",
        "required": "Farmer",
        "reason": "Citizen occupation ('Farmer') matches required occupation 'Farmer'."
      },
      {
        "criterion": "state",
        "result": "PASS",
        "user_value": "All India",
        "required": "No state restriction specified (All India)",
        "reason": "Pan-India Central Government scheme applicable across all States and Union Territories; no state restriction specified."
      }
    ],
    "passed_criteria_count": 3,
    "failed_criteria_count": 0,
    "unknown_criteria_count": 0
  }
}
```

If any mandatory criterion fails:
```json
{
  "status": "NOT_ELIGIBLE",
  "display_status": "🔴 Not Eligible",
  "summary": "Citizen is NOT ELIGIBLE. 1 mandatory eligibility criteria failed: 'annual_income'.",
  "criteria": [
    {
      "criterion": "annual_income",
      "result": "FAIL",
      "user_value": "₹350,000.00",
      "required": "<= ₹250,000.00",
      "reason": "Citizen annual income (₹350,000.00) exceeds the maximum ceiling of ₹250,000.00."
    }
  ],
  "passed_criteria_count": 2,
  "failed_criteria_count": 1,
  "unknown_criteria_count": 0
}
```

---

## 5. Scheme Eligibility API Endpoints

Mounted on the FastAPI router in [`backend/app/routes/eligibility_routes.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/routes/eligibility_routes.py):

### 5.1 Single Scheme Assessment
`POST /api/eligibility/evaluate`

Request Payload:
```json
{
  "scheme_id": "8f3b2c1a-5d4e-4f3a-9b8c-1e2d3c4b5a6f",
  "profile": {
    "age": 28,
    "gender": "FEMALE",
    "annual_income": 180000.00,
    "state_id": 23,
    "category": "OBC",
    "occupation": "Artisan"
  }
}
```

### 5.2 Bulk Scheme Discovery Evaluation
`GET /api/eligibility/schemes?age=28&gender=FEMALE&annual_income=180000&state_id=23`

Returns bulk evaluation of available schemes grouped by counts:
```json
{
  "total_evaluated": 12,
  "eligible_count": 5,
  "possibly_eligible_count": 4,
  "not_eligible_count": 3,
  "results": [...]
}
```

---

## 6. Security & Privacy Architecture

1. **Server-Side Evaluation:** The frontend client cannot dictate or tamper with eligibility results. Rules and citizen data are evaluated exclusively on the backend server.
2. **Citizen Privacy Isolation:** Authenticated user assessments verify ownership via `auth.uid()`. Citizens cannot view or evaluate other citizens' private profile data.
3. **Zero Secret Exposure:** Evaluation endpoints only expose public scheme metadata and deterministic explanations; service keys and private identity tokens are never returned.
