"""
Scheme Retrieval & Search API Endpoints
---------------------------------------
Provides read-only public endpoints for querying and discovering government welfare schemes:
  - GET /api/schemes
  - GET /api/schemes/search?q=
  - GET /api/schemes/central
  - GET /api/schemes/active
  - GET /api/schemes/state/{state_id}
  - GET /api/schemes/{scheme_id}
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.models.scheme import SchemeDetailResponse, SchemeListResponse
from app.services.scheme_service import SchemeService

router = APIRouter(prefix="/api/schemes", tags=["Schemes"])
scheme_service = SchemeService()


@router.get(
    "",
    response_model=SchemeListResponse,
    summary="List all government schemes",
    description="Retrieve paginated list of public welfare schemes with optional filters.",
)
def list_schemes(
    limit: int = Query(default=50, ge=1, le=100, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    government_level: Optional[str] = Query(default=None, description="'CENTRAL' or 'STATE'"),
    state_id: Optional[int] = Query(default=None, description="State foreign key ID"),
    category_id: Optional[int] = Query(default=None, description="Category foreign key ID"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="'ACTIVE', 'INACTIVE', or 'EXPIRED'"),
):
    try:
        return scheme_service.get_schemes(
            limit=limit,
            offset=offset,
            government_level=government_level,
            state_id=state_id,
            category_id=category_id,
            status=status_filter,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving schemes: {str(exc)}",
        )


@router.get(
    "/search",
    response_model=SchemeListResponse,
    summary="Search government schemes",
    description="Search schemes by keyword matching title or description.",
)
def search_schemes(
    q: str = Query(..., min_length=1, description="Search query keywords"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return scheme_service.search_schemes(query_text=q, limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching schemes: {str(exc)}",
        )


@router.get(
    "/central",
    response_model=SchemeListResponse,
    summary="List Central Government schemes",
    description="Retrieve all Pan-India Central Government welfare schemes.",
)
def list_central_schemes(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return scheme_service.get_central_schemes(limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving central schemes: {str(exc)}",
        )


@router.get(
    "/active",
    response_model=SchemeListResponse,
    summary="List active schemes",
    description=(
        "Retrieve all currently active welfare schemes whose effective registration status "
        "is OPEN and application deadline has not expired. Excludes schemes with future start dates, "
        "past deadlines, or inactive administrative status."
    ),
)
def list_active_schemes(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return scheme_service.get_active_schemes(limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving active schemes: {str(exc)}",
        )


@router.get(
    "/state/{state_id}",
    response_model=SchemeListResponse,
    summary="List State-specific schemes",
    description="Retrieve schemes restricted to a specific State or UT by ID, code (e.g. 'TN'), or name.",
)
def list_state_schemes(
    state_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return scheme_service.get_schemes_by_state(
            state_identifier=state_id, limit=limit, offset=offset
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving state schemes: {str(exc)}",
        )


@router.get(
    "/{scheme_id}",
    response_model=SchemeDetailResponse,
    summary="Get scheme details",
    description=(
        "Retrieve full details for a scheme, including registration activity, deadline classification, "
        "eligibility rules, required documents, and source citations."
    ),
)
def get_scheme_detail(scheme_id: str):
    try:
        scheme = scheme_service.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID '{scheme_id}' not found.",
            )
        return scheme
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving scheme details: {str(exc)}",
        )
