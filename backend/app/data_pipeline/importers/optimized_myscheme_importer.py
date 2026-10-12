"""
Optimized myScheme Batch Importer
----------------------------------
Hardened, credit-minimized ingestion engine for Parse myScheme data.

Optimization Features:
1. Sizing: Requests search pages with size=100 (maximum supported by Parse API).
2. Local Caching: Caches full search catalog and individual scheme details locally
   to eliminate duplicate network calls across runs and crashes.
3. Pre-filtering: Queries Supabase and local checkpoint to skip already-persisted
   or canary schemes BEFORE making any detail API calls.
4. Resumability: Seamlessly resumes from checkpoint without repeating prior work.
5. Rate Limiting & Backoff: Throttles API requests with exponential backoff on
   transient HTTP errors (429, 502, 503, 504, timeout).
6. Security & Invariant: Zero secrets persisted; zero changes to database schema or RLS.
7. Dry-Run Mode: Full offline simulation with zero live API calls and zero database writes.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import httpx
from dotenv import load_dotenv

from app.data_pipeline.data_validator import DataValidator
from app.data_pipeline.deduplication import Deduplicator, extract_slug_from_source
from app.data_pipeline.importers.myscheme_normalizer import MySchemeNormalizer
from app.data_pipeline.pipeline_checkpoint import PipelineCacheManager, QuotaEstimator
from app.integrations.supabase_client import (
    get_supabase_admin_client,
    is_supabase_admin_configured,
)
from app.utils.logger import pipeline_logger


CANARY_SLUGS = {
    "mranmas1",
    "uyegp",
    "atwsfww",
    "cmgcpsii",
    "gwwh",
}


class OptimizedMySchemeImporter:
    """
    Production-hardened importer designed to minimize Parse API credit usage.
    """

    SCRAPER_ID = "00040831-f035-4cb1-adbc-67dad5171ce1"
    BASE_URL = "https://api.parse.bot/scraper"
    SEARCH_PAGE_SIZE = 100  # Documented maximum size per call
    TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        cache_manager: Optional[PipelineCacheManager] = None,
        rate_limit_delay: float = 0.5,
        max_retries: int = 3,
        dry_run: bool = True,
    ):
        self.cache_manager = cache_manager or PipelineCacheManager()
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.search_url = f"{self.BASE_URL}/{self.SCRAPER_ID}/search_schemes"
        self.detail_url = f"{self.BASE_URL}/{self.SCRAPER_ID}/get_scheme_details"

    def get_existing_slugs_from_db(self, admin_client) -> Tuple[Set[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Query Supabase to identify all scheme slugs currently persisted.
        Returns:
            existing_slugs: set of all slugs in DB + canaries
            schemes: raw list of scheme rows
            sources: raw list of scheme_source rows
        """
        schemes = admin_client.table("schemes").select("id, scheme_name, state_id, government_level, official_url, last_date").execute().data or []
        sources = admin_client.table("scheme_sources").select("id, scheme_id, source_type, source_url").execute().data or []

        existing_slugs = set(CANARY_SLUGS)
        for src in sources:
            slug = extract_slug_from_source(src.get("source_type"), src.get("source_url"))
            if slug:
                existing_slugs.add(slug)

        return existing_slugs, schemes, sources

    def get_reference_lookups(self, admin_client) -> Tuple[Dict[str, Tuple[int, str]], Dict[str, Tuple[int, str]]]:
        """Retrieve state and category lookup tables from Supabase."""
        state_lookup: Dict[str, Tuple[int, str]] = {}
        category_lookup: Dict[str, Tuple[int, str]] = {}

        s_res = admin_client.table("states").select("id, name, code").execute()
        for s in s_res.data or []:
            state_lookup[s["name"].strip().lower()] = (s["id"], s["name"])
            state_lookup[s["code"].strip().lower()] = (s["id"], s["name"])

        c_res = admin_client.table("scheme_categories").select("id, name").execute()
        for c in c_res.data or []:
            category_lookup[c["name"].strip().lower()] = (c["id"], c["name"])

        return state_lookup, category_lookup

    def _http_get_with_retry(
        self,
        client: httpx.Client,
        url: str,
        params: Dict[str, Any],
        call_counter: Dict[str, int],
    ) -> Optional[Dict[str, Any]]:
        """
        Execute an HTTP GET request with rate limiting and exponential backoff.
        Only retries on transient network failures and 429/5xx status codes.
        """
        time.sleep(self.rate_limit_delay)

        for attempt in range(1, self.max_retries + 1):
            call_counter["api_calls"] += 1
            try:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in self.TRANSIENT_STATUS_CODES:
                    call_counter["retries"] += 1
                    backoff = (2 ** attempt) * 0.5
                    time.sleep(backoff)
                else:
                    # Non-transient client error (e.g. 400, 404, 403)
                    call_counter["permanent_failures"] += 1
                    return None
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                call_counter["retries"] += 1
                backoff = (2 ** attempt) * 0.5
                time.sleep(backoff)
            except Exception as exc:
                call_counter["permanent_failures"] += 1
                return None

        return None

    def fetch_or_load_search_catalog(
        self,
        client: Optional[httpx.Client] = None,
        state: str = "Tamil Nadu",
        call_counter: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve search catalog using local cache first, or paginate live with size=100.
        Uses 0 credits if already cached.
        """
        if call_counter is None:
            call_counter = {"api_calls": 0, "retries": 0, "permanent_failures": 0}

        # 1. Check local cache
        if self.cache_manager.has_catalog():
            cached_schemes = self.cache_manager.get_catalog_schemes()
            if cached_schemes:
                return cached_schemes

        # If offline or dry run without live client, return empty or raise
        if self.dry_run or client is None:
            return []

        # 2. Fetch live with size=100 pagination
        all_schemes: List[Dict[str, Any]] = []
        page_from = 0
        total_count = None

        while True:
            res_json = self._http_get_with_retry(
                client=client,
                url=self.search_url,
                params={"from": page_from, "size": self.SEARCH_PAGE_SIZE, "state": state},
                call_counter=call_counter,
            )

            if not res_json or not isinstance(res_json.get("data"), dict):
                break

            data = res_json["data"]
            schemes = data.get("schemes", [])
            if total_count is None:
                total_count = data.get("total", len(schemes))

            if not schemes:
                break

            all_schemes.extend(schemes)
            page_from += len(schemes)

            if total_count is not None and page_from >= total_count:
                break

        # Persist to local cache for future batches (0 credits on subsequent runs)
        if all_schemes:
            self.cache_manager.save_catalog(
                schemes=all_schemes,
                total_count=total_count or len(all_schemes),
                state=state,
                page_size_used=self.SEARCH_PAGE_SIZE,
            )

        return all_schemes

    def get_scheme_detail(
        self,
        slug: str,
        client: Optional[httpx.Client] = None,
        call_counter: Optional[Dict[str, int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve scheme detail using local cache first, or query live with retry.
        Uses 0 credits if already in local cache.
        """
        if call_counter is None:
            call_counter = {"api_calls": 0, "retries": 0, "permanent_failures": 0}

        # 1. Local Cache Check
        cached = self.cache_manager.get_detail(slug)
        if cached and "detail" in cached:
            return cached["detail"]

        if self.dry_run or client is None:
            return None

        # 2. Live API Call
        res_json = self._http_get_with_retry(
            client=client,
            url=self.detail_url,
            params={"slug": slug},
            call_counter=call_counter,
        )

        if not res_json or not isinstance(res_json.get("data"), dict):
            return None

        detail_data = res_json["data"]
        if detail_data and detail_data.get("scheme_name"):
            # Persist to local cache immediately
            self.cache_manager.save_detail(slug, detail_data)
            return detail_data

        return None

    def plan_batch_import(
        self,
        target_count: int = 25,
        state: str = "Tamil Nadu",
        total_catalog_size: int = 240,
    ) -> Dict[str, Any]:
        """
        Generate pre-import execution plan and credit estimation without making API calls.
        """
        if not is_supabase_admin_configured():
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured.")

        admin_client = get_supabase_admin_client()
        existing_slugs, db_schemes, db_sources = self.get_existing_slugs_from_db(admin_client)

        cached_catalog = self.cache_manager.get_catalog_schemes()
        cached_catalog_count = len(cached_catalog)
        cached_detail_slugs = self.cache_manager.get_cached_detail_slugs()

        # Identify candidate slugs from cached catalog if available
        candidate_slugs = []
        for s in cached_catalog:
            sl = s.get("slug")
            if sl and sl not in existing_slugs and sl not in CANARY_SLUGS:
                candidate_slugs.append(sl)

        quota_estimate = QuotaEstimator.calculate_minimum_credits(
            total_catalog_schemes=total_catalog_size,
            already_imported_count=len(existing_slugs),
            cached_catalog_schemes=cached_catalog_count,
            cached_details_count=len(cached_detail_slugs.intersection(candidate_slugs[:target_count])),
            target_import_count=target_count,
        )

        return {
            "mode": "PLAN_ONLY",
            "dry_run": self.dry_run,
            "target_batch_count": target_count,
            "current_db_schemes": len(db_schemes),
            "existing_slugs_count": len(existing_slugs),
            "cached_catalog_count": cached_catalog_count,
            "cached_details_count": len(cached_detail_slugs),
            "available_cached_candidates_count": len(candidate_slugs),
            "candidate_preview": candidate_slugs[:target_count],
            "quota_estimate": quota_estimate,
        }
