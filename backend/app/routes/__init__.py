"""Routes package initialization."""

from app.routes.schemes import router as schemes_router
from app.routes.eligibility_routes import router as eligibility_router

__all__ = ["schemes_router", "eligibility_router"]
