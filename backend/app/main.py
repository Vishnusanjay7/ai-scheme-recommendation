from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.integrations.supabase_client import (
    is_supabase_configured,
    check_supabase_connection,
)
from app.routes.schemes import router as schemes_router
from app.routes.eligibility_routes import router as eligibility_router
from app.routes.recommendation_routes import router as recommendation_router
from app.routes.profile_routes import router as profile_router
from app.routes.saved_scheme_routes import router as saved_schemes_router
from app.routes.notification_routes import router as notification_router
from app.routes.chat_routes import router as chat_router
from app.routes.auth_routes import router as auth_router

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

# Register API Routers
app.include_router(schemes_router)
app.include_router(eligibility_router)
app.include_router(recommendation_router)
app.include_router(profile_router)
app.include_router(saved_schemes_router)
app.include_router(notification_router)
app.include_router(chat_router)
app.include_router(auth_router)


@app.get("/health")
def health_check():
    """Health check endpoint to verify backend operational status."""
    return {
        "status": "ok",
        "message": "AI Government Scheme Recommendation API is running",
        "database_configured": is_supabase_configured(),
    }


@app.get("/health/db")
def health_check_database():
    """Detailed database connectivity check with Supabase."""
    return check_supabase_connection()
