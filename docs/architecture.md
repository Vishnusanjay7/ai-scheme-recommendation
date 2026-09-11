# Architecture Overview

> **Status:** Placeholder (Phase 0)  
> Detailed system architecture diagrams, data flow models, and interaction specifications will be completed during subsequent implementation phases.

## High-Level Architecture Components

1. **Frontend (Citizen Web Portal):**
   - Built with React + Vite (JavaScript).
   - Direct integration with Supabase Auth for citizen login/registration.
   - Communicates with FastAPI backend for scheme eligibility, recommendations, search, and chatbot.

2. **Backend API (FastAPI):**
   - Python FastAPI asynchronous server.
   - Modular routes for profiles, scheme queries, recommendations, and assistance.
   - Rule-based Eligibility Engine (strictly deterministic: Eligible / Possibly Eligible / Not Eligible).
   - AI Relevance & Ranking Engine (OpenAI API used solely for ranking and natural language interactions).

3. **Data Layer (Supabase PostgreSQL):**
   - Relational schema enforcing referential integrity.
   - Row Level Security (RLS) ensuring strict privacy for citizen profiles and saved schemes.
   - Official scheme registry with indexed categories, states, and eligibility rules.

4. **Scheme Data Acquisition & Ingestion Pipeline:**
   - Independent data acquisition module for verified official Indian government schemes (myScheme.gov.in standards).
