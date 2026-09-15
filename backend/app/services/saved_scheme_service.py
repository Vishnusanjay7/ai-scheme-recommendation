"""
Saved Schemes Service
---------------------
Implements citizen bookmarking operations for welfare schemes:
  - Save a scheme (idempotent, prevents duplicates)
  - Verify scheme existence before bookmarking (404 on nonexistent schemes)
  - List bookmarked schemes with real-time deadline & activity status
  - Remove saved scheme (removes junction record, never deletes parent scheme)
  - User isolation strictly enforced via auth.uid()
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from app.integrations.supabase_client import get_supabase_client
from app.models.saved_scheme import (
    SavedSchemeResponse,
    SavedSchemeStatusResponse,
    SaveSchemeActionResponse,
)
from app.services.deadline_service import get_scheme_activity


class SavedSchemeService:
    """Service handling bookmarking of welfare schemes by authenticated citizens."""

    def __init__(self, client=None):
        self._client = client

    def get_client(self):
        return self._client if self._client is not None else get_supabase_client()

    def _validate_uuid(self, val: str, field_name: str = "ID") -> str:
        try:
            return str(uuid.UUID(str(val)))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} format: '{val}'. Expected valid UUID.",
            )

    def save_scheme(self, user_id: str, scheme_id: str) -> SaveSchemeActionResponse:
        """
        Save a scheme for the authenticated citizen.
        - Validates scheme existence (raises 404 if not found).
        - Idempotently handles duplicate saves.
        """
        u_id = self._validate_uuid(user_id, "user_id")
        s_id = self._validate_uuid(scheme_id, "scheme_id")
        client = self.get_client()

        # 1. Verify scheme exists in schemes table
        scheme_check = client.table("schemes").select("id, name").eq("id", s_id).execute()
        if not scheme_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Government scheme with ID '{s_id}' does not exist.",
            )

        # 2. Check if already saved by this citizen
        existing = (
            client.table("saved_schemes")
            .select("id, saved_at")
            .eq("user_id", u_id)
            .eq("scheme_id", s_id)
            .execute()
        )
        if existing.data:
            return SaveSchemeActionResponse(
                status="already_saved",
                message="Scheme already saved in your bookmarks.",
                saved=True,
                scheme_id=s_id,
            )

        # 3. Ensure citizen record exists in public.users
        user_check = client.table("users").select("id").eq("id", u_id).execute()
        if not user_check.data:
            try:
                client.table("users").insert({
                    "id": u_id,
                    "email": f"{u_id}@citizen.local",
                    "full_name": "Citizen",
                }).execute()
            except Exception:
                pass

        # 4. Insert into saved_schemes
        try:
            client.table("saved_schemes").insert({
                "user_id": u_id,
                "scheme_id": s_id,
            }).execute()
        except Exception as exc:
            # Handle potential race condition / unique constraint duplicate
            err_str = str(exc).lower()
            if "duplicate" in err_str or "unique" in err_str:
                return SaveSchemeActionResponse(
                    status="already_saved",
                    message="Scheme already saved in your bookmarks.",
                    saved=True,
                    scheme_id=s_id,
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save scheme: {str(exc)}",
            )

        return SaveSchemeActionResponse(
            status="saved",
            message="Scheme saved successfully to your bookmarks.",
            saved=True,
            scheme_id=s_id,
        )

    def get_saved_schemes(self, user_id: str) -> List[SavedSchemeResponse]:
        """
        List all saved schemes for the authenticated citizen with real-time deadline & activity status.
        """
        u_id = self._validate_uuid(user_id, "user_id")
        client = self.get_client()

        # Query saved_schemes for this user
        saved_res = (
            client.table("saved_schemes")
            .select("id, user_id, scheme_id, saved_at")
            .eq("user_id", u_id)
            .order("saved_at", desc=True)
            .execute()
        )
        saved_rows = saved_res.data or []
        if not saved_rows:
            return []

        results: List[SavedSchemeResponse] = []
        for row in saved_rows:
            s_id = row["scheme_id"]
            scheme_res = client.table("schemes").select("*").eq("id", s_id).execute()
            if not scheme_res.data:
                continue

            scheme = scheme_res.data[0]

            # Compute authoritative real-time activity and deadline status
            activity = get_scheme_activity(scheme)

            results.append(
                SavedSchemeResponse(
                    id=str(row["id"]),
                    user_id=str(row["user_id"]),
                    scheme_id=str(s_id),
                    saved_at=str(row["saved_at"]),
                    scheme_name=scheme.get("name") or "Government Scheme",
                    benefits=scheme.get("benefits"),
                    government_level=scheme.get("government_level"),
                    state_id=scheme.get("state_id"),
                    official_url=scheme.get("official_url"),
                    source_url=scheme.get("source_url"),
                    start_date=str(scheme["start_date"]) if scheme.get("start_date") else None,
                    last_date=str(scheme["last_date"]) if scheme.get("last_date") else None,
                    activity_status=activity.status.value,
                    deadline_status=activity.deadline_status.value if activity.deadline_status else None,
                    days_remaining=activity.days_remaining,
                    is_actionable=activity.is_actionable,
                )
            )

        return results

    def is_scheme_saved(self, user_id: str, scheme_id: str) -> SavedSchemeStatusResponse:
        """Check if a specific scheme is saved by the citizen."""
        u_id = self._validate_uuid(user_id, "user_id")
        s_id = self._validate_uuid(scheme_id, "scheme_id")
        client = self.get_client()

        res = (
            client.table("saved_schemes")
            .select("id, saved_at")
            .eq("user_id", u_id)
            .eq("scheme_id", s_id)
            .execute()
        )
        if res.data:
            return SavedSchemeStatusResponse(
                saved=True,
                saved_at=str(res.data[0]["saved_at"]),
                scheme_id=s_id,
            )
        return SavedSchemeStatusResponse(
            saved=False,
            saved_at=None,
            scheme_id=s_id,
        )

    def remove_saved_scheme(self, user_id: str, scheme_id: str) -> SaveSchemeActionResponse:
        """
        Remove a bookmarked scheme for the authenticated citizen.
        CRITICAL: Deletes ONLY the record in saved_schemes, leaving the schemes table untouched.
        """
        u_id = self._validate_uuid(user_id, "user_id")
        s_id = self._validate_uuid(scheme_id, "scheme_id")
        client = self.get_client()

        # Delete bookmark record strictly scoped to auth.uid()
        res = (
            client.table("saved_schemes")
            .delete()
            .eq("user_id", u_id)
            .eq("scheme_id", s_id)
            .execute()
        )

        return SaveSchemeActionResponse(
            status="removed",
            message="Scheme successfully removed from your bookmarks.",
            saved=False,
            scheme_id=s_id,
        )
