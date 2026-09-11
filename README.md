# AI-Powered Government Scheme Recommendation System

## Project Objective
The **AI-Powered Government Scheme Recommendation System** is designed to help Indian citizens easily discover, assess eligibility for, and apply to relevant Central and State government welfare schemes. 

By combining a **deterministic, rule-based eligibility engine** (guaranteeing legal/factual eligibility determination) with an **AI relevance & ranking engine** and an intuitive conversational assistant, the platform bridges the awareness and access gap between citizens and government benefits.

---

## Technology Stack

- **Frontend:** React, Vite, JavaScript, CSS
- **Backend:** Python (3.11+), FastAPI, Uvicorn, Pydantic
- **Database:** Supabase PostgreSQL (with Row-Level Security)
- **Authentication:** Supabase Auth
- **AI / NLP:** OpenAI API (for ranking, scheme summaries, and citizen chatbot)
- **External Data:** Official Indian Government sources (e.g., myScheme.gov.in standards)
- **Notifications:** In-app notifications & email alerts

> **Note on Supabase Configuration:** Full Supabase database tables, migration scripts, and RLS policies will be introduced in **Phase 1**.

---

## Project Structure

```text
ai-gov-scheme-recommender/
│
├── backend/
│   ├── .venv/                      # Python virtual environment (ignored in git)
│   ├── app/
│   │   ├── routes/                 # API endpoint routers
│   │   ├── services/               # Business logic (Eligibility Engine, AI Ranking)
│   │   ├── data_pipeline/          # Government scheme ingestion & seed pipeline
│   │   ├── integrations/           # Supabase & OpenAI client integrations
│   │   ├── models/                 # Pydantic schemas and data models
│   │   ├── utils/                  # Helper utilities and validators
│   │   └── main.py                 # FastAPI application entry point
│   ├── requirements.txt            # Backend dependencies
│   └── .env.example                # Backend environment template
│
├── frontend/                       # React + Vite application (JavaScript)
│   ├── src/                        # React source components & pages
│   ├── package.json                # Frontend dependencies & scripts
│   ├── vite.config.js              # Vite configuration
│   └── .env.example                # Frontend environment template
│
├── database/
│   └── schema.sql                  # PostgreSQL schema definitions & RLS policies
│
├── tests/                          # Automated unit and integration tests
│
├── docs/                           # Architecture, database design & API documentation
│   ├── architecture.md
│   ├── database_design.md
│   └── api_documentation.md
│
├── .gitignore                      # Git ignore rules for node_modules, .venv, .env
├── .env.example                    # Global environment variables template
└── README.md                       # Project overview and setup instructions
```

---

## Getting Started

### 1. Backend Setup

1. Open PowerShell and navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. (If not already installed) Install backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. Verify the backend:
   - Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
   - Interactive Docs (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 2. Frontend Setup

1. Open a new PowerShell window and navigate to the frontend directory:
   ```powershell
   cd frontend
   ```

2. (If not already installed) Install npm dependencies:
   ```powershell
   npm install
   ```

3. Start the Vite development server:
   ```powershell
   npm run dev
   ```

4. Open your browser and navigate to the local URL displayed (typically `http://localhost:5173`).

---

### Core Architecture Rules

1. **Eligibility Determination:** The AI match score **never** decides eligibility. Eligibility is calculated purely through deterministic, mandatory logical rules resulting in:
   - **Eligible**
   - **Possibly Eligible**
   - **Not Eligible**
2. **AI Role:** OpenAI models are used solely for user intent parsing, relevance ranking, query summarization, and interactive assistance.
3. **Data Privacy:** Never commit `.env` files and never expose backend secret keys or OpenAI keys in frontend client code.
