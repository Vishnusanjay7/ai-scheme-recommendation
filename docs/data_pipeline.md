# Automatic Government Scheme Data Acquisition & Pipeline Specification

> **Phase:** 2 (Data Acquisition, Normalization, Validation, Deduplication, Persistence & Scheme API)  
> **Target Sources:** myScheme (MeitY/NeGD), data.gov.in (OGD), State Welfare Portals, Official Gazette Datasets  
> **Database:** Supabase PostgreSQL with RLS  
> **Pipeline Directory:** [`backend/app/data_pipeline/`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/data_pipeline/)

---

## 1. Overview & Core Principles

Phase 2 establishes an automated, robust data acquisition and harmonization pipeline for Indian Government welfare schemes.
It enforces the following core architectural rules:

1. **Official Data Exclusivity:** The pipeline never fabricates, hallucinates, or hardcodes synthetic schemes. Data originates solely from authorized government portals, official open data releases, or partner APIs.
2. **Access Governance & Ethical Compliance:** In strict adherence to web ethics and website terms of service:
   - Does not bypass CAPTCHAs, access controls, or rate limits.
   - Does not perform unauthorized web scraping of portals that forbid automated scraping.
   - Requires authorized partner credentials (e.g. MeitY API keys/MoUs) for direct live machine endpoints.
   - Operates via clean, modular adapters supporting both remote API feeds and verified official machine-readable dataset files.
3. **Deterministic Separation of Central & State Schemes:**
   - Central (Pan-India) schemes strictly have `state_id = NULL`.
   - State-specific schemes must map to one of India's 28 States or 8 Union Territories in the `states` reference table.
4. **Data Provenance:** Every imported record maintains complete lineage in `scheme_sources` (source URL, official portal, last verified timestamp).

---

## 2. Pipeline Architecture

```
                    ┌────────────────────────────────────────┐
                    │       Official Government Sources      │
                    │  (myScheme / data.gov.in / State APIs) │
                    └───────────────────┬────────────────────┘
                                        │
                                        ▼
                    ┌────────────────────────────────────────┐
                    │       Government Source Adapters       │
                    │      (app/integrations/government_     │
                    │               source.py)               │
                    └───────────────────┬────────────────────┘
                                        │ RawScheme Models
                                        ▼
                    ┌────────────────────────────────────────┐
                    │             Data Processor             │
                    │  - Whitespace & Name Canonicalization  │
                    │  - Safe Multi-Format Date Parsing      │
                    │  - Level & State/Category Normalization│
                    └───────────────────┬────────────────────┘
                                        │ NormalizedScheme Models
                                        ▼
                    ┌────────────────────────────────────────┐
                    │             Data Validator             │
                    │  - URL structure validation            │
                    │  - Date chronological consistency      │
                    │  - Central/State foreign key integrity │
                    └───────────────────┬────────────────────┘
                                        │ Validated Candidates
                                        ▼
                    ┌────────────────────────────────────────┐
                    │          Deduplication Engine          │
                    │  Priority 1: External Scheme ID        │
                    │  Priority 2: Canonical Official URL    │
                    │  Priority 3: Name + Level + State Key  │
                    └───────────────────┬────────────────────┘
                                        │ Action: INSERT or UPDATE
                                        ▼
                    ┌────────────────────────────────────────┐
                    │      Supabase PostgreSQL Database      │
                    │  - schemes                             │
                    │  - scheme_eligibility                  │
                    │  - scheme_documents                    │
                    │  - scheme_sources (Provenance)         │
                    └────────────────────────────────────────┘
```

---

## 3. Component Details

### 3.1 Government Source Adapters ([`backend/app/integrations/government_source.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/integrations/government_source.py))

