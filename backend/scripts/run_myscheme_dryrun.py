"""
Execution Script: myScheme 5-Scheme Dry-Run Import (Audited)
------------------------------------------------------------
Safely normalizes, validates, and audits the 5 Tamil Nadu schemes
fetched via the Parse myScheme API mirror with zero database writes.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend path is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.data_pipeline.data_validator import DataValidator
from app.data_pipeline.importers.myscheme_normalizer import MySchemeNormalizer
from app.integrations.supabase_client import get_supabase_client, is_supabase_configured
import httpx


def get_lookups():
    """Retrieve reference lookups from Supabase or fallback to verified master maps."""
    state_lookup = {}
    category_lookup = {}

    if is_supabase_configured():
        client = get_supabase_client()
        s_res = client.table("states").select("id, name, code").execute()
        for s in s_res.data or []:
            state_lookup[s["name"].strip().lower()] = (s["id"], s["name"])
            state_lookup[s["code"].strip().lower()] = (s["id"], s["name"])

        c_res = client.table("scheme_categories").select("id, name").execute()
        for c in c_res.data or []:
            category_lookup[c["name"].strip().lower()] = (c["id"], c["name"])
    else:
        state_lookup["tamil nadu"] = (23, "Tamil Nadu")
        state_lookup["tn"] = (23, "Tamil Nadu")

    return state_lookup, category_lookup


def fetch_5_schemes():
    """Fetch the 5 Tamil Nadu schemes live from Parse API mirror."""
    env_path = backend_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    key = os.getenv("PARSE_API_KEY")
    if not key:
        raise ValueError("PARSE_API_KEY is not set in backend/.env")

    client = httpx.Client(headers={"X-API-Key": key.strip()}, timeout=60.0)
    scraper_id = "00040831-f035-4cb1-adbc-67dad5171ce1"
    search_url = f"https://api.parse.bot/scraper/{scraper_id}/search_schemes"
    detail_url = f"https://api.parse.bot/scraper/{scraper_id}/get_scheme_details"

    search_res = client.get(search_url, params={"from": 0, "size": 5, "state": "Tamil Nadu"}).json()
    schemes = search_res.get("data", {}).get("schemes", [])

    results = []
    for s in schemes:
        d_res = client.get(detail_url, params={"slug": s["slug"]}).json()
        detail = d_res.get("data", {})
        results.append({"search": s, "detail": detail})

    return results


def main():
    data = fetch_5_schemes()
    state_lookup, category_lookup = get_lookups()

    schemes_preview = []
    readiness = {
        "schemes_fetched": len(data),
        "details_fetched_successfully": 0,
        "schemes_with_verified_official_urls": 0,
        "schemes_with_third_party_only_references": 0,
        "schemes_with_close_dates": 0,
        "schemes_with_no_close_date": 0,
        "schemes_with_explicit_ongoing_evidence": 0,
        "schemes_with_structured_eligibility": 0,
        "schemes_with_eligibility_requiring_verification": 0,
        "schemes_with_unknown_doc_mandatory_status": 0,
        "schemes_with_document_lists": 0,
        "schemes_with_missing_important_fields": 0,
        "schemes_safe_to_import": 0,
        "schemes_requiring_manual_verification": 0,
    }

    for idx, item in enumerate(data):
        search_item = item["search"]
        detail_item = item["detail"]

        if detail_item:
            readiness["details_fetched_successfully"] += 1

        normalized, unparsed_eligibility, verification_flags, audit = MySchemeNormalizer.normalize_scheme(
            search_item, detail_item, state_lookup, category_lookup
        )

        validation = DataValidator.validate_scheme(normalized)

        # Audit metrics
        if audit["has_verified_official_url"]:
            readiness["schemes_with_verified_official_urls"] += 1
        elif audit["third_party_only"]:
            readiness["schemes_with_third_party_only_references"] += 1

        if audit["has_close_date"]:
            readiness["schemes_with_close_dates"] += 1
        else:
            readiness["schemes_with_no_close_date"] += 1

        if audit["has_ongoing_evidence"]:
            readiness["schemes_with_explicit_ongoing_evidence"] += 1

        if audit["unknown_mandatory_doc_count"] > 0:
            readiness["schemes_with_unknown_doc_mandatory_status"] += 1

        elig = normalized.eligibility
        if elig and (elig.min_age or elig.max_age or elig.max_income or elig.gender or elig.education or elig.occupation):
            readiness["schemes_with_structured_eligibility"] += 1

        if verification_flags or unparsed_eligibility:
            readiness["schemes_with_eligibility_requiring_verification"] += 1

        if normalized.required_documents:
            readiness["schemes_with_document_lists"] += 1

        all_warnings = list(validation.warnings) + audit["validation_warnings"]

        if not validation.is_valid:
            readiness["schemes_with_missing_important_fields"] += 1
            readiness["schemes_requiring_manual_verification"] += 1
        else:
            readiness["schemes_safe_to_import"] += 1

        schemes_preview.append({
            "index": idx + 1,
            "slug": normalized.external_id,
            "scheme_name": normalized.scheme_name,
            "level": normalized.government_level,
            "beneficiary_state": normalized.state_name,
            "state_id": normalized.state_id,
            "category": normalized.category_name,
            "category_id": normalized.category_id,
            "description": (normalized.description[:180] + "...") if normalized.description and len(normalized.description) > 180 else normalized.description,
            "benefits": (normalized.benefits[:180] + "...") if normalized.benefits and len(normalized.benefits) > 180 else normalized.benefits,
            "start_date": normalized.start_date,
            "close_date": normalized.last_date,
            "official_url": normalized.official_url,
            "has_verified_official_url": audit["has_verified_official_url"],
            "source_url": normalized.source_url,
            "third_party_urls": audit["third_party_urls"],
            "has_ongoing_evidence": audit["has_ongoing_evidence"],
            "ongoing_evidence_text": audit["ongoing_evidence_text"],
            "extracted_eligibility": {
                "min_age": elig.min_age if elig else None,
                "max_age": elig.max_age if elig else None,
                "max_income": elig.max_income if elig else None,
                "gender": elig.gender if elig else None,
                "occupation": elig.occupation if elig else None,
                "education": elig.education if elig else None,
                "category": elig.category if elig else None,
                "disability": elig.disability_required if elig else False,
            },
            "unparsed_conditions": unparsed_eligibility,
            "verification_flags": verification_flags,
            "special_branches": elig.other_conditions.get("special_branches", []) if elig else [],
            "district_income_conditions": elig.other_conditions.get("district_income_conditions", {}) if elig else {},
            "parsed_documents": [
                {
                    "name": doc.document_name,
                    "mandatory": doc.mandatory,
                    "status": "UNKNOWN" if "MANDATORY_STATUS_UNKNOWN" in (doc.description or "") else ("MANDATORY" if doc.mandatory else "OPTIONAL"),
                    "description": doc.description,
                }
                for doc in normalized.required_documents
            ],
            "total_documents": audit["total_docs"],
            "unknown_mandatory_doc_count": audit["unknown_mandatory_doc_count"],
            "explicit_mandatory_doc_count": audit["explicit_mandatory_doc_count"],
            "application_process": (normalized.application_process[:180] + "...") if normalized.application_process and len(normalized.application_process) > 180 else normalized.application_process,
            "validation_is_valid": validation.is_valid,
            "validation_errors": validation.errors,
            "validation_warnings": all_warnings,
            "provenance": audit["provenance"],
        })

    output_obj = {
        "readiness_summary": readiness,
        "schemes": schemes_preview,
    }

    print("DRY_RUN_COMPLETE")
    print(json.dumps(output_obj, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
