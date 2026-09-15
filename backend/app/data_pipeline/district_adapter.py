"""
District Data Adapter & Interface
---------------------------------
Provides lookup and resolution for district-level scheme restrictions
against the Supabase `districts` table.

DATA GOVERNANCE & INTEGRITY:
In compliance with the project principles:
- Synthetic or invented district data is strictly prohibited.
- The initial schema contains official representative districts across sample States.
- The complete national registry of 780+ districts across all 36 States/UTs
  is designed to be imported via the Ministry of Panchayati Raj's official
  Local Government Directory (LGD) platform (https://lgdirectory.gov.in/).
- This adapter provides the clean interface for district validation and restriction checks.
"""

from typing import Any, Dict, List, Optional, Tuple
from app.integrations.supabase_client import get_supabase_client
from app.utils.logger import pipeline_logger


class DistrictAdapter:
    """
    Manages district reference data lookups and validation for scheme eligibility restrictions.
    """

    def __init__(self, districts_cache: Optional[List[Dict[str, Any]]] = None):
        self._cache = districts_cache or []
        self._by_state_and_name: Dict[Tuple[int, str], int] = {}
        if self._cache:
            self._rebuild_index()

    def load_from_supabase(self):
        """Fetch all currently loaded districts from Supabase."""
        try:
            client = get_supabase_client()
            res = client.table("districts").select("id, state_id, name, code").execute()
            self._cache = res.data or []
            self._rebuild_index()
            pipeline_logger._log_event(
                20,
                "districts_loaded",
                f"Loaded {len(self._cache)} official district records from database.",
                {"count": len(self._cache)},
            )
        except Exception as exc:
            pipeline_logger._log_event(
                30,
                "districts_load_failed",
                f"Failed to load districts from Supabase: {exc}",
                {"error": str(exc)},
            )

    def _rebuild_index(self):
        self._by_state_and_name.clear()
        for d in self._cache:
            state_id = d.get("state_id")
            name = (d.get("name") or "").strip().lower()
            if state_id and name:
                self._by_state_and_name[(state_id, name)] = d["id"]

    def resolve_district_id(self, state_id: int, district_name: str) -> Optional[int]:
        """
        Resolve district name to ID for a given state.
        Returns None if district is not registered.
        """
        if not district_name or not state_id:
            return None
        cleaned = district_name.strip().lower()
        return self._by_state_and_name.get((state_id, cleaned))

    def validate_district_restriction(
        self, state_id: Optional[int], district_id: Optional[int]
    ) -> bool:
        """
        Verify that a district belongs to the specified state restriction.
        """
        if district_id is None:
            return True
        if state_id is None:
            return False

        for d in self._cache:
            if d["id"] == district_id:
                return d["state_id"] == state_id
        return False
