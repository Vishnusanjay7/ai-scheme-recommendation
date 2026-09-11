from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Government Scheme Recommendation API",
    version="1.0.0",
    description="Backend API for AI-Powered Government Scheme Recommendation System",
)

# Enable CORS for frontend communication during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint to verify backend operational status."""
    return {
        "status": "ok",
        "message": "AI Government Scheme Recommendation API is running",
    }
