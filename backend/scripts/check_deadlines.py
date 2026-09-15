"""
CLI Deadline Monitoring Script
------------------------------
Executes the deadline monitoring service to evaluate saved schemes against
active application deadlines and deterministic citizen eligibility.

Usage:
  python backend/scripts/check_deadlines.py
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path to allow imports when run from any directory
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.notification_service import NotificationService


def run_deadline_check():
    """Run deadline monitoring evaluation and print factual operational metrics."""
    service = NotificationService()
    try:
        result = service.check_saved_scheme_deadlines()
        print("=== SchemeSetu Deadline Monitoring Run ===")
        print(f"Users checked: {result.users_checked}")
        print(f"Saved schemes checked: {result.saved_schemes_checked}")
        print(f"Eligible saved schemes: {result.eligible_saved_schemes}")
        print(f"Notifications created: {result.notifications_created}")
        print(f"Notifications skipped: {result.notifications_skipped}")
        print("==========================================")
        return 0
    except Exception as exc:
        print(f"Error executing deadline monitor: {str(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run_deadline_check())
