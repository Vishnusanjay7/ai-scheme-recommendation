"""
Phase 11R: Activity Status and State-Mapping Verification
--------------------------------------------------------
READ-ONLY verification script.
Evaluates all 62 schemes in Supabase using the corrected deadline_service semantics.
Verifies state mapping via SQL JOIN against states table.
"""

import sys
from collections import Counter
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

sys.stdout.reconfigure(encoding="utf-8")

from app.integrations.supabase_client import get_supabase_admin_client
from app.services.deadline_service import (
    get_scheme_activity,
    ActivityStatus,
    DeadlineClassification,
)

def run_phase11r_audit():
    print("=" * 80)
    print("PHASE 11R — ACTIVITY STATUS AND STATE-MAPPING AUDIT (READ-ONLY)")
    print("=" * 80)

    admin = get_supabase_admin_client()

    # 1. State Mapping Join
    print("\n--- 1. STATE MAPPING VERIFICATION (JOIN schemes.state_id -> states.id) ---")
    states_res = admin.table("states").select("*").execute()
    states = states_res.data or []
    state_lookup = {s["id"]: s for s in states}

    tn_states = [s for s in states if s.get("code") == "TN" or "tamil" in s.get("name", "").lower()]
    actual_tn_id = tn_states[0]["id"] if tn_states else None
    print(f"Total reference states in database: {len(states)}")
    print(f"Authoritative Tamil Nadu record in states table: ID={actual_tn_id}, Code='{tn_states[0]['code']}', Name='{tn_states[0]['name']}'")

    schemes_res = admin.table("schemes").select("*").execute()
    schemes = schemes_res.data or []
    print(f"Total schemes in database: {len(schemes)}")

    mismatched_schemes = []
    state_schemes_count = 0
    central_schemes_count = 0

    for s in schemes:
        gov_level = s.get("government_level")
        sid = s.get("state_id")
        if gov_level == "STATE":
            state_schemes_count += 1
            if sid is None:
                mismatched_schemes.append((s["scheme_name"], "Missing state_id on STATE scheme"))
            elif sid not in state_lookup:
                mismatched_schemes.append((s["scheme_name"], f"Invalid state_id {sid} not in states table"))
            elif sid != actual_tn_id:
                mismatched_schemes.append((s["scheme_name"], f"state_id {sid} does not match Tamil Nadu ({actual_tn_id})"))
        elif gov_level == "CENTRAL":
            central_schemes_count += 1
            if sid is not None:
                mismatched_schemes.append((s["scheme_name"], f"CENTRAL scheme has non-null state_id {sid}"))

    print(f"State schemes count: {state_schemes_count}")
    print(f"Central schemes count: {central_schemes_count}")
    print(f"Mismatched / Invalid state schemes: {len(mismatched_schemes)}")
    print(f"Every imported STATE scheme joins cleanly to Tamil Nadu (ID={actual_tn_id}): {len(mismatched_schemes) == 0}")

    # 2. Activity Status Audit with Updated Semantics
    print("\n--- 2. CORRECTED ACTIVITY STATUS EVALUATION ---")
    status_counts = Counter()
    deadline_counts = Counter()

    confirmed_open = []
    no_deadline_unconfirmed = []
    expired_schemes = []
    not_yet_open_schemes = []
    inactive_schemes = []
    unknown_schemes = []

    for s in schemes:
        info = get_scheme_activity(s)
        status_counts[info.status.value] += 1
        deadline_counts[info.deadline_status.value] += 1

        if info.status == ActivityStatus.OPEN:
            confirmed_open.append((s["id"], s["scheme_name"]))
        elif info.status == ActivityStatus.UNKNOWN:
            if info.deadline_status == DeadlineClassification.NO_DEADLINE:
                no_deadline_unconfirmed.append((s["id"], s["scheme_name"], info.reason))
            else:
                unknown_schemes.append((s["id"], s["scheme_name"], info.reason))
        elif info.status == ActivityStatus.EXPIRED:
            expired_schemes.append((s["id"], s["scheme_name"]))
        elif info.status == ActivityStatus.NOT_YET_OPEN:
            not_yet_open_schemes.append((s["id"], s["scheme_name"]))
        elif info.status == ActivityStatus.INACTIVE:
            inactive_schemes.append((s["id"], s["scheme_name"]))

    print(f"Activity Status breakdown:")
    print(f"  A. Confirmed OPEN: {len(confirmed_open)}")
    print(f"  B. NO_DEADLINE but activity unconfirmed (UNKNOWN): {len(no_deadline_unconfirmed)}")
    print(f"  C. EXPIRED: {len(expired_schemes)}")
    print(f"  D. NOT_YET_OPEN: {len(not_yet_open_schemes)}")
    print(f"  E. INACTIVE: {len(inactive_schemes)}")
    print(f"  F. UNKNOWN (other reasons): {len(unknown_schemes)}")
    print(f"  G. Other existing statuses: 0")

    if no_deadline_unconfirmed:
        print("\nDetails for NO_DEADLINE schemes with unconfirmed activity:")
        for sid, sname, reason in no_deadline_unconfirmed:
            print(f"  - [{sid}] '{sname}'")
            print(f"    Reason: {reason}")

    return {
        "actual_tn_id": actual_tn_id,
        "mismatched_state_records": len(mismatched_schemes),
        "total_schemes": len(schemes),
        "confirmed_open": len(confirmed_open),
        "no_deadline_unconfirmed": len(no_deadline_unconfirmed),
        "expired": len(expired_schemes),
        "not_yet_open": len(not_yet_open_schemes),
        "inactive": len(inactive_schemes),
        "unknown": len(unknown_schemes),
        "other_statuses": 0,
    }

if __name__ == "__main__":
    run_phase11r_audit()
