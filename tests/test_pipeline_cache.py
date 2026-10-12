"""
Tests for Data Pipeline Local Cache, Checkpointing, and Quota Estimation
-------------------------------------------------------------------------
Verifies:
1. PipelineCacheManager persists and retrieves catalog summaries safely.
2. PipelineCacheManager sanitizes inputs and never stores sensitive keys/tokens.
3. PipelineCacheManager supports resumable checkpointing of successes and failures.
4. QuotaEstimator calculates exact minimum Parse credits according to API rules.
5. OptimizedMySchemeImporter operates in dry-run mode without live network or DB writes.
"""

import os
import sys
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.data_pipeline.pipeline_checkpoint import PipelineCacheManager, QuotaEstimator
from app.data_pipeline.importers.optimized_myscheme_importer import (
    OptimizedMySchemeImporter,
    CANARY_SLUGS,
)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Fixture providing a temporary cache directory."""
    cache_path = tmp_path / "test_pipeline_cache"
    return cache_path


class TestQuotaEstimator:
    """Tests for API credit requirement calculations."""

    def test_minimum_credits_all_remaining_schemes_uncached(self):
        """
        Importing all 210 remaining schemes from scratch:
        - 240 catalog schemes / 100 per page = 3 search calls = 3 credits
        - 210 schemes * 2 credits = 420 detail credits
        - Total = 423 credits
        """
        est = QuotaEstimator.calculate_minimum_credits(
            total_catalog_schemes=240,
            already_imported_count=30,
            cached_catalog_schemes=0,
            cached_details_count=0,
            target_import_count=None,
        )
        assert est["remaining_catalog_schemes"] == 210
        assert est["schemes_to_import"] == 210
        assert est["search_calls_needed"] == 3
        assert est["search_credits_needed"] == 3
        assert est["detail_calls_needed"] == 210
        assert est["detail_credits_needed"] == 420
        assert est["total_credits_needed"] == 423

    def test_minimum_credits_all_remaining_schemes_with_cached_catalog(self):
        """
        When search catalog is already cached, 0 search calls are needed.
        Total = 0 + 420 = 420 credits.
        """
        est = QuotaEstimator.calculate_minimum_credits(
            total_catalog_schemes=240,
            already_imported_count=30,
            cached_catalog_schemes=240,
            cached_details_count=0,
            target_import_count=None,
        )
        assert est["search_calls_needed"] == 0
        assert est["search_credits_needed"] == 0
        assert est["detail_calls_needed"] == 210
        assert est["detail_credits_needed"] == 420
        assert est["total_credits_needed"] == 420

    def test_minimum_credits_batch2_target_25_schemes(self):
        """
        Batch 2 (25 new schemes):
        - If search catalog uncached: 3 search calls (3 credits) + 25 * 2 = 53 credits
        - If search catalog cached: 0 search calls + 25 * 2 = 50 credits
        """
        est_uncached = QuotaEstimator.calculate_minimum_credits(
            total_catalog_schemes=240,
            already_imported_count=30,
            cached_catalog_schemes=0,
            cached_details_count=0,
            target_import_count=25,
        )
        assert est_uncached["schemes_to_import"] == 25
        assert est_uncached["search_credits_needed"] == 3
        assert est_uncached["detail_credits_needed"] == 50
        assert est_uncached["total_credits_needed"] == 53

        est_cached = QuotaEstimator.calculate_minimum_credits(
            total_catalog_schemes=240,
            already_imported_count=30,
            cached_catalog_schemes=240,
            cached_details_count=0,
            target_import_count=25,
        )
        assert est_cached["schemes_to_import"] == 25
        assert est_cached["search_credits_needed"] == 0
        assert est_cached["detail_credits_needed"] == 50
        assert est_cached["total_credits_needed"] == 50


class TestPipelineCacheManager:
    """Tests for local filesystem caching and sanitization."""

    def test_catalog_caching_and_sanitization(self, temp_cache_dir):
        mgr = PipelineCacheManager(cache_dir=temp_cache_dir)
        assert not mgr.has_catalog()

        sample_schemes = [
            {
                "slug": "tn-scheme-1",
                "scheme_name": "Tamil Nadu Agriculture Support",
                "state": "Tamil Nadu",
                "level": "STATE",
                "category": "Agriculture",
                "api_key": "SECRET_SHOULD_BE_DROPPED",
                "auth_token": "BEARER_DROP_ME",
            },
            {
                "slug": "tn-scheme-2",
                "scheme_name": "Tamil Nadu Artist Pension",
                "state": "Tamil Nadu",
                "level": "STATE",
                "category": "Culture",
            },
        ]

        mgr.save_catalog(schemes=sample_schemes, total_count=240, state="Tamil Nadu", page_size_used=100)

        assert mgr.has_catalog()
        cat = mgr.get_catalog()
        assert cat["total_count"] == 240
        assert cat["cached_count"] == 2
        assert len(cat["schemes"]) == 2

        # Verify sensitive keys were stripped
        first_scheme = cat["schemes"][0]
        assert "api_key" not in first_scheme
        assert "auth_token" not in first_scheme
        assert first_scheme["slug"] == "tn-scheme-1"

        slugs = mgr.get_catalog_slugs()
        assert slugs == ["tn-scheme-1", "tn-scheme-2"]

    def test_detail_caching_and_sanitization(self, temp_cache_dir):
        mgr = PipelineCacheManager(cache_dir=temp_cache_dir)
        assert not mgr.has_detail("sample-slug")

        detail_payload = {
            "scheme_name": "Sample Scheme",
            "details": "Scheme description details",
            "benefits": "Financial aid",
            "authorization_header": "Bearer secret_header",
            "key_param": "secret_key",
        }

        mgr.save_detail("sample-slug", detail_payload)
        assert mgr.has_detail("sample-slug")

        cached = mgr.get_detail("sample-slug")
        assert cached is not None
        assert cached["slug"] == "sample-slug"
        assert cached["detail"]["scheme_name"] == "Sample Scheme"
        # Verify auth headers were dropped
        assert "authorization_header" not in cached["detail"]
        assert "key_param" not in cached["detail"]

    def test_resumable_checkpointing(self, temp_cache_dir):
        mgr = PipelineCacheManager(cache_dir=temp_cache_dir)

        mgr.record_success(batch_id="batch_1", slug="slug-a")
        mgr.record_failure(slug="slug-b", reason="Connection timeout")

        cp = mgr.get_checkpoint()
        assert "slug-a" in cp["processed_slugs"]
        assert "slug-b" in cp["failed_slugs"]
        assert cp["failed_slugs"]["slug-b"]["attempts"] == 1

        # Second failure increments attempt counter
        mgr.record_failure(slug="slug-b", reason="503 Service Unavailable")
        cp = mgr.get_checkpoint()
        assert cp["failed_slugs"]["slug-b"]["attempts"] == 2

        # Subsequent success clears the failure record
        mgr.record_success(batch_id="batch_2", slug="slug-b")
        cp = mgr.get_checkpoint()
        assert "slug-b" in cp["processed_slugs"]
        assert "slug-b" not in cp["failed_slugs"]


class TestOptimizedImporterDryRun:
    """Tests verifying dry-run safety and HTTP retry logic."""

    def test_dry_run_plan_without_network_calls(self, temp_cache_dir):
        mgr = PipelineCacheManager(cache_dir=temp_cache_dir)
        importer = OptimizedMySchemeImporter(cache_manager=mgr, dry_run=True)

        # Mock database queries
        mock_admin = MagicMock()
        mock_admin.table.return_value.select.return_value.execute.return_value.data = [
            {"id": "1", "scheme_name": "Canary Scheme 1", "state_id": 23, "government_level": "STATE", "official_url": None, "last_date": None}
        ]

        with patch("app.data_pipeline.importers.optimized_myscheme_importer.is_supabase_admin_configured", return_value=True), \
             patch("app.data_pipeline.importers.optimized_myscheme_importer.get_supabase_admin_client", return_value=mock_admin):
            plan = importer.plan_batch_import(target_count=25, total_catalog_size=240)

        assert plan["mode"] == "PLAN_ONLY"
        assert plan["dry_run"] is True
        assert plan["target_batch_count"] == 25
        assert "quota_estimate" in plan
        assert plan["quota_estimate"]["schemes_to_import"] == 25

    def test_http_get_retry_on_transient_failure(self, temp_cache_dir):
        mgr = PipelineCacheManager(cache_dir=temp_cache_dir)
        importer = OptimizedMySchemeImporter(cache_manager=mgr, rate_limit_delay=0.01, max_retries=2, dry_run=False)

        counter = {"api_calls": 0, "retries": 0, "permanent_failures": 0}

        # Mock client returning 503 then 200
        mock_client = MagicMock()
        mock_resp_fail = MagicMock(status_code=503)
        mock_resp_ok = MagicMock(status_code=200)
        mock_resp_ok.json.return_value = {"status": "ok"}
        mock_client.get.side_effect = [mock_resp_fail, mock_resp_ok]

        with patch("time.sleep", return_value=None):
            res = importer._http_get_with_retry(
                client=mock_client,
                url="https://api.example.com/test",
                params={},
                call_counter=counter,
            )

        assert res == {"status": "ok"}
        assert counter["api_calls"] == 2
        assert counter["retries"] == 1
        assert counter["permanent_failures"] == 0

    def test_http_get_fails_fast_on_404(self, temp_cache_dir):
        mgr = PipelineCacheManager(cache_dir=temp_cache_dir)
        importer = OptimizedMySchemeImporter(cache_manager=mgr, rate_limit_delay=0.01, max_retries=3, dry_run=False)

        counter = {"api_calls": 0, "retries": 0, "permanent_failures": 0}

        # 404 should fail immediately without retrying
        mock_client = MagicMock()
        mock_resp = MagicMock(status_code=404)
        mock_client.get.return_value = mock_resp

        with patch("time.sleep", return_value=None):
            res = importer._http_get_with_retry(
                client=mock_client,
                url="https://api.example.com/test",
                params={},
                call_counter=counter,
            )

        assert res is None
        assert counter["api_calls"] == 1
        assert counter["retries"] == 0
        assert counter["permanent_failures"] == 1
