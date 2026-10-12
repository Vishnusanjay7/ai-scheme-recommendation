# Mini-Project Viva Voce Questions & Answers

**Project Title:** AI-Powered Government Scheme Recommendation System  
**Subject:** Software Engineering, Artificial Intelligence, Database Management Systems, Web Development  
**Target Audience:** Final Review / External Project Evaluators  

---

### Core Architectural & Technology Questions

#### 1. Why did you choose FastAPI over Flask or Django for the backend?
**Answer:** FastAPI was selected because:
1. It is natively asynchronous (built on Starlette and ASGI/Uvicorn), allowing it to handle concurrent AI API calls and database queries with high throughput.
2. It enforces automatic data validation and serialization through **Pydantic v2**, preventing malformed citizen inputs.
3. It automatically generates interactive OpenAPI/Swagger documentation (`/docs`) for rapid endpoint testing.

#### 2. Why did you choose React for the frontend?
**Answer:** React’s component-driven architecture allows us to build reusable UI elements (e.g., `EligibilityBadge`, `DeadlineBadge`, `SchemeCard`). Its virtual DOM and state management (React Context API) enable real-time UI synchronization when filtering schemes, toggling bookmarks, or updating demographic parameters without full page reloads.

#### 3. Why did you use Supabase?
**Answer:** Supabase provides an enterprise-ready, open-source Backend-as-a-Service (BaaS) built on PostgreSQL. It offers built-in **JWT Authentication**, real-time subscriptions, and out-of-the-box **Row-Level Security (RLS)**, allowing us to build a secure, cloud-hosted relational system without deploying and managing separate authentication servers.

#### 4. Why use PostgreSQL instead of a NoSQL database like MongoDB?
**Answer:** Government scheme eligibility is fundamentally relational and structured. A 3NF PostgreSQL relational schema guarantees **ACID transactions**, strict foreign-key referential integrity (linking schemes to states, categories, eligibility, documents, and sources), and enables complex multi-table joins. NoSQL lacks the relational constraints required to prevent orphaned documents or inconsistent state mappings.

---

### Eligibility Engine & AI Questions

#### 5. What is the Deterministic Eligibility Engine and why is it necessary?
**Answer:** The Deterministic Eligibility Engine is a rule-based algorithm written in Python that mathematically compares a citizen’s profile against statutory criteria (age bounds, income ceiling, gender, caste, state, education). It is necessary because legal welfare eligibility requires 100% reproducible accuracy with zero margin for error or algorithmic hallucination.

#### 6. Why not use Generative AI / LLMs alone to evaluate citizen eligibility?
**Answer:** Large Language Models are probabilistic next-token predictors. If an LLM alone decided eligibility, it could hallucinate criteria, confuse maximum and minimum age thresholds, or falsely declare an ineligible citizen eligible. In welfare distribution, a false positive wastes citizen money and administrative time. Therefore, legal qualification is strictly deterministic.

#### 7. What is Natural Language Processing (NLP) in the context of your project?
**Answer:** NLP is the branch of AI that enables computers to understand, interpret, and generate human language. In our project, NLP is utilized in two places:
1. In the **AI Recommendation Engine**, where user search queries (e.g., *"scholarship for female engineering student"*) are semantically matched against scheme descriptions.
2. In the **Multilingual Chatbot**, where natural conversations in English and Tamil are processed into structured intent.

#### 8. How does the Chatbot work under the hood?
**Answer:** When a citizen sends a message, the chatbot endpoint (`POST /api/chat`) performs:
1. Language detection (identifying English or Tamil).
2. Context injection: retrieves the citizen's profile from the session (age, gender, state) and injects it into a structured system prompt.
3. Service reuse: calls the `DeterministicEligibilityEngine` to query verified candidate schemes.
4. Generative synthesis: uses OpenAI `gpt-4o-mini` to construct a conversational, empathetic response in the citizen's chosen language, citing official steps without altering the citizen's database profile.

#### 9. What is the Match Score (0–100) and how is it calculated?
**Answer:** The Match Score is a multi-factor index of **relevance, urgency, and alignment**. It is calculated after deterministic eligibility has confirmed that the citizen qualifies. The scoring matrix allocates up to 40 points for query/occupational alignment, 15 points for income priority, 10 points for demographic provisions, 10 points for geographic specificity (State vs Central), and 10 points for application deadline urgency.

