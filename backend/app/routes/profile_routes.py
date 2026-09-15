"""
Profile & Reference Data API Endpoints
--------------------------------------
Provides reference data for states, districts, and authenticated citizen profile management.

ENDPOINTS:
  - GET /api/states                    (Public reference list of Indian States/UTs)
  - GET /api/districts                 (Districts list, filtered by state_id)
  - GET /api/profile                   (Fetch authenticated citizen profile)
  - PUT /api/profile                   (Create or update authenticated citizen profile)

SECURITY INVARIANTS:
1. Citizen identity is resolved solely via auth.uid().
2. Cross-user profile access or modification is strictly forbidden.
3. Unauthenticated requests to /api/profile return 401 Unauthorized.
"""

from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.integrations.supabase_client import get_supabase_client
from app.models.eligibility import UserProfileInput
from app.utils.auth import get_authenticated_user_id

router = APIRouter(prefix="/api", tags=["Profile & Reference Data"])


class StateItem(BaseModel):
    id: int
    name: str
    code: str


class DistrictItem(BaseModel):
    id: int
    state_id: int
    name: str
    code: Optional[str] = None


class ProfileUpdatePayload(BaseModel):
    age: Optional[int] = Field(default=None, ge=0, le=150)
    gender: Optional[str] = Field(default=None, pattern="^(MALE|FEMALE|TRANSGENDER|OTHER)$")
    state_id: Optional[int] = None
    district_id: Optional[int] = None
    annual_income: Optional[float] = Field(default=None, ge=0)
    occupation: Optional[str] = None
    education: Optional[str] = None
    category: Optional[str] = None
    disability_status: Optional[bool] = False
    full_name: Optional[str] = None


class ProfileResponse(BaseModel):
    user_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    state_id: Optional[int] = None
    state_name: Optional[str] = None
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    annual_income: Optional[float] = None
    occupation: Optional[str] = None
    education: Optional[str] = None
    category: Optional[str] = None
    disability_status: bool = False
    profile_complete: bool = False


@router.get(
    "/states",
    response_model=List[StateItem],
    summary="Get all States and Union Territories",
)
def get_all_states():
    """Fetch official list of all 36 Indian States and Union Territories."""
    client = get_supabase_client()
    res = client.table("states").select("id, name, code").order("name").execute()
    return res.data or []


@router.get(
    "/districts",
    response_model=List[DistrictItem],
    summary="Get districts filtered by state",
)
def get_districts(
    state_id: Optional[int] = Query(default=None, description="Optional State ID to filter districts"),
):
    """Fetch districts, optionally filtered by state_id."""
    client = get_supabase_client()
    query = client.table("districts").select("id, state_id, name, code").order("name")
    if state_id is not None:
        query = query.eq("state_id", state_id)
    res = query.execute()
    return res.data or []


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get citizen profile",
    description="Retrieve demographic profile for authenticated user using auth.uid().",
)
def get_current_user_profile(
    auth_user_id: Optional[str] = Depends(get_authenticated_user_id),
):
    if not auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view profile.",
        )

    client = get_supabase_client()

    # 1. Fetch user record if exists
    user_res = client.table("users").select("email, full_name").eq("id", auth_user_id).limit(1).execute()
    user_row = user_res.data[0] if user_res.data else {}

    # 2. Fetch user profile record
    prof_res = client.table("user_profiles").select("*").eq("user_id", auth_user_id).limit(1).execute()
    prof_row = prof_res.data[0] if prof_res.data else {}

    # 3. Lookup state and district names if IDs exist
    state_name = None
    district_name = None
    if prof_row.get("state_id"):
        st_res = client.table("states").select("name").eq("id", prof_row["state_id"]).limit(1).execute()
        if st_res.data:
            state_name = st_res.data[0]["name"]

    if prof_row.get("district_id"):
        dt_res = client.table("districts").select("name").eq("id", prof_row["district_id"]).limit(1).execute()
        if dt_res.data:
            district_name = dt_res.data[0]["name"]

    # Calculate completion status
    core_fields = [
        prof_row.get("age"),
        prof_row.get("gender"),
        prof_row.get("state_id"),
        prof_row.get("occupation"),
        prof_row.get("education"),
        prof_row.get("category"),
    ]
    is_complete = all(f is not None for f in core_fields)

    return ProfileResponse(
        user_id=auth_user_id,
        email=user_row.get("email"),
        full_name=user_row.get("full_name"),
        age=prof_row.get("age"),
        gender=prof_row.get("gender"),
        state_id=prof_row.get("state_id"),
        state_name=state_name,
        district_id=prof_row.get("district_id"),
        district_name=district_name,
        annual_income=float(prof_row["annual_income"]) if prof_row.get("annual_income") is not None else None,
        occupation=prof_row.get("occupation"),
        education=prof_row.get("education"),
        category=prof_row.get("category"),
        disability_status=bool(prof_row.get("disability_status", False)),
        profile_complete=is_complete,
    )


@router.put(
    "/profile",
    response_model=ProfileResponse,
    summary="Update citizen profile",
    description="Save or update demographic attributes for the authenticated citizen.",
)
def update_current_user_profile(
    payload: ProfileUpdatePayload,
    auth_user_id: Optional[str] = Depends(get_authenticated_user_id),
):
    if not auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to update profile.",
        )

    client = get_supabase_client()

    # 1. Ensure user record in public.users exists
    user_check = client.table("users").select("id").eq("id", auth_user_id).execute()
    if not user_check.data:
        client.table("users").insert({
            "id": auth_user_id,
            "email": f"{auth_user_id}@citizen.local",
            "full_name": payload.full_name or "Citizen",
        }).execute()
    elif payload.full_name:
        client.table("users").update({"full_name": payload.full_name}).eq("id", auth_user_id).execute()

    # 2. Validate district belongs to state if both provided
    if payload.state_id is not None and payload.district_id is not None:
        dist_check = client.table("districts").select("id").eq("id", payload.district_id).eq("state_id", payload.state_id).execute()
        if not dist_check.data:
            # Clear invalid district selection
            payload.district_id = None

    profile_data = {
        "user_id": auth_user_id,
        "age": payload.age,
        "gender": payload.gender,
        "state_id": payload.state_id,
        "district_id": payload.district_id,
        "annual_income": payload.annual_income,
        "occupation": payload.occupation,
        "education": payload.education,
        "category": payload.category,
        "disability_status": payload.disability_status if payload.disability_status is not None else False,
    }

    # 3. Upsert profile in user_profiles
    existing = client.table("user_profiles").select("id").eq("user_id", auth_user_id).execute()
    if existing.data:
        client.table("user_profiles").update(profile_data).eq("user_id", auth_user_id).execute()
    else:
        client.table("user_profiles").insert(profile_data).execute()

    # Return refreshed profile view
    return get_current_user_profile(auth_user_id=auth_user_id)
