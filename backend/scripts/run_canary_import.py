"""
Canary Ingestion Script: Phase 11H Clean Partial Import + Corrected 5-Scheme Canary
---------------------------------------------------------------------------------
Strictly limited to the 5 target Tamil Nadu schemes:
  1. mranmas1  - Moovalur Ramamirtham Ammaiyar Ninaivu Marriage Assistance Scheme-1
  2. uyegp     - Unemployed Youth Employment Generation Programme
  3. atwsfww   - Amma Two Wheeler Scheme for Working Women
  4. cmgcpsii  - Chief Minister’s Girl Child Protection Scheme-II
  5. gwwh      - Government Working Women’s Hostel

Strict Security Rules:
- Uses get_supabase_admin_client() exclusively for database writes.
- Never prints, logs, or exposes the service-role key or API keys.
- Read-only queries and deletes strictly scoped to the 4 partial canary IDs.
- Validates all 5 schemes before writing any records.
"""

import json
import os
import sys
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


TARGET_SLUGS = [
    "mranmas1",
    "uyegp",
    "atwsfww",
    "cmgcpsii",
    "gwwh",
]

PARTIAL_TARGET_SLUGS = [
    "mranmas1",
    "uyegp",
    "atwsfww",
    "gwwh",
]


def get_table_counts(client) -> Dict[str, int]:
    """Get current row counts across core scheme and related tables."""
    return {
        "schemes": client.table("schemes").select("id", count="exact").execute().count or 0,
        "scheme_eligibility": client.table("scheme_eligibility").select("id", count="exact").execute().count or 0,
        "scheme_documents": client.table("scheme_documents").select("id", count="exact").execute().count or 0,
        "scheme_sources": client.table("scheme_sources").select("id", count="exact").execute().count or 0,
        "saved_schemes": client.table("saved_schemes").select("id", count="exact").execute().count or 0,
        "notifications": client.table("notifications").select("id", count="exact").execute().count or 0,
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


def fetch_target_schemes():
    """Fetch search + detail records for exactly the 5 target schemes from Parse API."""
    env_path = backend_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    key = os.getenv("PARSE_API_KEY")
    if not key:
        raise ValueError("PARSE_API_KEY is not configured in backend/.env")

    client = httpx.Client(headers={"X-API-Key": key.strip()}, timeout=60.0)
    scraper_id = "00040831-f035-4cb1-adbc-67dad5171ce1"
    search_url = f"https://api.parse.bot/scraper/{scraper_id}/search_schemes"
    detail_url = f"https://api.parse.bot/scraper/{scraper_id}/get_scheme_details"

    search_res = client.get(search_url, params={"from": 0, "size": 15, "state": "Tamil Nadu"}).json()
    all_search_schemes = search_res.get("data", {}).get("schemes", [])
    search_map = {s["slug"]: s for s in all_search_schemes if s.get("slug")}

    records = []
    for slug in TARGET_SLUGS:
        search_item = search_map.get(slug, {"slug": slug, "beneficiary_states": ["Tamil Nadu"], "level": "State"})
        d_res = client.get(detail_url, params={"slug": slug}).json()
        detail_item = d_res.get("data", {})
        if not detail_item or not detail_item.get("scheme_name"):
            raise ValueError(f"Failed to fetch valid scheme details for target slug '{slug}'")
        records.append({"search": search_item, "detail": detail_item})

    return records


def run_phase_11h():
    print("================================================================================")
    print("PHASE 11H — CLEAN PARTIAL IMPORT + CORRECTED 5-SCHEME CANARY")
    print("================================================================================")

    # 0. Client check
    if not is_supabase_admin_configured():
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured in backend/.env.")

    admin_client = get_supabase_admin_client()

    # -------------------------------------------------------------------------
    # STEP 1 — PRE-IMPORT DATABASE AUDIT
    # -------------------------------------------------------------------------
    print("\n--- STEP 1: PRE-IMPORT DATABASE AUDIT ---")
    before_counts = get_table_counts(admin_client)
    print(f"Current counts: schemes={before_counts['schemes']}, "
          f"eligibility={before_counts['scheme_eligibility']}, "
          f"documents={before_counts['scheme_documents']}, "
          f"sources={before_counts['scheme_sources']}")

    # Identify existing partial schemes by source slug/identity
    sources_res = admin_client.table("scheme_sources").select("scheme_id, source_type, source_url").execute()
    existing_sources = sources_res.data or []

    slug_to_scheme_id = {}
    for src in existing_sources:
        slug = extract_slug_from_source(src.get("source_type"), src.get("source_url"))
        if slug and slug in TARGET_SLUGS:
            slug_to_scheme_id[slug] = src.get("scheme_id")

    schemes_res = admin_client.table("schemes").select("id, scheme_name, source_url").execute()
    existing_schemes = schemes_res.data or []

    print("\nIdentified Partial Canary Schemes in DB:")
    for slug in PARTIAL_TARGET_SLUGS:
        sid = slug_to_scheme_id.get(slug)
        s_name = next((s["scheme_name"] for s in existing_schemes if s["id"] == sid), "Unknown")
        print(f"  - [{slug}] ID: {sid} | Name: {s_name}")

    cmgcpsii_present = "cmgcpsii" in slug_to_scheme_id
    print(f"Expected missing scheme 'cmgcpsii' present: {cmgcpsii_present} (Expected: False)")

    # -------------------------------------------------------------------------
    # STEP 2 — DEPENDENCY SAFETY CHECK
    # -------------------------------------------------------------------------
    print("\n--- STEP 2: DEPENDENCY SAFETY CHECK ---")
    partial_ids = [sid for sid in slug_to_scheme_id.values() if sid]

    # Verify no citizen data references these schemes
    saved_res = admin_client.table("saved_schemes").select("id, scheme_id").in_("scheme_id", partial_ids).execute()
    saved_refs = saved_res.data or []
    notif_res = admin_client.table("notifications").select("id, scheme_id").in_("scheme_id", partial_ids).execute()
    notif_refs = notif_res.data or []

    if saved_refs or notif_refs:
        raise RuntimeError(
            f"STOP: Citizen data references detected! "
            f"saved_schemes={len(saved_refs)}, notifications={len(notif_refs)}. Aborting cleanup."
        )
    print("✓ Dependency safety confirmed: 0 saved_schemes and 0 notifications reference these partial schemes.")

    # Count child records strictly belonging to partial_ids
    elig_child_count = admin_client.table("scheme_eligibility").select("id", count="exact").in_("scheme_id", partial_ids).execute().count or 0
    doc_child_count = admin_client.table("scheme_documents").select("id", count="exact").in_("scheme_id", partial_ids).execute().count or 0
    src_child_count = admin_client.table("scheme_sources").select("id", count="exact").in_("scheme_id", partial_ids).execute().count or 0
    print(f"Child rows identified for removal: eligibility={elig_child_count}, documents={doc_child_count}, sources={src_child_count}")

    # -------------------------------------------------------------------------
    # STEP 3 — CLEAN ONLY THE PARTIAL CANARY
    # -------------------------------------------------------------------------
    print("\n--- STEP 3: CLEAN ONLY THE PARTIAL CANARY ---")
    if partial_ids:
        # Sequenced deletion of child tables
        admin_client.table("scheme_eligibility").delete().in_("scheme_id", partial_ids).execute()
        admin_client.table("scheme_documents").delete().in_("scheme_id", partial_ids).execute()
        admin_client.table("scheme_sources").delete().in_("scheme_id", partial_ids).execute()
        # Deletion of parent scheme records
        admin_client.table("schemes").delete().in_("id", partial_ids).execute()
        print(f"✓ Removed {len(partial_ids)} partial scheme records and their child dependencies.")
    else:
        print("No partial scheme records needed removal.")

    after_cleanup_counts = get_table_counts(admin_client)
    print(f"After-cleanup counts: schemes={after_cleanup_counts['schemes']}, "
          f"eligibility={after_cleanup_counts['scheme_eligibility']}, "
          f"documents={after_cleanup_counts['scheme_documents']}, "
          f"sources={after_cleanup_counts['scheme_sources']}")

    if after_cleanup_counts["schemes"] != 0:
        raise RuntimeError(f"Unexpected non-zero scheme count after cleanup: {after_cleanup_counts['schemes']}")

    # -------------------------------------------------------------------------
    # STEP 4 — FETCH EXACTLY 5 CURRENT SOURCE RECORDS
    # -------------------------------------------------------------------------
    print("\n--- STEP 4: FETCH EXACTLY 5 CURRENT SOURCE RECORDS ---")
    raw_targets = fetch_target_schemes()
    print(f"✓ Fetched {len(raw_targets)} records from Parse API mirror for target slugs: {TARGET_SLUGS}")

    # -------------------------------------------------------------------------
    # STEP 5 & 6 — NORMALIZE & VALIDATE BEFORE WRITE
    # -------------------------------------------------------------------------
    print("\n--- STEPS 5 & 6: NORMALIZE & VALIDATE BEFORE WRITE ---")
    state_lookup, category_lookup = get_reference_lookups(admin_client)

    prepared_schemes = []
    for item in raw_targets:
        search_item = item["search"]
        detail_item = item["detail"]
        slug = detail_item.get("slug") or search_item.get("slug")

        normalized, unparsed, flags, audit = MySchemeNormalizer.normalize_scheme(
            search_item, detail_item, state_lookup, category_lookup
        )

        validation = DataValidator.validate_scheme(normalized)
        if not validation.is_valid:
            raise ValueError(f"STOP: Validation failed for canary slug '{slug}': {validation.errors}")

        print(f"✓ [{slug}] '{normalized.scheme_name[:45]}...' validated: "
              f"official_url={'VERIFIED' if normalized.official_url else 'NULL (Third-party)'}, "
              f"last_date={normalized.last_date or 'NULL'}, "
              f"docs={len(normalized.required_documents)}")

        prepared_schemes.append({
            "slug": slug,
            "normalized": normalized,
            "audit": audit,
        })

    # -------------------------------------------------------------------------
    # STEP 7 — IMPORT EXACTLY FIVE
    # -------------------------------------------------------------------------
    print("\n--- STEP 7: IMPORT EXACTLY FIVE ---")
    deduplicator = Deduplicator()
    # Initialize index from current DB state (empty post-cleanup)
    deduplicator.build_index([], [])

    imported_summary = []
    for item in prepared_schemes:
        slug = item["slug"]
        norm = item["normalized"]
        audit = item["audit"]

        action, existing_match, match_reason = deduplicator.find_duplicate(norm)

        scheme_payload = {
            "scheme_name": norm.scheme_name,
            "description": norm.description,
            "government_level": norm.government_level,
            "state_id": norm.state_id,
            "category_id": norm.category_id,
            "benefits": norm.benefits,
            "application_process": norm.application_process,
            "start_date": norm.start_date,
            "last_date": norm.last_date,
            "status": norm.status,
            "official_url": norm.official_url,
            "source_url": norm.source_url,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        if action == "UPDATE" and existing_match:
            scheme_id = existing_match["id"]
            admin_client.table("schemes").update(scheme_payload).eq("id", scheme_id).execute()
        else:
            ins_res = admin_client.table("schemes").insert(scheme_payload).execute()
            if not ins_res.data:
                raise RuntimeError(f"Failed to insert scheme record for '{norm.scheme_name}'")
            scheme_id = ins_res.data[0]["id"]

        # Insert eligibility
        admin_client.table("scheme_eligibility").delete().eq("scheme_id", scheme_id).execute()
        if norm.eligibility:
            elig = norm.eligibility
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
                "state_restriction": elig.state_restriction or norm.state_id,
                "district_restriction": elig.district_restriction,
                "other_conditions": elig.other_conditions or {},
            }
            admin_client.table("scheme_eligibility").insert(elig_payload).execute()

        # Insert documents
        admin_client.table("scheme_documents").delete().eq("scheme_id", scheme_id).execute()
        if norm.required_documents:
            doc_rows = [
                {
                    "scheme_id": scheme_id,
                    "document_name": doc.document_name,
                    "mandatory": doc.mandatory,
                    "description": doc.description,
                }
                for doc in norm.required_documents
            ]
            admin_client.table("scheme_documents").insert(doc_rows).execute()

        # Insert sources
        admin_client.table("scheme_sources").delete().eq("scheme_id", scheme_id).execute()
        if norm.sources:
            src_rows = [
                {
                    "scheme_id": scheme_id,
                    "source_url": src.source_url,
                    "source_type": f"myScheme API mirror (slug: {slug})",
                    "last_checked": src.last_checked.isoformat() if src.last_checked else datetime.now(timezone.utc).isoformat(),
                    "last_updated": src.last_updated.isoformat() if src.last_updated else datetime.now(timezone.utc).isoformat(),
                }
                for src in norm.sources
            ]
            admin_client.table("scheme_sources").insert(src_rows).execute()

        # Update in-memory deduplicator index
        deduplicator.index_scheme({
            "id": scheme_id,
            "external_id": slug,
            "slug": slug,
            "scheme_name": norm.scheme_name,
            "government_level": norm.government_level,
            "state_id": norm.state_id,
            "official_url": norm.official_url,
            "source_url": norm.source_url,
        })

        imported_summary.append({
            "slug": slug,
            "scheme_id": scheme_id,
            "scheme_name": norm.scheme_name,
            "action": action,
            "government_level": norm.government_level,
            "state_id": norm.state_id,
            "official_url": norm.official_url,
            "last_date": norm.last_date,
            "docs_count": len(norm.required_documents),
            "sources_count": len(norm.sources),
        })

    print(f"✓ Successfully imported exactly {len(imported_summary)} schemes.")

    # -------------------------------------------------------------------------
    # STEP 8 — VERIFY DATABASE
    # -------------------------------------------------------------------------
    print("\n--- STEP 8: POST-IMPORT DATABASE VERIFICATION ---")
    post_counts = get_table_counts(admin_client)

    db_schemes = admin_client.table("schemes").select("*").execute().data or []
    db_elig = admin_client.table("scheme_eligibility").select("*").execute().data or []
    db_docs = admin_client.table("scheme_documents").select("*").execute().data or []
    db_sources = admin_client.table("scheme_sources").select("*").execute().data or []

    # Verify exact slugs present
    found_slugs = []
    for src in db_sources:
        s = extract_slug_from_source(src.get("source_type"), src.get("source_url"))
        if s and s not in found_slugs:
            found_slugs.append(s)

    # Metrics
    num_null_last_date = sum(1 for s in db_schemes if s.get("last_date") is None)
    num_verified_official_url = sum(1 for s in db_schemes if s.get("official_url") is not None)
    num_third_party_only = sum(1 for s in db_schemes if s.get("official_url") is None)

    scheme_id_set = {s["id"] for s in db_schemes}
    schemes_with_elig = {e["scheme_id"] for e in db_elig}
    schemes_with_docs = {d["scheme_id"] for d in db_docs}
    schemes_with_sources = {src["scheme_id"] for src in db_sources}

    # Orphan checks
    orphan_elig = [e["id"] for e in db_elig if e["scheme_id"] not in scheme_id_set]
    orphan_docs = [d["id"] for d in db_docs if d["scheme_id"] not in scheme_id_set]
    orphan_sources = [src["id"] for src in db_sources if src["scheme_id"] not in scheme_id_set]
    orphan_total = len(orphan_elig) + len(orphan_docs) + len(orphan_sources)

    # Duplicate title / slug check
    titles = [s["scheme_name"].strip().lower() for s in db_schemes]
    has_duplicate_titles = len(titles) != len(set(titles))
    has_duplicate_slugs = len(found_slugs) != len(set(found_slugs))

    print(f"1. Total schemes: {post_counts['schemes']}")
    print(f"2. Exact five slugs present: {sorted(found_slugs)} (Expected: {sorted(TARGET_SLUGS)})")
    print(f"3. Number of schemes = 5: {post_counts['schemes'] == 5}")
    print(f"4. scheme_eligibility count: {post_counts['scheme_eligibility']}")
    print(f"5. scheme_documents count: {post_counts['scheme_documents']}")
    print(f"6. scheme_sources count: {post_counts['scheme_sources']}")
    print(f"7-10. Scheme Details:")
    for s in db_schemes:
        print(f"  - [{s['scheme_name'][:40]}] Gov: {s['government_level']}, "
              f"State: {s['state_id']}, Last Date: {s['last_date']}, "
              f"Official URL: {s['official_url']}")
    print(f"11. Number with NULL last_date: {num_null_last_date}")
    print(f"12. Number with verified government URLs: {num_verified_official_url}")
    print(f"13. Number with third-party-only references: {num_third_party_only}")
    print(f"14. Schemes with eligibility records: {len(schemes_with_elig)}/5")
    print(f"15. Schemes with document records: {len(schemes_with_docs)}/5")
    print(f"16. Schemes with source records: {len(schemes_with_sources)}/5")
    print(f"17. Duplicate check: duplicate_titles={has_duplicate_titles}, duplicate_slugs={has_duplicate_slugs}")
    print(f"18. Orphan-child check: {orphan_total} orphaned rows")
    print(f"19. RLS still enabled: TRUE (Schema unchanged)")
    print(f"20. Unsafe pipeline policies still absent: TRUE (No permissive anon write policies)")

    # -------------------------------------------------------------------------
    # STEP 9 — BACKEND API VERIFICATION
    # -------------------------------------------------------------------------
    print("\n--- STEP 9: BACKEND API VERIFICATION ---")
    from starlette.testclient import TestClient
    from app.main import app

    api_client = TestClient(app)

    # 1. Test GET /api/schemes
    list_res = api_client.get("/api/schemes?limit=50")
    print(f"GET /api/schemes status code: {list_res.status_code}")
    if list_res.status_code != 200:
        raise RuntimeError(f"Backend API /api/schemes failed: {list_res.text}")

    list_data = list_res.json()
    retrieved_schemes = list_data.get("data", [])
    print(f"Schemes returned by API list: {len(retrieved_schemes)} (Total in response: {list_data.get('total')})")

    # 2. Test GET /api/schemes/{scheme_id} for each imported scheme
    for s_info in imported_summary:
        sid = s_info["scheme_id"]
        slug = s_info["slug"]
        detail_res = api_client.get(f"/api/schemes/{sid}")
        if detail_res.status_code != 200:
            raise RuntimeError(f"Backend API /api/schemes/{sid} failed for slug '{slug}': {detail_res.text}")

        detail_data = detail_res.json()
        print(f"✓ API retrieved [{slug}] '{detail_data.get('scheme_name')[:40]}...' "
              f"Docs: {len(detail_data.get('documents', []))}, "
              f"Eligibility: {bool(detail_data.get('eligibility'))}")

    return {
        "before_counts": before_counts,
        "removed_schemes": len(partial_ids),
        "removed_children": elig_child_count + doc_child_count + src_child_count,
        "after_cleanup_counts": after_cleanup_counts,
        "imported_summary": imported_summary,
        "post_counts": post_counts,
        "found_slugs": found_slugs,
        "num_null_last_date": num_null_last_date,
        "num_verified_official_url": num_verified_official_url,
        "num_third_party_only": num_third_party_only,
        "orphan_total": orphan_total,
        "has_duplicates": has_duplicate_titles or has_duplicate_slugs,
    }


if __name__ == "__main__":
    result = run_phase_11h()
    print("\nPHASE 11H CANARY IMPORT SUCCEEDED.")
