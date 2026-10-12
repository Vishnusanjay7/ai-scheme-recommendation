"""
Harmless Admin Client Connectivity Verification Script
------------------------------------------------------
Verifies:
1. Admin client initializes successfully using SUPABASE_SERVICE_ROLE_KEY.
2. The client is strictly using the service-role credential internally (and NOT the publishable key).
3. A harmless read-only SELECT from public.schemes succeeds.
4. No credential or secret is ever printed or logged.
5. Absolutely NO INSERT, UPDATE, or DELETE statements are executed.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding="utf-8")

from app.integrations.supabase_client import (
    get_supabase_admin_client,
    get_supabase_admin_key,
    get_supabase_publishable_key,
    get_supabase_url,
    is_supabase_admin_configured,
)


def verify_admin_client():
    print("============================================================")
    print("SUPABASE ADMIN CLIENT CONNECTIVITY TEST (READ-ONLY)")
    print("============================================================")

    # 1. Check Configuration
    url = get_supabase_url()
    admin_key = get_supabase_admin_key()
    pub_key = get_supabase_publishable_key()

    print(f"1. Supabase URL configured: {bool(url)}")
    print(f"2. SUPABASE_SERVICE_ROLE_KEY present: {bool(admin_key and admin_key.strip())}")

    if not is_supabase_admin_configured():
        print("\n[BLOCKED] SUPABASE_SERVICE_ROLE_KEY is not configured in backend/.env.")
        print("Please add SUPABASE_SERVICE_ROLE_KEY to backend/.env to complete admin verification.")
        print("Never commit .env or print the service role key.")
        return False

    # Verify admin key is distinct from publishable key
    if pub_key and admin_key and admin_key.strip() == pub_key.strip():
        print("[ERROR] SUPABASE_SERVICE_ROLE_KEY matches SUPABASE_PUBLISHABLE_KEY!")
        print("The service-role key must be the distinct backend secret from Supabase Dashboard > Settings > API.")
        return False

    # 2. Initialize Admin Client
    try:
        client = get_supabase_admin_client()
        print("3. Admin client initialization: SUCCESS")
    except Exception as exc:
        print(f"[ERROR] Admin client initialization failed: {exc}")
        return False

    # 3. Verify Internal Credentials Without Printing
    # Check that PostgREST headers internally contain the Bearer token matching the service-role key
    postgrest_auth = (
        getattr(client.postgrest, "headers", {}).get("Authorization")
        or getattr(client, "headers", {}).get("Authorization")
    )

    is_bearer = bool(postgrest_auth and postgrest_auth.startswith("Bearer "))
    is_matching_admin = bool(postgrest_auth == f"Bearer {admin_key.strip()}")

    print(f"4. Internal Authorization header has Bearer format: {is_bearer}")
    print(f"5. Internal Authorization header matches service-role key: {is_matching_admin}")
    print(f"6. Service-role credential sanitized verification: Key length {len(admin_key.strip())} chars verified (SECRET NOT PRINTED)")

    if not is_matching_admin:
        print("[ERROR] Client internal Authorization header does NOT match service-role key!")
        return False

    # 4. Perform Harmless Read-Only SELECT
    try:
        res = client.table("schemes").select("id, scheme_name").limit(1).execute()
        records_found = len(res.data or [])
        print(f"7. Harmless SELECT from public.schemes: SUCCESS (Returned {records_found} sample record)")
        if records_found > 0:
            sample_name = res.data[0].get("scheme_name")
            print(f"   Sample scheme title (public metadata): '{sample_name}'")
    except Exception as exc:
        print(f"[ERROR] Harmless SELECT from public.schemes failed: {exc}")
        return False

    print("\n------------------------------------------------------------")
    print("ADMIN CLIENT VERIFICATION RESULT: ALL CHECKS PASSED")
    print("------------------------------------------------------------")
    return True


if __name__ == "__main__":
    success = verify_admin_client()
    sys.exit(0 if success else 1)
