#!/usr/bin/env python3
"""
CLI Script: Collect Government Schemes
--------------------------------------
Executes the Phase 2 data acquisition pipeline from official government sources
or validated dataset files.

Usage:
  python backend/scripts/collect_schemes.py --dry-run
  python backend/scripts/collect_schemes.py --file path/to/official_dataset.json
  python backend/scripts/collect_schemes.py --source "myScheme National Portal" --dry-run
"""

import argparse
import json
import os
from pathlib import Path
import sys

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.data_pipeline.scheme_collector import SchemeCollector
from app.data_pipeline.source_manager import SourceManager


def main():
    parser = argparse.ArgumentParser(
        description="Acquire and ingest official government schemes into the database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Run normalization, validation, and deduplication without modifying the database (default: True).",
    )
    parser.add_argument(
        "--live",
        dest="dry_run",
        action="store_false",
        help="Persist changes to Supabase (requires SUPABASE_SERVICE_ROLE_KEY).",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to official government dataset file (JSON).",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Specific source adapter name to collect from.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum records to fetch per source.",
    )

    args = parser.parse_args()

    print("=" * 65)
    print("AI Government Scheme Recommender - Scheme Collector Pipeline")
    print(f"Mode: {'DRY RUN (No DB Writes)' if args.dry_run else 'LIVE PERSISTENCE'}")
    print("=" * 65)

    collector = SchemeCollector(dry_run=args.dry_run)
    sources = [args.source] if args.source else None

    summary = collector.collect_and_update_schemes(
        sources=sources,
        dataset_file=args.file,
        limit_per_source=args.limit,
    )

    print("\n--- Execution Summary ---")
    print(json.dumps(summary, indent=2))
    print("=" * 65)

    # Return exit code based on whether critical errors occurred
    if summary["errors"] and summary["records_valid"] == 0 and summary["records_received"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
