"""
AI Scheme Recommendation API Endpoints
---------------------------------------
Provides personalized, multi-factor ranked recommendations for public welfare schemes:
  - POST /api/recommendations
  - GET  /api/recommendations

SECURITY & ARCHITECTURAL INVARIANTS:
1. Authenticated citizen identity is resolved strictly via auth.uid().
2. Authenticated users cannot override their stored profile with arbitrary client inputs.
3. Cross-user access is blocked (user A cannot request user B's recommendations).
4. Guest/anonymous requests cannot access private user profiles in the database.
5. All recommendations returned are guaranteed to be deterministically ELIGIBLE and OPEN.
6. The match score (0–100) indicates relevance only, never legal eligibility percentage.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.eligibility import UserProfileInput
from app.models.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_engine import RecommendationService
from app.utils.auth import get_authenticated_user_id

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])
recommendation_service = RecommendationService()


@router.post(
    "",
    response_model=RecommendationResponse,
    summary="Get personalized scheme recommendations (POST)",
    description=(
        "Returns multi-factor ranked scheme recommendations for an authenticated citizen or guest. "
        "Strictly verifies legal eligibility (Phase 3) and registration activity (Phase 4) "
        "before performing AI relevance ranking. The match score indicates fit, not eligibility."
    ),
)
def get_recommendations_post(
    request: RecommendationRequest,
    auth_user_id: Optional[str] = Depends(get_authenticated_user_id),
):
    # 1. Authenticated Citizen Flow
    if auth_user_id:
        if request.user_id and request.user_id != auth_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-user access denied: client-supplied user_id does not match authenticated user identity.",
            )
        if request.profile is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authenticated users cannot override their database profile with an arbitrary profile dictionary.",
            )
        target_user_id = auth_user_id
        target_profile = None

    # 2. Guest / Anonymous User Flow
    else:
        if request.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Guest/anonymous requests cannot access private user profiles. Please authenticate or provide guest profile attributes.",
            )
        target_user_id = None
        target_profile = request.profile

    try:
        return recommendation_service.recommend_schemes(
            profile=target_profile,
            user_id=target_user_id,
            query=request.query,
            limit=request.limit,
            offset=request.offset,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(val_err).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation processing failed: {str(exc)}",
        )


@router.get(
    "",
    response_model=RecommendationResponse,
    summary="Get personalized scheme recommendations (GET)",
    description="Convenience GET endpoint for scheme recommendations via query parameters.",
)
def get_recommendations_get(
    q: Optional[str] = Query(default=None, description="Natural-language search need (e.g. 'farming equipment')"),
    user_id: Optional[str] = Query(default=None, description="Citizen UUID"),
    age: Optional[int] = Query(default=None, ge=0, le=150),
    gender: Optional[str] = Query(default=None),
    state_id: Optional[int] = Query(default=None),
    district_id: Optional[int] = Query(default=None),
    annual_income: Optional[float] = Query(default=None, ge=0),
    occupation: Optional[str] = Query(default=None),
    education: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    disability_status: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    auth_user_id: Optional[str] = Depends(get_authenticated_user_id),
):
    # 1. Authenticated User Flow
    if auth_user_id:
        if user_id and user_id != auth_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-user access denied: client-supplied user_id does not match authenticated user identity.",
            )
        has_override = any(
            x is not None
            for x in [age, gender, state_id, district_id, annual_income, occupation, education, category, disability_status]
        )
        if has_override:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authenticated users cannot override their database profile with arbitrary query parameters.",
            )
        target_user_id = auth_user_id
        target_profile = None

    # 2. Guest User Flow
    else:
        if user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Guest/anonymous requests cannot access private user profiles. Please authenticate or provide guest profile attributes.",
            )
        target_user_id = None
        target_profile = UserProfileInput(
            age=age,
            gender=gender,
            state_id=state_id,
            district_id=district_id,
            annual_income=annual_income,
            occupation=occupation,
            education=education,
            category=category,
            disability_status=disability_status,
        )

    try:
        return recommendation_service.recommend_schemes(
            profile=target_profile,
            user_id=target_user_id,
            query=q,
            limit=limit,
            offset=offset,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(val_err).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation processing failed: {str(exc)}",
        )
