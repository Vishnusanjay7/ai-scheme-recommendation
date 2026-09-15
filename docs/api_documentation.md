# API Documentation

> **Phase:** 1 (Supabase Database + RLS)  
> **Interactive Documentation:** When the backend is running, complete OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs`.

---

## Health & System Endpoints

### 1. General Health Check
- **Route:** `GET /health`
- **Description:** Verifies that the FastAPI application is alive and indicates whether database credentials are configured in the environment.
- **Response Format (`200 OK`):**
  ```json
  {
    "status": "ok",
    "message": "AI Government Scheme Recommendation API is running",
    "database_configured": false
  }
  ```

### 2. Database Connectivity Check
- **Route:** `GET /health/db`
- **Description:** Queries Supabase PostgreSQL to verify active network connectivity, credentials validity, and table accessibility.
- **Response Format (`200 OK` - Configured & Connected):**
  ```json
  {
    "status": "connected",
    "configured": true,
    "sample_data": [
      {"id": 1, "code": "AP", "name": "Andhra Pradesh"}
    ],
    "message": "Successfully connected to Supabase."
  }
  ```
- **Response Format (`200 OK` - Unconfigured):**
  ```json
  {
    "status": "unconfigured",
    "configured": false,
    "message": "SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY are not set in environment."
  }
  ```
