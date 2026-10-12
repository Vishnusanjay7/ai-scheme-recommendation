"""
Complete Tamil Nadu Search Catalog Cache Script (Phase 11N)
-----------------------------------------------------------
Builds a complete local cache of the Tamil Nadu search catalog
using the minimum possible number of search_schemes calls.

Rules:
1. READ-ONLY with respect to Supabase (Zero database writes, zero schema/RLS changes).
2. Zero scheme details fetched (0 get_scheme_details calls).
3. Do NOT re-fetch page 0 if existing cached page (100 schemes) is valid.
4. Uses size=100 for all queries.
5. Retrieves only missing pages (page 1: from=100, page 2: from=200).
6. Deduplicates by source slug/ID preserving source metadata.
7. Saves completed catalog to backend/data/pipeline_cache/tn_search_catalog.json.
8. Never prints or exposes PARSE_API_KEY.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from dotenv import load_dotenv
import httpx

# Force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.data_pipeline.pipeline_checkpoint import PipelineCacheManager


def complete_tn_search_catalog():
    print("================================================================================")
    print("PHASE 11N — COMPLETE TAMIL NADU SEARCH CATALOG CACHE (READ-ONLY)")
    print("================================================================================")

    cache_mgr = PipelineCacheManager()
    catalog_path = cache_mgr.catalog_file

    # 1. Inspect existing cached catalog
    existing_schemes: List[Dict[str, Any]] = []
    existing_slugs: Set[str] = set()

    if catalog_path.is_file():
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                cat_data = json.load(f)
                existing_schemes = cat_data.get("schemes", [])
                for s in existing_schemes:
                    slug = s.get("slug")
                    if slug:
                        existing_slugs.add(slug)
            print(f"1. Existing cached records: {len(existing_schemes)} schemes (Unique slugs: {len(existing_slugs)})")
        except Exception as exc:
            print(f"Warning: Failed to parse existing catalog file: {exc}")
    else:
        print("1. No existing catalog found on disk.")

    # 2. Setup Parse API Client
    env_path = backend_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    key = os.getenv("PARSE_API_KEY")
    if not key:
        raise ValueError("PARSE_API_KEY is not configured in backend/.env")

    scraper_id = "00040831-f035-4cb1-adbc-67dad5171ce1"
    search_url = f"https://api.parse.bot/scraper/{scraper_id}/search_schemes"

    client = httpx.Client(
        headers={"X-API-Key": key.strip()},
        timeout=30.0,
    )

    page_size = 100
    start_offset = len(existing_schemes) if len(existing_schemes) >= 100 else 0
    if start_offset > 0:
        print(f"2. Valid page 0 ({start_offset} schemes) detected in cache. Skipping page 0 to conserve credits.")

    new_search_calls = 0
    new_records_obtained = 0
    duplicate_count = 0
    missing_failed_pages = []
    all_schemes: List[Dict[str, Any]] = list(existing_schemes)
    seen_slugs: Set[str] = set(existing_slugs)

    current_offset = start_offset
    total_catalog_reported = 240

    while True:
        print(f"\nFetching search page: state='Tamil Nadu', from={current_offset}, size={page_size}...")
        resp_json = None
        new_search_calls += 1

        for attempt in range(1, 4):
            try:
                resp = client.get(
                    search_url,
                    params={"from": current_offset, "size": page_size, "state": "Tamil Nadu"},
                )
                if resp.status_code == 200:
                    resp_json = resp.json()
                    break
                elif resp.status_code in {429, 500, 502, 503, 504}:
                    print(f"   Transient error HTTP {resp.status_code} on attempt {attempt}. Retrying...")
                    time.sleep(2.0 * attempt)
                else:
                    print(f"   Non-retryable status HTTP {resp.status_code} received.")
                    break
            except Exception as exc:
                print(f"   Request exception on attempt {attempt}: {exc}")
                time.sleep(2.0 * attempt)

        if not resp_json or not isinstance(resp_json.get("data"), dict):
            print(f"   Failed to fetch page at offset {current_offset}.")
            missing_failed_pages.append(f"offset_{current_offset}")
            break

        data = resp_json["data"]
        schemes = data.get("schemes", [])
        total_reported = data.get("total", total_catalog_reported)
        total_catalog_reported = total_reported

        print(f"   Search call succeeded! Returned {len(schemes)} schemes (Total reported by API: {total_reported}).")

        if not schemes:
            print("   No more schemes returned on this page.")
            break

        # Process and deduplicate schemes
        page_new_count = 0
        for s in schemes:
            slug = s.get("slug")
            if not slug:
                continue

            if slug in seen_slugs:
                duplicate_count += 1
                continue

            seen_slugs.add(slug)
            all_schemes.append(s)
            page_new_count += 1

        new_records_obtained += page_new_count
        print(f"   Added {page_new_count} new unique schemes from this page (Total accumulated: {len(all_schemes)}).")

        current_offset += len(schemes)

        # Stop if we have reached or exceeded total reported by API, or got a partial page
        if len(schemes) < page_size or (total_reported is not None and current_offset >= total_reported):
            print(f"   Reached end of catalog (offset {current_offset} of {total_reported}).")
            break

        time.sleep(1.0)  # Pacing between search calls

    # 3. Save the completed catalog to the existing cache location
    print(f"\n3. Saving completed catalog to {catalog_path}...")
    cache_mgr.save_catalog(
        schemes=all_schemes,
        total_count=total_catalog_reported or len(all_schemes),
        state="Tamil Nadu",
        page_size_used=page_size,
    )

    # Verify the saved file
    saved_catalog = cache_mgr.get_catalog()
    final_unique_count = saved_catalog.get("cached_count", len(all_schemes))
    print(f"   Successfully saved {final_unique_count} unique Tamil Nadu schemes to cache.")

    credits_consumed = new_search_calls  # 1 credit per successful search_schemes call

    summary = {
        "existing_cached_records": len(existing_schemes),
        "new_search_calls_made": new_search_calls,
        "new_records_obtained": new_records_obtained,
        "final_unique_catalog_count": final_unique_count,
        "duplicate_count": duplicate_count,
        "missing_failed_pages": missing_failed_pages,
        "parse_credits_consumed": credits_consumed,
        "catalog_file": str(catalog_path),
    }

    print("\nResult Summary:")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    complete_tn_search_catalog()
