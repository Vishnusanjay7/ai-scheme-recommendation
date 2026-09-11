# API Documentation

> **Status:** Placeholder (Phase 0)  
> Detailed endpoint definitions, request/response schemas, and error codes will be documented as routes are implemented.

## Baseline Endpoint (Phase 0)

### Health Check
- **Endpoint:** `GET /health`
- **Description:** Verifies that the FastAPI application is alive and responding.
- **Response Format:**
  ```json
  {
    "status": "ok",
    "message": "AI Government Scheme Recommendation API is running"
  }
  ```

Interactive OpenAPI documentation is automatically available when running the backend at `http://127.0.0.1:8000/docs`.