#### 10. Why is the Match Score kept strictly different from Eligibility?
**Answer:** Eligibility is binary/three-state legal qualification (`ELIGIBLE`, `POSSIBLY_ELIGIBLE`, `NOT_ELIGIBLE`). A citizen cannot be "85% legally eligible." Conflating relevance with eligibility misleads citizens into believing their approval is partially guaranteed. The Match Score represents priority and fit, never legal permission to receive funds.

---

### Deadlines, Temporal Logic & Deduplication

#### 11. How does the system monitor application deadlines?
**Answer:** The system implements a temporal classification algorithm (`DeadlineService`) that compares the current system timestamp against the scheme's `scheme_close_date`. It categorizes active schemes into `PERMANENT`, `NO_DEADLINE`, `APPROACHING` ($\le 7$ days), `URGENT` ($\le 3$ days), `CLOSING_TODAY`, or `EXPIRED`.

#### 12. What happens when a scheme has no closing date (`NO_DEADLINE`)?
**Answer:** In official gazettes, many welfare schemes operate on an ongoing annual basis without an explicit closing date. However, **`NO_DEADLINE` does not automatically mean `OPEN`**. Our system inspects the source text: if explicit application evidence exists, it is classified as `ActivityStatus.OPEN`; if evidence is missing (e.g. inactive archive schemes), it evaluates to `ActivityStatus.UNKNOWN` and is withheld from active recommendations to prevent sending citizens to defunct portals.

#### 13. How are duplicate schemes prevented during data ingestion?
**Answer:** Deduplication is enforced at three levels:
1. Database Unique Constraint on the `slug` column (`ALTER TABLE schemes ADD CONSTRAINT unique_slug UNIQUE (slug)`).
2. String sanitization and slug normalization in `DataProcessor`.
3. Ingestion pipeline check: queries existing slugs before performing insert or upsert operations.

---

### Security, Authentication & Data Protection

#### 14. What is Row-Level Security (RLS) and why is it critical?
**Answer:** RLS is a PostgreSQL security feature that evaluates security policies at the database row level for every SQL query. Even if a malicious user uses the public Supabase API key to execute `SELECT * FROM user_profiles`, PostgreSQL evaluates the policy `auth.uid() = id` and returns **0 rows**, ensuring complete data isolation between citizens.

#### 15. What is the Supabase Service-Role Key and how is it secured?
**Answer:** The `SUPABASE_SERVICE_ROLE_KEY` is an administrative credential that bypasses Row-Level Security. It is strictly stored in `backend/.env` and loaded exclusively into backend pipeline scripts. It is never exposed in API responses or committed to GitHub (`.gitignore`).

#### 16. Why must the Service-Role Key NEVER be included in the React frontend?
**Answer:** React is executed inside the user's web browser. Any environment variable bundled by Vite (e.g. `VITE_SERVICE_ROLE_KEY`) is embedded directly in plaintext in compiled JavaScript files (`assets/index-*.js`). A user could inspect the code and gain full administrative write/delete access over the entire production database.

---

### Data Pipeline & Normalization Questions

#### 17. How is government scheme data acquired?
**Answer:** Scheme data is acquired through a batch ingestion pipeline that connects to MyScheme records via a third-party Parse API scraper layer. The pipeline fetches search catalog summaries, downloads complete JSON detail records, normalizes the unstructured fields, extracts document prerequisites, and upserts them into our Supabase PostgreSQL schema.

#### 18. Why use an API access layer instead of scraping MyScheme directly?
**Answer:** The prototype accesses MyScheme-derived data through a third-party API access layer (Parse); this is not the official MyScheme API. Official government portals implement rate limiters, anti-bot protections, and dynamic client-side rendering. Using an audited API layer provides structured JSON responses, eliminates IP-banning risks, guarantees reproducible imports, and isolates the data pipeline behind a consistent interface.

#### 19. How are official government URLs validated?
**Answer:** Government application links are passed through an anti-phishing sanitizer in `MySchemeNormalizer`. The system verifies that URLs belong strictly to verified `.gov.in`, `.nic.in`, or official state domains (e.g. `tn.gov.in`). Third-party blog or aggregator URLs are strictly excluded from the `official_url` field.

