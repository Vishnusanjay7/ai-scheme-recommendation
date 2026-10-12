"""
Data Pipeline Checkpoint & Local Caching Architecture
------------------------------------------------------
Provides secure, secret-free local caching and resumable checkpointing
for the Government Scheme Ingestion Pipeline.

Features:
- Search Catalog Caching: Persists discovered scheme summaries to eliminate
  redundant search_schemes API calls across batch runs.
- Scheme Detail Caching: Persists fetched detail payloads to eliminate
  redundant get_scheme_details API calls upon interruption/retry.
- Quota & Credit Estimation: Computes minimum Parse credits needed based on
  documented endpoint pricing (1 credit/search with size=100, 2 credits/detail).
- Security Guarantee: Never stores API keys, service role credentials, or
  authorization headers in cache files. Only public scheme data is stored.
- Database Invariant: Zero schema or RLS modifications.
"""

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "pipeline_cache"


class PipelineCacheManager:
    """
    Manages local filesystem caching for search summaries and scheme details.
    Guarantees no sensitive credentials are ever persisted.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = Path(cache_dir or DEFAULT_CACHE_DIR)
        self.catalog_file = self.cache_dir / "tn_search_catalog.json"
        self.checkpoint_file = self.cache_dir / "import_checkpoint.json"
        self.details_dir = self.cache_dir / "details"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create cache directory hierarchy if not existing."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.details_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Search Catalog Operations
    # -------------------------------------------------------------------------

    def has_catalog(self) -> bool:
        """Check if search catalog is already cached locally."""
        return self.catalog_file.is_file() and self.catalog_file.stat().st_size > 10

    def get_catalog(self) -> Optional[Dict[str, Any]]:
        """Retrieve the cached search catalog."""
        if not self.has_catalog():
            return None
        try:
            with open(self.catalog_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def get_catalog_schemes(self) -> List[Dict[str, Any]]:
        """Retrieve list of scheme summaries from catalog cache."""
        data = self.get_catalog()
        if data and isinstance(data.get("schemes"), list):
            return data["schemes"]
        return []

    def get_catalog_slugs(self) -> List[str]:
        """Return all unique slugs in the cached catalog preserving order."""
        schemes = self.get_catalog_schemes()
        slugs = []
        for s in schemes:
            sl = s.get("slug")
            if sl and sl not in slugs:
                slugs.append(sl)
        return slugs

    def save_catalog(
        self,
        schemes: List[Dict[str, Any]],
        total_count: int,
        state: str = "Tamil Nadu",
        page_size_used: int = 100,
    ) -> None:
        """
        Persist search catalog locally.
        Sanitizes input to guarantee zero secrets are saved.
        """
        sanitized_schemes = []
        seen_slugs = set()
        for s in schemes:
            slug = s.get("slug")
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            # Retain only public scheme search fields
            sanitized_schemes.append({
                "slug": slug,
                "scheme_name": s.get("scheme_name") or s.get("name") or "",
                "state": s.get("state") or state,
                "beneficiary_states": s.get("beneficiary_states") or [s.get("state") or state],
                "level": s.get("level") or s.get("government_level") or "STATE",
                "category": s.get("category") or "",
                "brief_description": s.get("brief_description") or s.get("description") or "",
            })

        payload = {
            "state": state,
            "total_count": total_count,
            "cached_count": len(sanitized_schemes),
            "page_size_used": page_size_used,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "schemes": sanitized_schemes,
        }

        temp_file = self.catalog_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        temp_file.replace(self.catalog_file)

    # -------------------------------------------------------------------------
    # Scheme Detail Cache Operations
    # -------------------------------------------------------------------------

    def _get_detail_path(self, slug: str) -> Path:
        """Return safe filesystem path for a scheme detail cache file."""
        safe_slug = "".join(c for c in slug if c.isalnum() or c in "-_")
        return self.details_dir / f"{safe_slug}.json"

    def has_detail(self, slug: str) -> bool:
        """Check if detail record for slug is cached locally."""
        path = self._get_detail_path(slug)
        return path.is_file() and path.stat().st_size > 10

    def get_detail(self, slug: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached detail record for slug."""
        if not self.has_detail(slug):
            return None
        try:
            with open(self._get_detail_path(slug), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save_detail(self, slug: str, detail_data: Dict[str, Any]) -> None:
        """
        Persist scheme detail locally.
        Sanitizes to remove any sensitive metadata or headers.
        """
        # Create safe copy without any auth headers or request metadata
        safe_data = {
            "slug": slug,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "detail": {k: v for k, v in detail_data.items() if not k.lower().startswith(("auth", "key", "token", "header"))},
        }

        path = self._get_detail_path(slug)
        temp_path = path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(safe_data, f, indent=2, ensure_ascii=False)
        temp_path.replace(path)

    def get_cached_detail_slugs(self) -> Set[str]:
        """Return set of all slugs currently present in the detail cache."""
        slugs = set()
        for p in self.details_dir.glob("*.json"):
            slugs.add(p.stem)
        return slugs

    # -------------------------------------------------------------------------
    # Resumable Checkpoint Operations
    # -------------------------------------------------------------------------

    def get_checkpoint(self) -> Dict[str, Any]:
        """Load execution checkpoint."""
        if self.checkpoint_file.is_file():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "last_run_at": None,
            "batches_completed": [],
            "processed_slugs": [],
            "failed_slugs": {},
        }

    def record_success(self, batch_id: str, slug: str) -> None:
        """Record successful scheme ingestion in checkpoint."""
        cp = self.get_checkpoint()
        if slug not in cp["processed_slugs"]:
            cp["processed_slugs"].append(slug)
        if slug in cp.get("failed_slugs", {}):
            del cp["failed_slugs"][slug]
        if batch_id not in cp.get("batches_completed", []):
            cp["batches_completed"].append(batch_id)
        cp["last_run_at"] = datetime.now(timezone.utc).isoformat()

        temp_file = self.checkpoint_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(cp, f, indent=2)
        temp_file.replace(self.checkpoint_file)

    def record_failure(self, slug: str, reason: str) -> None:
        """Record a failed scheme attempt with reason and retry count."""
        cp = self.get_checkpoint()
        failed = cp.setdefault("failed_slugs", {})
        prev = failed.get(slug, {"attempts": 0, "reason": reason})
        failed[slug] = {
            "attempts": prev.get("attempts", 0) + 1,
            "reason": reason,
            "last_attempt_at": datetime.now(timezone.utc).isoformat(),
        }
        cp["last_run_at"] = datetime.now(timezone.utc).isoformat()

        temp_file = self.checkpoint_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(cp, f, indent=2)
        temp_file.replace(self.checkpoint_file)


