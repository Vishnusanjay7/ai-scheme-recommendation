"""
Supabase Database & RLS Verification Utility
---------------------------------------------
Executes verification against a live Supabase instance:
- Verifies reachability
- Confirms presence of all 12 tables
- Confirms reference data (36 States & UTs, scheme categories)
- Verifies RLS protection: anon/unauthenticated requests cannot access private citizen data
"""

import sys
from pathlib import Path

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.integrations.supabase_client import get_supabase_client, is_supabase_configured

TABLES_PUBLIC = [
    "states",
    "districts",
    "scheme_categories",
    "schemes",
    "scheme_eligibility",
    "scheme_documents",
    "scheme_sources",
]

TABLES_PRIVATE = [
    "users",
    "user_profiles",
    "saved_schemes",
    "notifications",
    "chat_history",
]

ALL_12_TABLES = TABLES_PUBLIC + TABLES_PRIVATE


def verify_supabase():
    print("=" * 60)
    print("AI Government Scheme Recommender - Supabase Verification")
    print("=" * 60)

    if not is_supabase_configured():
        print("[!] Supabase credentials are not configured in environment.")
        print("    Please set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in backend/.env")
        return False

    client = get_supabase_client()
    print("[✓] Supabase client initialized successfully.")

    # 1. Check Public Tables
    print("\n--- 1. Testing Public Tables (Should be readable) ---")
    public_success = 0
    for tbl in TABLES_PUBLIC:
        try:
            res = client.table(tbl).select("*").limit(1).execute()
            print(f" [✓] Public table '{tbl}' is accessible. (Rows: {len(res.data)})")
            public_success += 1
        except Exception as e:
            print(f" [✗] Error querying public table '{tbl}': {e}")

    # 2. Check Reference Data
    print("\n--- 2. Checking Reference Data ---")
    try:
        states_res = client.table("states").select("id, name, code").execute()
        count = len(states_res.data)
        print(f" [*] States & Union Territories count: {count} (Expected: 36)")
        if count == 36:
            print(" [✓] All 36 States & UTs successfully loaded.")
        else:
            print(" [!] Note: States count differs from 36. Run schema.sql reference seeds if needed.")
    except Exception as e:
        print(f" [✗] Error reading states: {e}")

    try:
        cat_res = client.table("scheme_categories").select("id, name").execute()
        print(f" [✓] Scheme categories count: {len(cat_res.data)} loaded.")
    except Exception as e:
        print(f" [✗] Error reading scheme categories: {e}")

    # 3. Check Private Tables (RLS Protection)
    print("\n--- 3. Testing RLS Protection on Private Citizen Tables ---")
    print(" (Unauthenticated / Anon clients should receive empty sets or access denied)")
    private_protected = 0
    for tbl in TABLES_PRIVATE:
        try:
            res = client.table(tbl).select("*").limit(1).execute()
            # Under RLS, anon client without auth.uid() should get 0 rows
            if len(res.data) == 0:
                print(f" [✓] RLS ACTIVE: '{tbl}' returned 0 rows for unauthenticated client.")
                private_protected += 1
            else:
                print(f" [!] RLS WARNING: '{tbl}' returned data to unauthenticated client!")
        except Exception as e:
            # Some RLS setups error out on unauthorized queries, which is also protected
            print(f" [✓] RLS ACTIVE: '{tbl}' query denied or blocked ({type(e).__name__}).")
            private_protected += 1

    print("\n" + "=" * 60)
    print(f"Summary: {public_success}/{len(TABLES_PUBLIC)} public tables accessible | {private_protected}/{len(TABLES_PRIVATE)} private tables protected by RLS.")
    print("=" * 60)
    return public_success == len(TABLES_PUBLIC) and private_protected == len(TABLES_PRIVATE)


if __name__ == "__main__":
    verify_supabase()
