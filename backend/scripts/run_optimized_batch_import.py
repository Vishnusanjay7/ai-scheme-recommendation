"""
Optimized Batch Ingestion & Quota Planning Script
--------------------------------------------------
Usage:
    python backend/scripts/run_optimized_batch_import.py [--dry-run] [--target 25]

Rules:
- Strictly minimizes Parse API credits:
    * search_schemes: 1 credit per call (queries with size=100)
    * get_scheme_details: 2 credits per call
- Utilizes local checkpoint/cache:
    * 0 search credits if catalog already cached
    * 0 detail credits if detail already cached
- Skips already imported schemes (30 existing) and canary slugs
- Safe dry-run mode: does NOT call live Parse API; does NOT write to database
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.data_pipeline.importers.optimized_myscheme_importer import OptimizedMySchemeImporter
from app.data_pipeline.pipeline_checkpoint import PipelineCacheManager, QuotaEstimator
from app.integrations.supabase_client import (
    get_supabase_admin_client,
    is_supabase_admin_configured,
)


def run_plan_or_import(target_count: int = 25, dry_run: bool = True):
    print("================================================================================")
    print(f"OPTIMIZED MYSCHEME BATCH IMPORTER [{'DRY-RUN' if dry_run else 'LIVE'}]")
    print("================================================================================")

    if not is_supabase_admin_configured():
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured in backend/.env")

    cache_mgr = PipelineCacheManager()
    importer = OptimizedMySchemeImporter(cache_manager=cache_mgr, dry_run=dry_run)

    plan = importer.plan_batch_import(target_count=target_count, total_catalog_size=240)

    print(f"\n1. Current Database State:")
    print(f"   - Confirmed schemes in DB: {plan['current_db_schemes']}")
    print(f"   - Slugs indexed for deduplication: {plan['existing_slugs_count']}")

    print(f"\n2. Local Cache State:")
    print(f"   - Search catalog cached: {cache_mgr.has_catalog()} ({plan['cached_catalog_count']} schemes)")
    print(f"   - Scheme details cached: {plan['cached_details_count']} files")
    print(f"   - Available cached candidates: {plan['available_cached_candidates_count']}")

    print(f"\n3. Quota & Credit Requirement (Target Batch: {target_count} schemes):")
    q = plan["quota_estimate"]
    print(f"   - Total catalog size: {q['total_catalog_schemes']}")
    print(f"   - Already imported in DB: {q['already_imported_count']}")
    print(f"   - Remaining schemes to import: {q['remaining_catalog_schemes']}")
    print(f"   - Target schemes for this batch: {q['schemes_to_import']}")
    print(f"   - Search calls needed (size=100): {q['search_calls_needed']} ({q['search_credits_needed']} credit(s))")
    print(f"   - Detail calls needed (2 credits each): {q['detail_calls_needed']} ({q['detail_credits_needed']} credits)")
    print(f"   - TOTAL MINIMUM CREDITS NEEDED: {q['total_credits_needed']} credits")

    print(f"\n4. Full Execution Plan:")
    print(json.dumps(plan, indent=2))

    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimized Batch Importer")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate without API calls or DB writes")
    parser.add_argument("--target", type=int, default=25, help="Number of new schemes to target")
    args = parser.parse_args()

    run_plan_or_import(target_count=args.target, dry_run=args.dry_run)