class QuotaEstimator:
    """
    Calculates exact Parse API credit requirements based on documented pricing:
    - search_schemes: 1 credit per call (max size = 100)
    - get_scheme_details: 2 credits per call
    """

    CREDIT_COST_SEARCH = 1
    CREDIT_COST_DETAIL = 2
    MAX_SEARCH_PAGE_SIZE = 100

    @classmethod
    def calculate_minimum_credits(
        cls,
        total_catalog_schemes: int = 240,
        already_imported_count: int = 30,
        cached_catalog_schemes: int = 0,
        cached_details_count: int = 0,
        target_import_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculate theoretical minimum credits needed.

        Args:
            total_catalog_schemes: Total schemes in the state catalog (e.g. 240 for TN).
            already_imported_count: Schemes already persisted in Supabase (e.g. 30).
            cached_catalog_schemes: Schemes already stored in local search cache.
            cached_details_count: Scheme details already cached locally.
            target_import_count: Schemes to import in this run (e.g. 25, or None for all remaining).
        """
        remaining_schemes_in_catalog = max(0, total_catalog_schemes - already_imported_count)
        schemes_to_import = remaining_schemes_in_catalog if target_import_count is None else min(target_import_count, remaining_schemes_in_catalog)

        # 1. Search Calls
        # If catalog is already fully cached, 0 search calls are needed.
        if cached_catalog_schemes >= total_catalog_schemes:
            search_calls_needed = 0
        else:
            uncached_search_items = max(0, total_catalog_schemes - cached_catalog_schemes)
            search_calls_needed = math.ceil(uncached_search_items / cls.MAX_SEARCH_PAGE_SIZE)

        search_credits_needed = search_calls_needed * cls.CREDIT_COST_SEARCH

        # 2. Detail Calls
        # Each scheme to import requires 1 detail call (2 credits), unless detail is already cached.
        uncached_details_needed = max(0, schemes_to_import - cached_details_count)
        detail_calls_needed = uncached_details_needed
        detail_credits_needed = detail_calls_needed * cls.CREDIT_COST_DETAIL

        total_credits = search_credits_needed + detail_credits_needed

        return {
            "total_catalog_schemes": total_catalog_schemes,
            "already_imported_count": already_imported_count,
            "remaining_catalog_schemes": remaining_schemes_in_catalog,
            "schemes_to_import": schemes_to_import,
            "max_search_page_size": cls.MAX_SEARCH_PAGE_SIZE,
            "search_calls_needed": search_calls_needed,
            "search_credits_needed": search_credits_needed,
            "detail_calls_needed": detail_calls_needed,
            "detail_credits_needed": detail_credits_needed,
            "total_credits_needed": total_credits,
            "breakdown": {
                "search_call_unit_cost": cls.CREDIT_COST_SEARCH,
                "detail_call_unit_cost": cls.CREDIT_COST_DETAIL,
                "search_calls_description": f"{search_calls_needed} search call(s) with size={cls.MAX_SEARCH_PAGE_SIZE}",
                "detail_calls_description": f"{detail_calls_needed} detail call(s) at 2 credits each",
            },
        }
