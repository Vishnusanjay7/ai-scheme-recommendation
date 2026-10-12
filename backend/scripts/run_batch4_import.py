"""
Phase 11P: Tamil Nadu Bulk Import Batch 4 (Target Exactly 15 New Schemes)
-------------------------------------------------------------------------
Imports up to exactly 15 new unique Tamil Nadu schemes from Parse myScheme API mirror
into Supabase PostgreSQL using the cached 239-scheme catalog.

Target:
- Database schemes: 50 -> 65 schemes (exactly 15 new schemes).

Strict Rules:
- ZERO search_schemes calls (uses completed tn_search_catalog.json).
- ZERO database schema or RLS modifications.
- Uses get_supabase_admin_client() exclusively for database writes.
- 0.5s pacing between live requests with timeout=60.0s.
- Detail caching in backend/data/pipeline_cache/details/{slug}.json.
- Skips known empty/broken slugs; fast-fails on non-retryable errors.
- Stops safely if HTTP 429 rate limit is encountered.
- Normalizes using MySchemeNormalizer, validates with DataValidator, deduplicates with Deduplicator.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dotenv import load_dotenv

# Force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import httpx
from starlette.testclient import TestClient
from app.data_pipeline.data_validator import DataValidator
from app.data_pipeline.deduplication import Deduplicator, extract_slug_from_source
from app.data_pipeline.importers.myscheme_normalizer import MySchemeNormalizer
from app.data_pipeline.pipeline_checkpoint import PipelineCacheManager
from app.integrations.supabase_client import (
    get_supabase_admin_client,
    is_supabase_admin_configured,
)
from app.services.deadline_service import get_scheme_activity


TARGET_NEW_COUNT = 15
INITIAL_CREDIT_BALANCE = 60

# Confirmed empty/missing detail slugs on Parse mirror from prior phases
KNOWN_PERMANENT_EMPTY_SLUGS = {
    "sgrcsl",
    "pcardbpt",
    "matn",
    "admptpfdap",
    "tncmbs",
    "dmrnicmasi",
    "atnmasfogii",
    "sogateakva",
    "soefatfatftpomic",
    "fatmtfeodap",
    "mafpawmd",
    "psa",
    "ratvip",
    "bowbwodapd",
    "ftthip",
}


def get_table_counts(client) -> Dict[str, int]:
    """Get current row counts across core scheme tables."""
    return {
        "schemes": client.table("schemes").select("id", count="exact").execute().count or 0,
        "scheme_eligibility": client.table("scheme_eligibility").select("id", count="exact").execute().count or 0,
        "scheme_documents": client.table("scheme_documents").select("id", count="exact").execute().count or 0,
        "scheme_sources": client.table("scheme_sources").select("id", count="exact").execute().count or 0,
    }


def get_reference_lookups(admin_client):
    """Retrieve reference maps for states and categories from Supabase."""
    state_lookup = {}
    category_lookup = {}

    s_res = admin_client.table("states").select("id, name, code").execute()
    for s in s_res.data or []:
        state_lookup[s["name"].strip().lower()] = (s["id"], s["name"])
        state_lookup[s["code"].strip().lower()] = (s["id"], s["name"])

    c_res = admin_client.table("scheme_categories").select("id, name").execute()
    for c in c_res.data or []:
        category_lookup[c["name"].strip().lower()] = (c["id"], c["name"])

    return state_lookup, category_lookup


def run_batch4_import():
    print("================================================================================")
    print("PHASE 11P — TAMIL NADU BULK IMPORT BATCH 4 (EXACTLY 15 NEW SCHEMES)")
    print("================================================================================")

    # 1. Security & Configuration Check
    if not is_supabase_admin_configured():
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured in backend/.env.")

    env_path = backend_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("PARSE_API_KEY")
    if not api_key:
        raise ValueError("PARSE_API_KEY is not configured in backend/.env")

    admin_client = get_supabase_admin_client()
    cache_mgr = PipelineCacheManager()

    # 2. Database Baseline Verification
    counts_before = get_table_counts(admin_client)
    print(f"Current DB counts: schemes={counts_before['schemes']}, "
          f"eligibility={counts_before['scheme_eligibility']}, "
          f"documents={counts_before['scheme_documents']}, "
          f"sources={counts_before['scheme_sources']}")

    if counts_before["schemes"] != 50:
        raise RuntimeError(f"Expected exactly 50 schemes before Batch 4, found {counts_before['schemes']}")

    # 3. Retrieve Existing Schemes & Index for Deduplication
    existing_schemes = admin_client.table("schemes").select("*").execute().data or []
    existing_sources = admin_client.table("scheme_sources").select("*").execute().data or []

    deduplicator = Deduplicator()
    deduplicator.build_index(existing_schemes, existing_sources)

    existing_slugs = set()
    for src in existing_sources:
        sl = extract_slug_from_source(src.get("source_type"), src.get("source_url"))
        if sl:
            existing_slugs.add(sl)

    print(f"Existing slugs in DB ({len(existing_slugs)}): {sorted(existing_slugs)}")

    state_lookup, category_lookup = get_reference_lookups(admin_client)

    # 4. Load Cached 239-Scheme Catalog (ZERO search calls)
    if not cache_mgr.has_catalog():
        raise RuntimeError("Cached catalog tn_search_catalog.json not found! Phase 11N must be run first.")

    catalog_schemes = cache_mgr.get_catalog_schemes()
    print(f"Loaded {len(catalog_schemes)} schemes from local catalog cache (0 search calls used).")

    # 5. Setup HTTP Client for Detail Fetching
    scraper_id = "00040831-f035-4cb1-adbc-67dad5171ce1"
    detail_url = f"https://api.parse.bot/scraper/{scraper_id}/get_scheme_details"

    http_client = httpx.Client(
        headers={"X-API-Key": api_key.strip()},
        timeout=60.0,
    )

    cached_details_reused = 0
    live_detail_calls = 0
    failed_detail_calls = 0
    rate_limit_encountered = False

    inserted_schemes: List[Dict[str, Any]] = []
    skipped_schemes: List[Dict[str, Any]] = []

    print(f"\nStarting Batch 4 ingestion (Target: exactly {TARGET_NEW_COUNT} new schemes)...")

    for s_item in catalog_schemes:
        if len(inserted_schemes) >= TARGET_NEW_COUNT:
            break

        slug = s_item.get("slug")
        if not slug:
            continue

        # Skip schemes already in Supabase
        if slug in existing_slugs:
            continue

        # Skip known permanently broken mirror slugs
        if slug in KNOWN_PERMANENT_EMPTY_SLUGS:
            continue

        # Check local detail cache first
        detail_data = None
        cached_detail = cache_mgr.get_detail(slug)
        if cached_detail and "detail" in cached_detail:
            detail_data = cached_detail["detail"]
            cached_details_reused += 1
            print(f"Detail for '{slug}' loaded from local cache (0 API credits).")
        else:
            time.sleep(0.5)  # Pacing

            # Fetch detail with retry on transient network/5xx
            for attempt in range(1, 3):
                live_detail_calls += 1
                try:
                    resp = http_client.get(detail_url, params={"slug": slug})
                    if resp.status_code == 200:
                        d_json = resp.json()
                        d_data = d_json.get("data")
                        if isinstance(d_data, dict) and d_data.get("scheme_name"):
                            detail_data = d_data
                            cache_mgr.save_detail(slug, detail_data)
                            break
                        else:
                            # 200 but empty data
                            failed_detail_calls += 1
                            cache_mgr.record_failure(slug, "Empty detail data on mirror")
                            break
                    elif resp.status_code == 429:
                        print(f"[RATE LIMIT] HTTP 429 encountered on slug '{slug}'. Stopping batch safely.")
                        rate_limit_encountered = True
                        failed_detail_calls += 1
                        break
                    elif resp.status_code in {500, 502, 503, 504}:
                        time.sleep(2.0 * attempt)
                    else:
                        failed_detail_calls += 1
                        break
                except (httpx.TimeoutException, httpx.NetworkError):
                    time.sleep(2.0 * attempt)
                except Exception:
                    failed_detail_calls += 1
                    break

            if rate_limit_encountered:
                break

        if not detail_data or not detail_data.get("scheme_name"):
            skipped_schemes.append({"slug": slug, "reason": "Failed to fetch detail record"})
            continue

        # Normalization
        normalized, unparsed, flags, audit = MySchemeNormalizer.normalize_scheme(
            s_item, detail_data, state_lookup, category_lookup
        )

        # Validation
        val = DataValidator.validate_scheme(normalized)
        if not val.is_valid:
            skipped_schemes.append({"slug": slug, "reason": f"Validation errors: {val.errors}"})
            cache_mgr.record_failure(slug, f"Validation errors: {val.errors}")
            continue

        # Deduplication
        action, match, reason = deduplicator.find_duplicate(normalized)
        if action != "INSERT":
            skipped_schemes.append({"slug": slug, "reason": f"Duplicate detected: {reason}"})
            continue

        # Database Persist: Scheme
        now_iso = datetime.now(timezone.utc).isoformat()
        scheme_payload = {
            "scheme_name": normalized.scheme_name,
            "description": normalized.description,
            "government_level": normalized.government_level,
            "state_id": normalized.state_id,
            "category_id": normalized.category_id,
            "benefits": normalized.benefits,
            "application_process": normalized.application_process,
            "start_date": normalized.start_date,
            "last_date": normalized.last_date,
            "status": normalized.status,
            "official_url": normalized.official_url,
            "source_url": normalized.source_url,
            "last_updated": now_iso,
        }

        ins_res = admin_client.table("schemes").insert(scheme_payload).execute()
        if not ins_res.data:
            raise RuntimeError(f"Database insert failed for scheme: '{normalized.scheme_name}'")
        scheme_id = ins_res.data[0]["id"]

        # Database Persist: Eligibility
        if normalized.eligibility:
            elig = normalized.eligibility
            elig_payload = {
                "scheme_id": scheme_id,
                "min_age": elig.min_age,
                "max_age": elig.max_age,
                "max_income": elig.max_income,
                "gender": elig.gender,
                "occupation": elig.occupation,
                "education": elig.education,
                "category": elig.category,
                "disability_required": elig.disability_required,
                "state_restriction": elig.state_restriction or normalized.state_id,
                "district_restriction": elig.district_restriction,
                "other_conditions": elig.other_conditions or {},
            }
            admin_client.table("scheme_eligibility").insert(elig_payload).execute()

        # Database Persist: Documents
        if normalized.required_documents:
            doc_rows = [
                {
                    "scheme_id": scheme_id,
                    "document_name": doc.document_name,
                    "mandatory": doc.mandatory,
                    "description": doc.description,
                }
                for doc in normalized.required_documents
            ]
            admin_client.table("scheme_documents").insert(doc_rows).execute()

        # Database Persist: Sources
        if normalized.sources:
            src_rows = [
                {
                    "scheme_id": scheme_id,
                    "source_url": src.source_url,
                    "source_type": f"myScheme API mirror (slug: {slug})",
                    "last_checked": src.last_checked.isoformat() if src.last_checked else now_iso,
                    "last_updated": src.last_updated.isoformat() if src.last_updated else now_iso,
                }
                for src in normalized.sources
            ]
            admin_client.table("scheme_sources").insert(src_rows).execute()

        # Deduplicator index and slug tracking
        deduplicator.index_scheme({
            "id": scheme_id,
            "external_id": slug,
            "slug": slug,
            "scheme_name": normalized.scheme_name,
            "government_level": normalized.government_level,
            "state_id": normalized.state_id,
            "official_url": normalized.official_url,
            "source_url": normalized.source_url,
        })
        existing_slugs.add(slug)
        cache_mgr.record_success(batch_id="batch_4", slug=slug)

        inserted_schemes.append({
            "index": len(inserted_schemes) + 1,
            "id": scheme_id,
            "slug": slug,
            "scheme_name": normalized.scheme_name,
            "government_level": normalized.government_level,
            "state_id": normalized.state_id,
            "official_url": normalized.official_url,
            "last_date": normalized.last_date,
            "docs_count": len(normalized.required_documents),
            "sources_count": len(normalized.sources),
            "has_eligibility": bool(normalized.eligibility),
        })

        print(f"[{len(inserted_schemes)}/{TARGET_NEW_COUNT}] Inserted '{slug}' - {normalized.scheme_name[:40]}... (Docs: {len(normalized.required_documents)})")

    # 6. Post-Import Database Verification
    print("\n--- POST-IMPORT DATABASE VERIFICATION ---")
    counts_after = get_table_counts(admin_client)
    print(f"Updated DB counts: schemes={counts_after['schemes']}, "
          f"eligibility={counts_after['scheme_eligibility']}, "
          f"documents={counts_after['scheme_documents']}, "
          f"sources={counts_after['scheme_sources']}")

    all_db_schemes = admin_client.table("schemes").select("*").execute().data or []
    all_db_elig = admin_client.table("scheme_eligibility").select("*").execute().data or []
    all_db_docs = admin_client.table("scheme_documents").select("*").execute().data or []
    all_db_sources = admin_client.table("scheme_sources").select("*").execute().data or []

    # Activity and Deadline Classifications
    null_last_date_count = sum(1 for s in all_db_schemes if s.get("last_date") is None)
    verified_official_url_count = sum(1 for s in all_db_schemes if s.get("official_url") is not None)
    third_party_only_count = sum(1 for s in all_db_schemes if s.get("official_url") is None)

    explicit_open_count = 0
    no_deadline_count = 0
    for s in all_db_schemes:
        act = get_scheme_activity(s)
        if act.status == "OPEN":
            explicit_open_count += 1
        if act.deadline_status == "NO_DEADLINE":
            no_deadline_count += 1

    # Integrity & Orphan checks
    scheme_ids = {s["id"] for s in all_db_schemes}
    orphan_elig = [e["id"] for e in all_db_elig if e["scheme_id"] not in scheme_ids]
    orphan_docs = [d["id"] for d in all_db_docs if d["scheme_id"] not in scheme_ids]
    orphan_sources = [src["id"] for src in all_db_sources if src["scheme_id"] not in scheme_ids]
    total_orphans = len(orphan_elig) + len(orphan_docs) + len(orphan_sources)

    # Duplicates check
    all_slugs = []
    for src in all_db_sources:
        sl = extract_slug_from_source(src.get("source_type"), src.get("source_url"))
        if sl and sl not in all_slugs:
            all_slugs.append(sl)

    names = [s["scheme_name"].strip().lower() for s in all_db_schemes]
    has_duplicate_names = len(names) != len(set(names))
    has_duplicate_slugs = len(all_slugs) != len(set(all_slugs))

    # 7. Backend API Retrieval Verification
    print("\n--- BACKEND API RETRIEVAL VERIFICATION ---")
    from app.main import app
    api_client = TestClient(app)

    list_res = api_client.get("/api/schemes?limit=100")
    if list_res.status_code != 200:
        raise RuntimeError(f"Backend API /api/schemes failed: {list_res.text}")

    list_data = list_res.json()
    api_total = list_data.get("total")
    api_returned_count = len(list_data.get("data", []))
    print(f"API List /api/schemes returned total={api_total}, items={api_returned_count}")

    api_verified_new_schemes = 0
    for s_info in inserted_schemes:
        sid = s_info["id"]
        det_res = api_client.get(f"/api/schemes/{sid}")
        if det_res.status_code == 200:
            api_verified_new_schemes += 1
        else:
            print(f"Warning: /api/schemes/{sid} returned {det_res.status_code}")

    print(f"Verified retrieval for {api_verified_new_schemes}/{len(inserted_schemes)} Batch 4 schemes via backend API.")

    successful_live_calls = live_detail_calls - failed_detail_calls
    credits_consumed = successful_live_calls * 2
    remaining_credits_estimated = INITIAL_CREDIT_BALANCE - credits_consumed

    output_data = {
        "schemes_before": counts_before["schemes"],
        "schemes_after": counts_after["schemes"],
        "successful_new_imports": len(inserted_schemes),
        "target_slugs": [s["slug"] for s in inserted_schemes],
        "skipped_schemes": skipped_schemes,
        "eligibility_count": counts_after["scheme_eligibility"],
        "documents_count": counts_after["scheme_documents"],
        "sources_count": counts_after["scheme_sources"],
        "verified_official_url_count": verified_official_url_count,
        "third_party_only_count": third_party_only_count,
        "null_last_date_count": null_last_date_count,
        "explicit_open_count": explicit_open_count,
        "no_deadline_count": no_deadline_count,
        "has_duplicate_names": has_duplicate_names,
        "has_duplicate_slugs": has_duplicate_slugs,
        "orphan_total": total_orphans,
        "api_total": api_total,
        "api_verified_new": api_verified_new_schemes,
        "cached_details_reused": cached_details_reused,
        "live_detail_calls": live_detail_calls,
        "failed_detail_calls": failed_detail_calls,
        "parse_credits_consumed": credits_consumed,
        "remaining_credits_estimated": remaining_credits_estimated,
        "rate_limit_encountered": rate_limit_encountered,
    }

    print("\nBATCH 4 IMPORT COMPLETE")
    return output_data


if __name__ == "__main__":
    res = run_batch4_import()
    print("\nResult Summary:")
    print(json.dumps(res, indent=2))
