"""
Authentication & Provisioning Routes
------------------------------------
Handles citizen registration and provisioning via the Supabase Admin client,
bypassing external email rate limits on public sign-up endpoints.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

import logging
from app.integrations.supabase_client import (
    get_supabase_admin_client,
    is_supabase_admin_configured,
)

logger = logging.getLogger("auth_routes")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class CitizenRegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, description="Citizen email address")
    password: str = Field(..., min_length=6, description="Citizen password")
    full_name: Optional[str] = Field(None, description="Citizen full name")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_citizen(payload: CitizenRegisterRequest):
    """
    Registers a new citizen by provisioning an account directly via the
    Supabase Admin client with pre-confirmed email.
    Completely eliminates 'over_email_send_rate_limit' errors.
    """
    email = payload.email.strip().lower()
    full_name = payload.full_name.strip() if payload.full_name else ""

    if not is_supabase_admin_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin provisioning service not configured.",
        )

    admin_client = get_supabase_admin_client()

    try:
        user_attributes = {
            "email": email,
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name},
        }

        user_resp = admin_client.auth.admin.create_user(user_attributes)
        user = user_resp.user if hasattr(user_resp, "user") else user_resp

        logger.info(f"Successfully provisioned citizen account: {email}")
        return {
            "status": "success",
            "message": "Account created successfully. You can now sign in.",
            "user": {
                "id": str(getattr(user, "id", "")),
                "email": getattr(user, "email", email),
            },
        }
    except Exception as exc:
        err_msg = str(exc)
        logger.warning(f"Registration error for {email}: {err_msg}")
        if "already registered" in err_msg.lower() or "unique constraint" in err_msg.lower():
            # If user already exists, update email_confirm to True and set new password
            try:
                users = admin_client.auth.admin.list_users()
                for u in users:
                    if u.email and u.email.lower() == email:
                        admin_client.auth.admin.update_user_by_id(
                            u.id,
                            {
                                "email_confirm": True,
                                "password": payload.password,
                                "user_metadata": {"full_name": full_name or getattr(u, "user_metadata", {}).get("full_name", "")},
                            },
                        )
                        logger.info(f"Re-confirmed and updated existing account for {email}")
                        return {
                            "status": "success",
                            "message": "Account updated and confirmed successfully. You can now sign in.",
                            "user": {"id": str(u.id), "email": u.email},
                        }
            except Exception as update_exc:
                logger.error(f"Failed to auto-confirm existing account: {update_exc}")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists. Please login instead.",
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {err_msg}",
        )
