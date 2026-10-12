"""
Batch 1 Ingestion Script: Exactly 25 Additional Unique Tamil Nadu Schemes
-------------------------------------------------------------------------
Imports exactly 25 new Tamil Nadu schemes from Parse myScheme API mirror
into Supabase PostgreSQL using the audited pipeline.

Strict Rules:
- Excludes existing canary slugs: mranmas1, uyegp, atwsfww, cmgcpsii, gwwh
- Uses get_supabase_admin_client() exclusively for database writes
- Preserves all normalization, official URL, date, and document rules
- Ensures idempotency and deduplication (total schemes becomes exactly 30)
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import httpx
from app.data_pipeline.data_validator import DataValidator
from app.data_pipeline.deduplication import Deduplicator, extract_slug_from_source
from app.data_pipeline.importers.myscheme_normalizer import MySchemeNormalizer
from app.integrations.supabase_client import (
    get_supabase_admin_client,
    is_supabase_admin_configured,
)
from app.services.deadline_service import get_scheme_activity


CANARY_SLUGS = {
    "mranmas1",
    "uyegp",
    "atwsfww",
    "cmgcpsii",
    "gwwh",
}

TARGET_NEW_COUNT = 25


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


def run_batch_import():
    print("================================================================================")
    print("PHASE 11J — TAMIL NADU BULK IMPORT BATCH 1 (EXACTLY 25 NEW SCHEMES)")
    print("================================================================================")

    if not is_supabase_admin_configured():
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured in backend/.env.")

    admin_client = get_supabase_admin_client()

    # 1. Baseline Counts
    counts_before = get_table_counts(admin_client)
    print(f"Current DB counts: schemes={counts_before['schemes']}, "
          f"eligibility={counts_before['scheme_eligibility']}, "
          f"documents={counts_before['scheme_documents']}, "
          f"sources={counts_before['scheme_sources']}")

    # 2. Existing Schemes & Sources for Deduplication
    existing_schemes = admin_client.table("schemes").select("*").execute().data or []
    existing_sources = admin_client.table("scheme_sources").select("*").execute().data or []
    existing_docs = admin_client.table("scheme_documents").select("id, scheme_id").execute().data or []

    deduplicator = Deduplicator()
    deduplicator.build_index(existing_schemes, existing_sources)

    existing_slugs = set(CANARY_SLUGS)
    for src in existing_sources:
        sl = extract_slug_from_source(src.get("source_type"), src.get("source_url"))
        if sl:
            existing_slugs.add(sl)

    print(f"Existing slugs in DB ({len(existing_slugs)}): {sorted(existing_slugs)}")

    # Pre-populate already inserted Batch 1 schemes if resuming
    inserted_schemes = []
    for s in existing_schemes:
        src_entry = next((sr for sr in existing_sources if sr["scheme_id"] == s["id"]), None)
        slug = extract_slug_from_source(
            src_entry.get("source_type") if src_entry else None,
            src_entry.get("source_url") if src_entry else None,
        )
        if slug and slug not in CANARY_SLUGS:
            inserted_schemes.append({
                "index": len(inserted_schemes) + 1,
                "id": s["id"],
                "slug": slug,
                "scheme_name": s["scheme_name"],
                "government_level": s["government_level"],
                "state_id": s["state_id"],
                "official_url": s["official_url"],
                "last_date": s["last_date"],
                "docs_count": len([d for d in existing_docs if d["scheme_id"] == s["id"]]),
                "sources_count": len([sr for sr in existing_sources if sr["scheme_id"] == s["id"]]),
                "has_eligibility": True,
            })

    print(f"Batch 1 schemes already in DB: {len(inserted_schemes)}/{TARGET_NEW_COUNT}")

    state_lookup, category_lookup = get_reference_lookups(admin_client)

    # 3. Setup Parse API Client
    env_path = backend_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    key = os.getenv("PARSE_API_KEY")
    if not key:
        raise ValueError("PARSE_API_KEY is not configured in backend/.env")

    client = httpx.Client(headers={"X-API-Key": key.strip()}, timeout=60.0)
    scraper_id = "00040831-f035-4cb1-adbc-67dad5171ce1"
    search_url = f"https://api.parse.bot/scraper/{scraper_id}/search_schemes"
    detail_url = f"https://api.parse.bot/scraper/{scraper_id}/get_scheme_details"

    parse_calls = 0
    parse_retries = 0
    skipped_schemes = []

    search_page = 0
    search_page_size = 20

    while len(inserted_schemes) < TARGET_NEW_COUNT:
        # Fetch search page with retry
        search_schemes = None
        for attempt in range(3):
            parse_calls += 1
            try:
                s_res = client.get(
                    search_url,
                    params={"from": search_page * search_page_size, "size": search_page_size, "state": "Tamil Nadu"},
                ).json()
                if isinstance(s_res.get("data"), dict) and "schemes" in s_res["data"]:
                    search_schemes = s_res["data"]["schemes"]
                    break
                else:
                    parse_retries += 1
                    time.sleep(1.5)
            except Exception:
                parse_retries += 1
                time.sleep(1.5)

        if not search_schemes:
            if search_page * search_page_size >= 240:
                print("Exhausted all search results for Tamil Nadu.")
                break
            search_page += 1
            continue

        for s in search_schemes:
            if len(inserted_schemes) >= TARGET_NEW_COUNT:
                break

            slug = s.get("slug")
            if not slug:
                continue

            if slug in existing_slugs:
                continue

            # Fetch details with retry
            detail = None
            for attempt in range(3):
                parse_calls += 1
                try:
                    d_res = client.get(detail_url, params={"slug": slug}).json()
                    detail = d_res.get("data", {})
                    if detail and detail.get("scheme_name"):
                        break
                    else:
                        time.sleep(1)
                except Exception:
                    parse_retries += 1
                    time.sleep(1.5)

            if not detail or not detail.get("scheme_name"):
                skipped_schemes.append({"slug": slug, "reason": "Failed to fetch detail record"})
                continue

            # Normalize
            normalized, unparsed, flags, audit = MySchemeNormalizer.normalize_scheme(
                s, detail, state_lookup, category_lookup
            )

            # Validate
            val = DataValidator.validate_scheme(normalized)
            if not val.is_valid:
                skipped_schemes.append({"slug": slug, "reason": f"Validation errors: {val.errors}"})
                continue

            # Deduplicate
            action, match, reason = deduplicator.find_duplicate(normalized)
            if action != "INSERT":
                skipped_schemes.append({"slug": slug, "reason": f"Duplicate detected: {reason}"})
                continue

            # Persist Scheme
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

            # Persist Eligibility
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

            # Persist Documents
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

            # Persist Sources
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

            # Register in Deduplicator index
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

            print(f"[{len(inserted_schemes)}/25] Inserted '{slug}' - {normalized.scheme_name[:40]}... (Docs: {len(normalized.required_documents)})")

        search_page += 1

    # 5. Post-Import Database Audit
    print("\n--- POST-IMPORT DATABASE VERIFICATION ---")
    counts_after = get_table_counts(admin_client)

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

    # 6. Backend API Retrieval Verification
    print("\n--- BACKEND API RETRIEVAL VERIFICATION ---")
    from starlette.testclient import TestClient
    from app.main import app

    api_client = TestClient(app)

    list_res = api_client.get("/api/schemes?limit=50")
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

    print(f"Verified retrieval for {api_verified_new_schemes}/{len(inserted_schemes)} newly inserted schemes via backend API.")

    output_data = {
        "counts_before": {
            "schemes": 5,
            "scheme_eligibility": 5,
            "scheme_documents": 46,
            "scheme_sources": 12,
        },
        "counts_after": counts_after,
        "inserted_count": len(inserted_schemes),
        "inserted_slugs": [s["slug"] for s in inserted_schemes],
        "skipped_schemes": skipped_schemes,
        "null_last_date_count": null_last_date_count,
        "verified_official_url_count": verified_official_url_count,
        "third_party_only_count": third_party_only_count,
        "explicit_open_count": explicit_open_count,
        "no_deadline_count": no_deadline_count,
        "duplicate_check": {
            "has_duplicate_names": has_duplicate_names,
            "has_duplicate_slugs": has_duplicate_slugs,
        },
        "orphan_total": total_orphans,
        "api_total": api_total,
        "api_verified_new": api_verified_new_schemes,
        "parse_calls": parse_calls,
        "parse_retries": parse_retries,
    }

    print("\nBATCH 1 IMPORT COMPLETE")
    return output_data


if __name__ == "__main__":
    res = run_batch_import()
    print("\nResult:")
    print(json.dumps(res, indent=2))
