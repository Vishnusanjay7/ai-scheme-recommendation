"""
Saved Schemes API Endpoints
---------------------------
Provides citizen bookmarking and saved schemes operations:
  - POST   /api/saved-schemes/{scheme_id}  (Save a scheme for authenticated citizen)
  - GET    /api/saved-schemes              (List authenticated citizen's saved schemes)
  - GET    /api/saved-schemes/{scheme_id}  (Check if a specific scheme is saved)
  - DELETE /api/saved-schemes/{scheme_id}  (Remove a scheme from saved bookmarks)

SECURITY & AUTHORIZATION INVARIANTS:
1. All operations strictly require valid authentication and derive identity from auth.uid().
2. Unauthenticated requests are rejected with 401 Unauthorized.
3. Client cannot specify or override user_id to access or alter another citizen's saved schemes.
4. Nonexistent schemes return 404.
5. Deleting a saved scheme removes ONLY the junction bookmark row; never the parent scheme.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.saved_scheme import (
    SavedSchemeResponse,
    SavedSchemeStatusResponse,
    SaveSchemeActionResponse,
)
from app.services.saved_scheme_service import SavedSchemeService
from app.utils.auth import get_authenticated_user_id

router = APIRouter(prefix="/api/saved-schemes", tags=["Saved Schemes"])
saved_scheme_service = SavedSchemeService()


def _require_auth_user(auth_user_id: Optional[str] = Depends(get_authenticated_user_id)) -> str:
    """Ensure the request is authenticated with a valid citizen UUID."""
    if not auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to manage saved schemes.",
        )
    return auth_user_id


@router.post(
    "/{scheme_id}",
    response_model=SaveSchemeActionResponse,
    summary="Save a scheme for the authenticated citizen",
    description="Bookmarks a welfare scheme. Idempotent: saving an already saved scheme returns a clean success response without duplicate rows.",
)
def save_scheme(
    scheme_id: str,
    user_id: str = Depends(_require_auth_user),
):
    return saved_scheme_service.save_scheme(user_id=user_id, scheme_id=scheme_id)


@router.get(
    "",
    response_model=List[SavedSchemeResponse],
    summary="List authenticated citizen's saved schemes",
    description="Returns all bookmarked welfare schemes for the calling citizen with live deadline & activity statuses.",
)
def get_saved_schemes(
    user_id: str = Depends(_require_auth_user),
):
    return saved_scheme_service.get_saved_schemes(user_id=user_id)


@router.get(
    "/{scheme_id}",
    response_model=SavedSchemeStatusResponse,
    summary="Check if a scheme is saved",
    description="Returns whether the calling citizen has bookmarked the specified scheme.",
)
def check_scheme_saved(
    scheme_id: str,
    user_id: str = Depends(_require_auth_user),
):
    return saved_scheme_service.is_scheme_saved(user_id=user_id, scheme_id=scheme_id)


@router.delete(
    "/{scheme_id}",
    response_model=SaveSchemeActionResponse,
    summary="Remove a scheme from saved bookmarks",
    description="Removes the bookmark record for this citizen. The underlying government scheme is untouched.",
)
def remove_saved_scheme(
    scheme_id: str,
    user_id: str = Depends(_require_auth_user),
):
    return saved_scheme_service.remove_saved_scheme(user_id=user_id, scheme_id=scheme_id)
