import glob
import os
import re
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

sys.stdout.reconfigure(encoding="utf-8")

from app.integrations.supabase_client import get_supabase_admin_client

def inspect_state_mapping():
    print("=" * 80)
    print("INSPECTING STATE MAPPING & HARD-CODED REFERENCES")
    print("=" * 80)

    admin = get_supabase_admin_client()

    # 1. Fetch states table
    states = admin.table("states").select("*").execute().data or []
    print(f"Total states in DB: {len(states)}")
    tn_states = [s for s in states if s.get("code") == "TN" or "tamil" in s.get("name", "").lower()]
    for s in tn_states:
        print(f"  Tamil Nadu record: id={s['id']}, code={s['code']}, name='{s['name']}'")

    actual_tn_id = tn_states[0]["id"] if tn_states else None

    # 2. Join schemes.state_id -> states.id
    schemes = admin.table("schemes").select("id, scheme_name, government_level, state_id").execute().data or []
    state_lookup = {s["id"]: s for s in states}

    mismatched_schemes = []
    state_schemes_count = 0
    central_schemes_count = 0

    for s in schemes:
        gov_level = s.get("government_level")
        sid = s.get("state_id")

        if gov_level == "STATE":
            state_schemes_count += 1
            if sid is None:
                mismatched_schemes.append((s, "Missing state_id on STATE scheme"))
            elif sid not in state_lookup:
                mismatched_schemes.append((s, f"Invalid state_id {sid} not in states table"))
            elif sid != actual_tn_id:
                mismatched_schemes.append((s, f"state_id {sid} ({state_lookup[sid]['name']}) does not match Tamil Nadu ({actual_tn_id})"))
        elif gov_level == "CENTRAL":
            central_schemes_count += 1
            if sid is not None:
                mismatched_schemes.append((s, f"CENTRAL scheme has non-null state_id {sid}"))

    print(f"\nScheme breakdown:")
    print(f"  Total schemes: {len(schemes)}")
    print(f"  STATE schemes: {state_schemes_count}")
    print(f"  CENTRAL schemes: {central_schemes_count}")
    print(f"  Mismatched / Invalid state schemes: {len(mismatched_schemes)}")
    if mismatched_schemes:
        for s, reason in mismatched_schemes:
            print(f"    - {s['scheme_name']}: {reason}")
    else:
        print(f"  [✓] All {state_schemes_count} STATE schemes resolve to Tamil Nadu (id={actual_tn_id}) via states.id join!")

    # 3. Check for hard-coded state IDs across codebase
    print("\n--- Searching for hard-coded state ID patterns in codebase ---")
    patterns = [
        re.compile(r"\bstate_id\s*==?\s*\d+\b"),
        re.compile(r"\bstate_restriction\s*==?\s*\d+\b"),
        re.compile(r"[\"']state_id[\"']\s*:\s*\d+"),
        re.compile(r"[\"']state_restriction[\"']\s*:\s*\d+"),
    ]

    found_matches = []
    for ext in ["py", "jsx", "js", "sql"]:
        for p in root_dir.glob(f"**/*.{ext}"):
            p_str = str(p)
            if "node_modules" in p_str or ".venv" in p_str or "dist" in p_str or ".git" in p_str or "audit_" in p_str or "inspect_state" in p_str:
                continue
            try:
                with open(p, "r", encoding="utf-8") as fp:
                    for i, line in enumerate(fp, 1):
                        for pat in patterns:
                            if pat.search(line):
                                found_matches.append((p.relative_to(root_dir), i, line.strip()))
            except Exception:
                pass

    print(f"Found {len(found_matches)} matches in application code/tests:")
    for fpath, lno, ltext in found_matches:
        print(f"  {fpath}:{lno}: {ltext}")

    return {
        "actual_tn_id": actual_tn_id,
        "state_schemes_count": state_schemes_count,
        "mismatched_schemes": mismatched_schemes,
        "found_matches": found_matches,
    }

if __name__ == "__main__":
    inspect_state_mapping()
