"""
Government Scheme Service Layer
--------------------------------
Encapsulates all scheme retrieval and search business logic against the
public Supabase PostgreSQL database tables:
  - schemes
  - scheme_eligibility
  - scheme_documents
  - scheme_sources
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import uuid

from app.integrations.supabase_client import get_supabase_client
from app.models.deadline import ActivityStatus
from app.models.scheme import (
    SchemeDetailResponse,
    SchemeItemResponse,
    SchemeListResponse,
)
from app.services.deadline_service import get_scheme_activity


class SchemeService:
    """
    Handles read-only scheme queries, searches, and relations retrieval.
    """

    def __init__(self, client=None):
        self._client = client

    @property
    def client(self):
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_schemes(
        self,
        limit: int = 50,
        offset: int = 0,
        government_level: Optional[str] = None,
        state_id: Optional[int] = None,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> SchemeListResponse:
        """Fetch paginated schemes with optional filtering."""
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        query = self.client.table("schemes").select("*", count="exact")

        if government_level:
            query = query.eq("government_level", government_level.upper())
        if state_id is not None:
            query = query.eq("state_id", state_id)
        if category_id is not None:
            query = query.eq("category_id", category_id)
        if status:
            query = query.eq("status", status.upper())

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        res = query.execute()

        rows = res.data or []
        total = res.count if res.count is not None else len(rows)

        items = [SchemeItemResponse(**row, activity=get_scheme_activity(row)) for row in rows]
        return SchemeListResponse(
            total=total,
            count=len(items),
            offset=offset,
            limit=limit,
            data=items,
        )

    def get_scheme_by_id(
        self, scheme_id: str, current_datetime: Optional[datetime] = None
    ) -> Optional[SchemeDetailResponse]:
        """Fetch comprehensive details for a single scheme including relations and deadline activity."""
        # Validate UUID format
        try:
            uuid.UUID(str(scheme_id))
        except ValueError:
            return None

        res = self.client.table("schemes").select("*").eq("id", scheme_id).execute()
        if not res.data:
            return None

        scheme_row = res.data[0]
        activity_info = get_scheme_activity(scheme_row, current_datetime=current_datetime)

        # Fetch nested relations
        elig_res = (
            self.client.table("scheme_eligibility")
            .select("*")
            .eq("scheme_id", scheme_id)
            .execute()
        )
        elig_data = elig_res.data[0] if elig_res.data else None

        docs_res = (
            self.client.table("scheme_documents")
            .select("*")
            .eq("scheme_id", scheme_id)
            .execute()
        )
        docs_data = docs_res.data or []

        srcs_res = (
            self.client.table("scheme_sources")
            .select("*")
            .eq("scheme_id", scheme_id)
            .execute()
        )
        srcs_data = srcs_res.data or []

        return SchemeDetailResponse(
            **scheme_row,
            activity=activity_info,
            eligibility=elig_data,
            documents=docs_data,
            sources=srcs_data,
        )

    def search_schemes(
        self, query_text: str, limit: int = 50, offset: int = 0
    ) -> SchemeListResponse:
        """Search schemes by keyword in scheme_name or description."""
        if not query_text or not query_text.strip():
            return SchemeListResponse(total=0, count=0, offset=offset, limit=limit, data=[])

        cleaned = query_text.strip()
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        # PostgREST OR filter across name and description
        search_filter = f"scheme_name.ilike.%{cleaned}%,description.ilike.%{cleaned}%"
        query = (
            self.client.table("schemes")
            .select("*", count="exact")
            .or_(search_filter)
            .range(offset, offset + limit - 1)
        )
        res = query.execute()

        rows = res.data or []
        total = res.count if res.count is not None else len(rows)

        items = [SchemeItemResponse(**row, activity=get_scheme_activity(row)) for row in rows]
        return SchemeListResponse(
            total=total,
            count=len(items),
            offset=offset,
            limit=limit,
            data=items,
        )

    def get_schemes_by_state(
        self, state_identifier: str, limit: int = 50, offset: int = 0
    ) -> SchemeListResponse:
        """
        Fetch schemes restricted to a specific State or UT.
        state_identifier can be a numeric state_id, an ISO state code ('TN'),
        or full state name ('Tamil Nadu').
        """
        state_id: Optional[int] = None

        if state_identifier.isdigit():
            state_id = int(state_identifier)
        else:
            # Query states table to resolve ID
            st_res = (
                self.client.table("states")
                .select("id")
                .or_(f"code.ilike.{state_identifier.strip()},name.ilike.{state_identifier.strip()}")
                .limit(1)
                .execute()
            )
            if st_res.data:
                state_id = st_res.data[0]["id"]
            else:
                return SchemeListResponse(
                    total=0, count=0, offset=offset, limit=limit, data=[]
                )

        return self.get_schemes(
            limit=limit,
            offset=offset,
            government_level="STATE",
            state_id=state_id,
        )

    def get_central_schemes(self, limit: int = 50, offset: int = 0) -> SchemeListResponse:
        """Fetch Pan-India Central Government welfare schemes."""
        return self.get_schemes(
            limit=limit,
            offset=offset,
            government_level="CENTRAL",
        )

    def get_active_schemes(
        self, limit: int = 50, offset: int = 0, current_datetime: Optional[datetime] = None
    ) -> SchemeListResponse:
        """
        Fetch currently open and actionable welfare schemes.
        Strictly excludes schemes whose effective registration status is EXPIRED,
        NOT_YET_OPEN, or INACTIVE, even if their database status is labeled 'ACTIVE'.
        """
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        # Retrieve candidate schemes from database
        query = self.client.table("schemes").select("*").eq("status", "ACTIVE").order("created_at", desc=True)
        res = query.execute()
        rows = res.data or []

        # Filter strictly for effective OPEN activity and non-expired deadline
        active_items: List[SchemeItemResponse] = []
        for row in rows:
            activity = get_scheme_activity(row, current_datetime=current_datetime)
            if activity.status == ActivityStatus.OPEN and activity.is_actionable:
                active_items.append(SchemeItemResponse(**row, activity=activity))

        total_active = len(active_items)
        paginated_items = active_items[offset : offset + limit]

        return SchemeListResponse(
            total=total_active,
            count=len(paginated_items),
            offset=offset,
            limit=limit,
            data=paginated_items,
        )