#### 20. How are required documents handled when gazette information is incomplete?
**Answer:** Each document record in `scheme_documents` possesses an `is_mandatory` boolean. When a gazette text explicitly mandates a document (e.g. *"Aadhaar card is compulsory"*), it is marked `True` (`Mandatory`). If the text does not specify whether it is mandatory or optional, it is marked `None` and rendered as **"Requirement Unspecified"** in the UI, ensuring zero false assertions.

#### 21. How are complex natural-language eligibility conditions handled?
**Answer:** Conditions that cannot be parsed into standard relational columns (such as *"applicant must cultivate pulses"* or *"residence of not less than 10 years"*) are captured in the `other_conditions` JSONB column. The deterministic engine flags these as `UNKNOWN`, routing the scheme to `POSSIBLY_ELIGIBLE` ("Verification Required") and presenting the citizen with the exact clause requiring manual verification.

---

### System Integration & Scalability Questions

#### 22. How are deadline notifications triggered?
**Answer:** The notification service evaluates active schemes saved by citizens. When the deadline classification shifts to `URGENT` ($\le 3$ days) or `APPROACHING` ($\le 7$ days), a notification record is inserted into the `notifications` table linking the citizen's user ID, scheme title, and urgency message, accompanied by an unread flag.

#### 23. How is multilingual support (Tamil/English) implemented?
**Answer:** Multilingual support is implemented at the conversational NLP layer. The chatbot detects language markers; when Tamil is detected, the LLM is instructed via system prompt instructions to synthesize responses in standard, formal Tamil using appropriate administrative vocabulary, ensuring accessible communication for vernacular citizens.

#### 24. What are the primary limitations of the current implementation?
**Answer:**
1. *Geographic Scope:* The current live database contains 62 imported Tamil Nadu schemes. The architecture supports expansion to Central and other State/UT schemes, but full nationwide scheme population is not yet complete.
2. *API Credit Constraints:* Synchronization is throttled by third-party Parse API quota limits.
3. *Manual Document Verification:* Department-specific conditions cannot be validated automatically without direct integration with DigiLocker or e-Seva APIs.

#### 25. How can the system scale to support all 28 States and 8 Union Territories?
**Answer:** The database schema is already normalized with a master `states` table (36 rows representing 28 States and 8 Union Territories). Scaling to all states requires executing our `OptimizedMySchemeImporter` with pagination across other state codes (e.g., `MH`, `KA`, `UP`). Because state filtering is performed at the query level (`state_id = user_state_id OR government_level = 'CENTRAL'`), the recommendation engine scales with $O(N)$ candidate filtering without architectural changes.

#### 26. What is the difference between an authenticated citizen and a guest user?
**Answer:** An authenticated citizen's profile is securely stored in the `user_profiles` database table and protected by RLS. A guest user provides ephemeral in-memory demographic inputs that are evaluated in transient FastAPI memory without writing to the database, ensuring privacy for casual visitors.

#### 27. How did you verify system quality and stability?
**Answer:** System stability was validated through:
* **247 Pytest backend tests** covering schema integrity, RLS, eligibility rules, and deadline logic.
* **20 Vitest frontend tests** verifying badge rendering, UI state, and user actions.
* **Oxlint static code analysis** (0 errors, 0 warnings).
* **Vite production build** verification.

#### 28. What happens if the OpenAI API goes offline or encounters rate limits?
**Answer:** The `RecommendationService` implements a **Deterministic Fallback Matrix**. If the OpenAI API throws an exception or times out, the system automatically falls back to an internal mathematical ranking algorithm based on demographic matching and deadline proximity, ensuring zero downtime for the citizen.

#### 29. Can the chatbot modify the citizen's stored profile?
**Answer:** No. The chatbot endpoint (`POST /api/chat`) is strictly read-only with respect to `user_profiles`. It does not execute SQL `UPDATE` or `INSERT` statements against the user's demographic profile, preventing conversational drift from corrupting stored records.

#### 30. What is Explainable AI (XAI) and how is it reflected in your project?
**Answer:** Explainable AI refers to methods that allow humans to understand and trust the results created by machine learning algorithms. In our project, rather than presenting a black-box percentage, we display an itemized breakdown of every statutory criterion (Age, Income, Gender, State), explaining why each rule passed, failed, or requires manual verification.
