# Database Design Specification

> **Status:** Placeholder (Phase 0)  
> The detailed database design, entity-relationship diagrams, table definitions, indexes, and Row Level Security (RLS) policies will be completed in Phase 1.

## Planned Tables

- `users` (managed by Supabase Auth)
- `user_profiles` (citizen demographic, financial, and educational profile data)
- `states` & `districts` (standard geographic reference)
- `scheme_categories` (agriculture, education, healthcare, social welfare, etc.)
- `schemes` (master scheme records from official government sources)
- `scheme_eligibility` (structured deterministic criteria for age, income, caste, etc.)
- `scheme_documents` (mandatory and supporting document requirements)
- `scheme_sources` (source provenance and official application URLs)
- `saved_schemes` (user bookmarked schemes)
- `notifications` (in-app notifications and deadline alerts)
- `chat_history` (user chatbot interaction sessions)