Defines an abstract base class `GovernmentSourceAdapter` exposing:
- `source_name: str`: Human-readable source identifier.
- `source_type: str`: Category (`NATIONAL_PORTAL`, `OGD_API`, `STATE_PORTAL`, `DATASET_FILE`).
- `base_url: str`: Canonical portal URL.
- `is_available() -> bool`: Verifies required environment credentials or files.
- `fetch_schemes() -> List[RawScheme]`: Acquires raw scheme instances.
- `fetch_scheme_details(id) -> Optional[RawScheme]`: Detailed scheme fetch.

#### Concrete Adapters:
- `MySchemeAdapter`: Integrates with the national platform (https://www.myscheme.gov.in/). Discloses that unauthenticated automated scraping is restricted, and requires `MYSCHEME_API_KEY` for live partner endpoints.
- `CentralGovernmentAdapter`: Integrates with Open Government Data India (https://data.gov.in/) requiring `DATA_GOV_IN_API_KEY`.
- `StateGovernmentAdapter`: Extensible for state portals (e.g., TNeGA, MahaDBT, Seva Sindhu).
- `OfficialFileDatasetAdapter`: Ingests authorized machine-readable JSON/CSV dataset exports published by ministries.

### 3.2 Data Processor ([`backend/app/data_pipeline/data_processor.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/data_pipeline/data_processor.py))

Transforms heterogeneous raw payloads into clean `NormalizedScheme` models:
- **Whitespace Sanitization:** Collapses tabs, carriage returns, and duplicate spaces.
- **Name Canonicalization:** Strips enclosing quotes, dangling punctuation, and excessive padding.
- **Safe Date Normalization:** Parses ISO-8601 (`YYYY-MM-DD`), Indian standard (`DD-MM-YYYY`, `DD/MM/YYYY`), and written dates (`31 May 2026`) safely into `YYYY-MM-DD`. Returns `None` for unparseable or open-ended ("ongoing") deadlines.
- **Government Level Normalization:** Strict resolution to `"CENTRAL"` or `"STATE"`.
- **State Enforcement:** 
  - For `CENTRAL` schemes, `state_id` is unconditionally forced to `NULL`.
  - For `STATE` schemes, maps the candidate state to one of the 36 official entries in `public.states`.
- **Category Resolution:** Normalizes input against the 14 official welfare categories in `public.scheme_categories`.

### 3.3 Data Validator ([`backend/app/data_pipeline/data_validator.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/data_pipeline/data_validator.py))

Rejects incomplete or corrupted data prior to database interaction:
- Name length $\ge 3$ characters.
- Valid `government_level` in `('CENTRAL', 'STATE')`.
- State consistency: State schemes must have valid `state_id`; Central schemes must not.
- URL structure: Ensures valid HTTP/HTTPS schemes and valid host domains.
- Chronology: Checks that `last_date` $\ge$ `start_date` if both are supplied.
- Returns structured `ValidationResult` with precise error messages.

### 3.4 Deduplication Engine ([`backend/app/data_pipeline/deduplication.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/data_pipeline/deduplication.py))

Determines whether incoming data represents a **genuinely new scheme** (`INSERT`) or an **updated version of an existing scheme** (`UPDATE`):
1. **Priority 1 (External ID):** Exact match on the official source's external identifier.
2. **Priority 2 (Canonical URL):** Canonical URL match on `official_url` or `source_url`.
3. **Priority 3 (Composite Key):** Matches on `(normalized_name, government_level, state_id)`.

When an existing scheme is detected, the pipeline performs an in-place update on `schemes`, preserves referential integrity, and updates `scheme_sources` and `last_updated` timestamps.

### 3.5 Database Persistence ([`backend/app/data_pipeline/importers/official_importer.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/data_pipeline/importers/official_importer.py))

Persists validated schemes to Supabase PostgreSQL across 4 relational tables:
1. `schemes`: Core welfare metadata.
2. `scheme_eligibility`: Structured numerical, demographic, and categorical constraints.
3. `scheme_documents`: Mandatory and optional documentation rules.
4. `scheme_sources`: Provenance citations and timestamps.

> **Security Note:** Due to PostgreSQL Row Level Security (RLS) on public tables, writing data requires server-side elevated privileges (`SUPABASE_SERVICE_ROLE_KEY`). Public clients only hold SELECT access.

---

## 4. Scheme Retrieval API Endpoints

FastAPI endpoints implemented in [`backend/app/routes/schemes.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/routes/schemes.py):

| Method | Endpoint | Query Parameters / Path | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/schemes` | `limit`, `offset`, `government_level`, `state_id`, `category_id`, `status` | Paginated list of public welfare schemes |
| `GET` | `/api/schemes/{scheme_id}` | `scheme_id` (UUID) | Comprehensive details with eligibility, documents, sources |
| `GET` | `/api/schemes/search` | `q` (min 1 char), `limit`, `offset` | Keyword search in scheme titles and descriptions |
| `GET` | `/api/schemes/state/{state_id}` | `state_id` (ID, Code 'TN', or Name), `limit`, `offset` | Schemes restricted to a specific State/UT |
| `GET` | `/api/schemes/central` | `limit`, `offset` | Pan-India Central Government schemes |
| `GET` | `/api/schemes/active` | `limit`, `offset` | Currently active welfare schemes |

---

## 5. CLI Execution & Scheduling

### Running Data Collection

Run in **Dry-Run Mode** (Default — verifies normalization, validation, and deduplication without modifying the database):
```bash
python backend/scripts/collect_schemes.py --dry-run
```

Run collection on an **Official Dataset File**:
```bash
python backend/scripts/collect_schemes.py --file tests/fixtures/official_scheme_template.json --dry-run
```

Execute **Live Database Persistence** (Requires `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`):
```bash
python backend/scripts/collect_schemes.py --file path/to/official_data.json --live
```

Target a **Specific Registered Source**:
```bash
python backend/scripts/collect_schemes.py --source "myScheme National Portal" --dry-run
```

### Running Periodic Updates

```bash
python backend/scripts/update_schemes.py --dry-run
```

### Scheduling Architecture

For production deployments, `collect_schemes.py` and `update_schemes.py` can be scheduled via:
- Linux `cron` (e.g. nightly sync at 02:00 AM UTC)
- Cloud scheduling services (AWS EventBridge, GitHub Actions Scheduled Workflows, Google Cloud Run Jobs)
- Supabase Edge Functions with `pg_cron`

---

## 6. How to Add a New Government Source

1. Subclass `GovernmentSourceAdapter` in [`backend/app/integrations/government_source.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/integrations/government_source.py):
   ```python
   class KeralaStatePortalAdapter(GovernmentSourceAdapter):
       @property
       def source_name(self) -> str:
           return "Kerala e-District Portal"

       @property
       def source_type(self) -> str:
           return "STATE_PORTAL"

       @property
       def base_url(self) -> str:
           return "https://edistrict.kerala.gov.in"

       def is_available(self) -> bool:
           return bool(os.getenv("KERALA_PORTAL_API_KEY"))

       def fetch_schemes(self, limit: Optional[int] = None) -> List[RawScheme]:
           ...
   ```
2. Register the new adapter with `SourceManager` in [`backend/app/data_pipeline/source_manager.py`](file:///C:/Users/vishn/ai-gov-scheme-recommender/backend/app/data_pipeline/source_manager.py).
3. The collector automatically discovers the adapter and processes its output through the normalization, validation, deduplication, and persistence pipeline.

---

## 7. Official Source Limitations & Compliance Notice

- **myScheme.gov.in:** Operates under Government of India NeGD/MeitY guidelines. Official automated access requires partner registration or National Data & Analytics Platform (NDAP) onboarding. The system provides the adapter interface and reports credentials status cleanly without violating terms of service.
- **data.gov.in:** Requires an official OGD API Key (`DATA_GOV_IN_API_KEY`).
- **District Registry (LGD):** Authoritative national district mappings (780+ districts) are designed to be imported from the Ministry of Panchayati Raj Local Government Directory (`lgdirectory.gov.in`). Representative districts are initially seeded in Phase 1.
