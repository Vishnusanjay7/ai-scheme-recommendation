"""
Eligibility Service
-------------------
Coordinates database retrieval of citizen profiles, scheme rules,
and executes the deterministic eligibility engine.
"""

from typing import Any, Dict, List, Optional
import uuid

from app.integrations.supabase_client import get_supabase_client
from app.models.eligibility import (
    BulkEligibilityResponse,
    EligibilityEvaluationResponse,
    EligibilityExplanation,
    UserProfileInput,
)
from app.services.eligibility_engine import evaluate_eligibility
from app.utils.logger import pipeline_logger


class EligibilityService:
    """
    Database-backed service for evaluating single and bulk scheme eligibility.
    """

    def __init__(self, client=None):
        self._client = client

    @property
    def client(self):
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_user_profile_from_db(self, user_id: str) -> Optional[UserProfileInput]:
        """Fetch citizen profile from Supabase user_profiles table."""
        try:
            uuid.UUID(str(user_id))
        except ValueError:
            return None

        res = (
            self.client.table("user_profiles")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if not res.data:
            return None

        row = res.data[0]
        return UserProfileInput(
            user_id=row.get("user_id"),
            age=row.get("age"),
            gender=row.get("gender"),
            state_id=row.get("state_id"),
            district_id=row.get("district_id"),
            annual_income=float(row["annual_income"]) if row.get("annual_income") is not None else None,
            occupation=row.get("occupation"),
            education=row.get("education"),
            category=row.get("category"),
            disability_status=row.get("disability_status"),
        )

    def evaluate_scheme(
        self,
        scheme_id: str,
        user_id: Optional[str] = None,
        profile_input: Optional[UserProfileInput] = None,
    ) -> Optional[EligibilityEvaluationResponse]:
        """
        Evaluate a single scheme for a citizen profile.
        Profile can originate from the database (user_id) or explicit profile_input.
        """
        try:
            uuid.UUID(str(scheme_id))
        except ValueError:
            return None

        # 1. Fetch scheme record
        scheme_res = (
            self.client.table("schemes")
            .select("id, scheme_name, government_level, state_id, status")
            .eq("id", scheme_id)
            .execute()
        )
        if not scheme_res.data:
            return None
        scheme_record = scheme_res.data[0]

        # 2. Fetch scheme eligibility rules
        elig_res = (
            self.client.table("scheme_eligibility")
            .select("*")
            .eq("scheme_id", scheme_id)
            .execute()
        )
        elig_rules = elig_res.data[0] if elig_res.data else {}

        # 3. Resolve citizen profile securely
        resolved_profile = None
        if user_id:
            if profile_input is not None:
                raise ValueError(
                    "Authenticated users cannot override their database profile with an arbitrary profile dictionary."
                )
            resolved_profile = self.get_user_profile_from_db(user_id)
            if not resolved_profile:
                # User has authenticated credentials but no stored user_profiles record
                raise ValueError(f"Citizen profile for user ID '{user_id}' was not found in the database.")
        else:
            # Guest / unauthenticated evaluation: strictly in-memory, never accessing private DB user_profiles
            resolved_profile = profile_input or UserProfileInput()

        # 4. Execute deterministic engine
        explanation: EligibilityExplanation = evaluate_eligibility(
            profile=resolved_profile,
            scheme=scheme_record,
            eligibility_rules=elig_rules,
        )

        return EligibilityEvaluationResponse(
            scheme_id=scheme_id,
            scheme_name=scheme_record.get("scheme_name"),
            government_level=scheme_record.get("government_level"),
            evaluation=explanation,
        )

    def evaluate_all_schemes(
        self,
        user_id: Optional[str] = None,
        profile_input: Optional[UserProfileInput] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> BulkEligibilityResponse:
        """
        Bulk evaluate all public schemes for a citizen profile.
        Does NOT perform AI ranking; returns deterministic eligibility states.
        """
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        # 1. Resolve profile securely
        resolved_profile = None
        if user_id:
            if profile_input is not None and any(
                v is not None
                for k, v in profile_input.model_dump().items()
                if k != "user_id"
            ):
                raise ValueError(
                    "Authenticated users cannot override their database profile with arbitrary profile parameters."
                )
            resolved_profile = self.get_user_profile_from_db(user_id)
            if not resolved_profile:
                raise ValueError(f"Citizen profile for user ID '{user_id}' was not found in the database.")
        else:
            # Guest evaluation: strictly in-memory
            resolved_profile = profile_input or UserProfileInput()

        # 2. Query schemes
        schemes_res = (
            self.client.table("schemes")
            .select("id, scheme_name, government_level, state_id, status")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        schemes = schemes_res.data or []

        # 3. Query all eligibility rules for these schemes
        scheme_ids = [s["id"] for s in schemes]
        elig_map: Dict[str, Dict[str, Any]] = {}
        if scheme_ids:
            elig_res = (
                self.client.table("scheme_eligibility")
                .select("*")
                .in_("scheme_id", scheme_ids)
                .execute()
            )
            for row in elig_res.data or []:
                elig_map[row["scheme_id"]] = row

        # 4. Evaluate each scheme
        results: List[EligibilityEvaluationResponse] = []
        eligible_count = 0
        possibly_count = 0
        not_eligible_count = 0

        for s in schemes:
            s_id = s["id"]
            rules = elig_map.get(s_id, {})
            explanation = evaluate_eligibility(resolved_profile, s, rules)

            if explanation.status.value == "ELIGIBLE":
                eligible_count += 1
            elif explanation.status.value == "POSSIBLY_ELIGIBLE":
                possibly_count += 1
            else:
                not_eligible_count += 1

            results.append(
                EligibilityEvaluationResponse(
                    scheme_id=s_id,
                    scheme_name=s.get("scheme_name"),
                    government_level=s.get("government_level"),
                    evaluation=explanation,
                )
            )

        return BulkEligibilityResponse(
            total_evaluated=len(results),
            eligible_count=eligible_count,
            possibly_eligible_count=possibly_count,
            not_eligible_count=not_eligible_count,
            results=results,
        )
