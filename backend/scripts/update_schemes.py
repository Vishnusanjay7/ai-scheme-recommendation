#!/usr/bin/env python3
"""
CLI Script: Update Government Schemes
-------------------------------------
Executes periodic maintenance and synchronization of existing schemes
from official government sources (checking deadlines, status transitions,
and ministry updates).

Designed to be invoked periodically by an external scheduler/cron system.

Usage:
  python backend/scripts/update_schemes.py --dry-run
  python backend/scripts/update_schemes.py --live
"""

import argparse
import json
from pathlib import Path
import sys

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.data_pipeline.scheme_collector import SchemeCollector


def main():
    parser = argparse.ArgumentParser(
        description="Update existing government scheme records and check deadline transitions."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate updates without writing to database (default: True).",
    )
    parser.add_argument(
        "--live",
        dest="dry_run",
        action="store_false",
        help="Commit updates to Supabase (requires SUPABASE_SERVICE_ROLE_KEY).",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to refreshed government dataset file (JSON).",
    )

    args = parser.parse_args()

    print("=" * 65)
    print("AI Government Scheme Recommender - Periodic Scheme Sync")
    print(f"Mode: {'DRY RUN (No DB Writes)' if args.dry_run else 'LIVE UPDATE'}")
    print("=" * 65)

    collector = SchemeCollector(dry_run=args.dry_run)
    summary = collector.collect_and_update_schemes(dataset_file=args.file)

    print("\n--- Synchronization Summary ---")
    print(json.dumps(summary, indent=2))
    print("=" * 65)


if __name__ == "__main__":
    main()
