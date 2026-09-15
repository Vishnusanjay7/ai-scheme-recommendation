"""
Deterministic Scheme Eligibility Evaluation API Endpoints
----------------------------------------------------------
Provides server-side evaluation endpoints for single schemes and bulk discovery:
  - POST /api/eligibility/evaluate
  - GET  /api/eligibility/schemes
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.eligibility import (
    BulkEligibilityResponse,
    EligibilityEvaluationRequest,
    EligibilityEvaluationResponse,
    UserProfileInput,
)
from app.services.eligibility_service import EligibilityService
from app.utils.auth import get_authenticated_user_id

router = APIRouter(prefix="/api/eligibility", tags=["Eligibility"])
eligibility_service = EligibilityService()


@router.post(
    "/evaluate",
    response_model=EligibilityEvaluationResponse,
    summary="Evaluate single scheme eligibility",
    description=(
        "Deterministically evaluate citizen eligibility for a specific scheme. "
        "Strictly enforces auth.uid() for authenticated users and blocks arbitrary profile overrides. "
        "Guest evaluations operate purely in-memory and cannot access private citizen profiles."
    ),
)
def evaluate_single_scheme(
    request: EligibilityEvaluationRequest,
    auth_user_id: Optional[str] = Depends(get_authenticated_user_id),
):
    # 1. Authenticated User Flow
    if auth_user_id:
        # Cross-user access check: client cannot supply a different user_id
        if request.user_id and request.user_id != auth_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-user access denied: client-supplied user_id does not match authenticated user identity.",
            )

        # Profile override check: authenticated users must not override database profile with arbitrary input
        if request.profile is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authenticated users cannot override their database profile with an arbitrary profile dictionary.",
            )

        target_user_id = auth_user_id
        target_profile = None

    # 2. Guest / Anonymous User Flow
    else:
        # Private profile access check: guest cannot pass user_id to look up database profiles
        if request.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Guest/anonymous requests cannot access private user profiles. Please authenticate or evaluate using guest profile attributes.",
            )

        target_user_id = None
        target_profile = request.profile

    try:
        result = eligibility_service.evaluate_scheme(
            scheme_id=request.scheme_id,
            user_id=target_user_id,
            profile_input=target_profile,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID '{request.scheme_id}' was not found.",
            )
        return result
    except HTTPException:
        raise
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(val_err).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Eligibility evaluation failed: {str(exc)}",
        )


@router.get(
    "/schemes",
    response_model=BulkEligibilityResponse,
    summary="Bulk evaluate scheme eligibility",
    description=(
        "Bulk evaluate public schemes against a citizen profile. "
        "Does NOT rank or perform AI scoring; returns deterministic status for every scheme."
    ),
)
def evaluate_bulk_schemes(
    user_id: Optional[str] = Query(default=None, description="Authenticated citizen user UUID"),
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
        profile_params = None

    # 2. Guest / Anonymous User Flow
    else:
        if user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Guest/anonymous requests cannot access private user profiles. Please authenticate or evaluate using guest profile attributes.",
            )
        target_user_id = None
        profile_params = UserProfileInput(
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
        return eligibility_service.evaluate_all_schemes(
            user_id=target_user_id,
            profile_input=profile_params,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(val_err).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk eligibility evaluation failed: {str(exc)}",
        )
