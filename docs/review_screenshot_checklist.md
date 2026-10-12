# Mini-Project Review Screenshot Checklist

**Project:** AI-Powered Government Scheme Recommendation System  
**Review Type:** College Mini-Project Technical Evaluation & Demonstration  
**Safety & Security Note:** **DO NOT** include live API keys (`PARSE_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`) or production database passwords in any presentation slides or report screenshots.

---

## 18 Required Review Screenshots

| # | Screenshot Name | File Name Recommendation | Viewport / Route | Key Visual Elements to Highlight | Evaluator Focal Point |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Landing Page** | `01_landing_page.png` | Desktop 1080p (`/`) | Hero title, subtitle, "Get Started" and "Browse Schemes" call-to-actions, stats counter (62 Real Tamil Nadu Schemes), modern design system. | Demonstrates responsive UI, civic mission statement, and intuitive accessibility for everyday citizens. |
| **2** | **Register Page** | `02_register_page.png` | Centered Modal (`/register`) | Registration card with Full Name, Email, Password fields, client-side validation hints, link to Sign In. | Integration with Supabase Auth for citizen account provisioning with encrypted password handling. |
| **3** | **Login Page** | `03_login_page.png` | Centered Modal (`/login`) | Clean credentials form, Remember Me option, error handling state for invalid credentials. | Secure JWT token acquisition and session initialization. |
| **4** | **Citizen Profile** | `04_profile_page.png` | Form View (`/profile`) | Demographic inputs: Age (19), Gender (Female), Annual Family Income (₹1,20,000), Occupation (Student), Education (Higher Secondary), Social Category (General). | Comprehensive citizen profile modeling required for multi-dimensional eligibility evaluation. |
| **5** | **State & District Selection** | `05_state_district_selection.png` | Dropdown Close-up (`/profile`) | State dropdown showing **Tamil Nadu** (`state_id = 23`) and cascading District dropdown showing **Chennai** or **Coimbatore**. | Relational geographic hierarchy; dynamic district retrieval via foreign-key constraint. |
| **6** | **Recommendation Results** | `06_recommendations_grid.png` | Grid View (`/recommendations`) | Ranked scheme cards displaying Scheme Title, Match Score (e.g. 85%), Eligibility Badge (`ELIGIBLE`), Deadline Badge, and action buttons. | Two-stage pipeline: Geographic pre-filtering followed by deterministic eligibility assessment. |
| **7** | **Eligibility Explanation** | `07_eligibility_explanation.png` | Criteria Breakdown / Modal | Itemized checklist: Age (PASS), Gender (PASS), State (PASS), Income (PASS) with explicit rationale for each rule. | Explainable AI (XAI) principle: Citizens know exactly why they qualify without opaque algorithmic guesswork. |
| **8** | **Scheme Details** | `08_scheme_details.png` | Scheme View (`/schemes/:id`) | Header with Administering Department (e.g. *Social Welfare and Women Empowerment Department*), Overview tags, Scheme Summary. | Single-source-of-truth representation joining metadata, eligibility, documents, and provenance. |
| **9** | **Benefits & Documents** | `09_benefits_and_documents.png` | Middle Section (`/schemes/:id`) | Financial assistance description and the Required Documents list with badges (`Mandatory` vs. `Requirement Unspecified`). | Handling statutory ambiguity: Unconfirmed document mandates are never falsely asserted as mandatory. |
| **10** | **Application Procedure** | `10_application_procedure.png` | Lower Section (`/schemes/:id`) | Step-by-step guidance for Online and Offline submission modes, accompanied by the **"Visit Official Portal"** button. | Civic utility: Direct guidance to genuine government application channels (`.gov.in` / `.nic.in`). |
| **11** | **Saved Schemes (Bookmarks)** | `11_saved_schemes.png` | Library View (`/saved-schemes`) | Collection of user-bookmarked schemes with real-time deadline status and quick access to application details. | Cross-session citizen persistence and user-isolated bookmark management. |
| **12** | **Notifications Page** | `12_notifications_page.png` | Center Card (`/notifications`) | Timeline of alerts: Upcoming application deadlines (e.g. *Urgent: 3 days remaining*), read/unread status badges. | Automated deadline monitoring and time-decay classification keeping citizens proactively informed. |
| **13** | **Chatbot (English Path)** | `13_chatbot_english.png` | Chat Widget (`/chat`) | Citizen query: *"I am a college student in Tamil Nadu. What schemes can I apply for?"* followed by contextual response with recommended schemes. | Natural Language Processing (NLP) conversational interface with strict eligibility guardrails. |
| **14** | **Chatbot (Tamil Path)** | `14_chatbot_tamil.png` | Chat Widget (`/chat`) | Citizen query in Tamil: *"நான் தமிழ்நாட்டில் படிக்கும் மாணவி..."* and response in natural Tamil explaining schemes. | Multilingual cross-lingual accessibility; inclusive service delivery for vernacular citizens. |
| **15** | **Supabase Database Tables** | `15_supabase_tables.png` | Supabase Studio Dashboard | Table browser showing `schemes` (62 rows), `scheme_eligibility` (62 rows), `scheme_documents` (314 rows), `scheme_sources` (103 rows). | Relational database schema integrity and real government dataset ingestion. |
| **16** | **Row-Level Security (RLS) Policies** | `16_supabase_rls_policies.png` | Supabase Studio Auth & RLS | RLS policy table showing `user_profiles`, `saved_schemes`, and `notifications` restricted strictly to `auth.uid() = user_id`. | Zero data leakage: Authenticated users cannot inspect or modify other citizens' private records. |
| **17** | **System Architecture Diagram** | `17_system_architecture.png` | High-Resolution Diagram | Multi-tier architecture: React Frontend $\leftrightarrow$ FastAPI Gateway $\leftrightarrow$ Deterministic Engine + AI Relevance Engine $\leftrightarrow$ Supabase PostgreSQL. | Clear separation of concerns between deterministic legal logic and probabilistic AI ranking. |
| **18** | **Database Relationship Diagram (ERD)** | `18_database_erd.png` | Entity-Relationship Diagram | Crow's foot notation linking `schemes` (1:1 with `scheme_eligibility`, 1:N with `scheme_documents`, 1:N with `scheme_sources`, N:1 with `states` and `scheme_categories`). | Relational schema design, 3NF normalization, and foreign-key referential integrity. |

---

## Guidelines for Capturing Presentation Screenshots

1. **Window Resolution:** Standardize browser window to **1920 $\times$ 1080** (Full HD) with 100% zoom.
2. **Clean Test State:** Use a realistic test profile (e.g. *19yo Student, Chennai*) rather than placeholder text like *"test test"*. *(Note: Use a temporary test account; credentials are not stored in project files.)*
3. **Redaction / Security:** Inspect all address bars, console logs, and network tabs before capturing; ensure no bearer tokens or private API keys appear in frame.
4. **Annotation:** Use consistent callout boxes (colored rectangles with brief labels) to draw the evaluators' attention directly to key architectural features (e.g. highlighting the distinction between `ELIGIBLE` status and `85% Match` score).
