"""
Supabase Client Integration
---------------------------
Provides a thread-safe singleton client for interacting with Supabase PostgreSQL and Auth.
Credentials are read strictly from environment variables:
  - SUPABASE_URL
  - SUPABASE_PUBLISHABLE_KEY (or SUPABASE_ANON_KEY)
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client, ClientOptions

# Automatically find and load .env from backend/ or project root
_backend_dir = Path(__file__).resolve().parent.parent.parent
_root_dir = _backend_dir.parent

load_dotenv(_backend_dir / ".env")
load_dotenv(_root_dir / ".env")

_supabase_client: Optional[Client] = None


import re

def normalize_supabase_url(url: Optional[str]) -> Optional[str]:
    """
    Sanitize and normalize Supabase URL.
    If a dashboard project URL is provided (e.g., https://supabase.com/dashboard/project/<ref>),
    it converts it to the proper API URL: https://<ref>.supabase.co.
    """
    if not url:
        return url
    url = url.strip()
    match = re.match(r"^https?://(?:www\.)?supabase\.com/dashboard/project/([a-zA-Z0-9_-]+)/?$", url)
    if match:
        project_ref = match.group(1)
        return f"https://{project_ref}.supabase.co"
    return url.rstrip("/")


def get_supabase_url() -> Optional[str]:
    """Retrieve normalized Supabase API URL from environment."""
    raw_url = os.getenv("SUPABASE_URL")
    return normalize_supabase_url(raw_url) if raw_url else None


def get_supabase_publishable_key() -> Optional[str]:
    """Retrieve publishable/anon key from environment."""
    return (
        os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_KEY")
    )


def get_supabase_config() -> tuple[Optional[str], Optional[str]]:
    """
    Retrieve Supabase URL and Publishable Key from environment variables.
    Supports SUPABASE_URL, and SUPABASE_PUBLISHABLE_KEY (with SUPABASE_ANON_KEY / SUPABASE_KEY fallbacks).
    Never falls back to SUPABASE_SERVICE_ROLE_KEY to prevent accidental permission escalation in public client.
    """
    url = get_supabase_url()
    key = get_supabase_publishable_key()
    return url, key


def get_supabase_admin_key() -> Optional[str]:
    """Retrieve service-role key for backend administrative tasks."""
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY")


_supabase_admin_client: Optional[Client] = None


def is_supabase_admin_configured() -> bool:
    """Return True if both Supabase URL and service-role key are non-empty strings."""
    url = get_supabase_url()
    admin_key = get_supabase_admin_key()
    return bool(url and admin_key and url.strip() and admin_key.strip())


def get_supabase_admin_client() -> Client:
    """
    Get or initialize a dedicated backend-only Supabase client with service-role permissions.
    This client is strictly isolated from user sessions and publishable keys.
    Uses ClientOptions with auto_refresh_token=False and persist_session=False
    so that user sessions or auth tokens can never overwrite service-role authorization.
    Raises ValueError if SUPABASE_SERVICE_ROLE_KEY is not configured.
    """
    global _supabase_admin_client
    if _supabase_admin_client is not None:
        return _supabase_admin_client

    url = get_supabase_url()
    admin_key = get_supabase_admin_key()
    if not url or not admin_key or not admin_key.strip():
        raise ValueError(
            "Supabase admin credentials are missing. Please configure SUPABASE_SERVICE_ROLE_KEY "
            "in backend/.env for backend data ingestion."
        )

    from supabase import ClientOptions
    options = ClientOptions(
        auto_refresh_token=False,
        persist_session=False,
    )
    _supabase_admin_client = create_client(url.strip(), admin_key.strip(), options=options)
    return _supabase_admin_client


def reset_supabase_admin_client() -> None:
    """Reset the admin singleton instance."""
    global _supabase_admin_client
    _supabase_admin_client = None


def is_supabase_configured() -> bool:
    """Return True if both Supabase URL and key are non-empty strings."""
    url, key = get_supabase_config()
    return bool(url and key and url.strip() and key.strip())


def get_supabase_client() -> Client:
    """
    Get or initialize the cached Supabase client singleton.
    Raises ValueError if environment variables are not configured.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    url, key = get_supabase_config()

    if not url or not key:
        raise ValueError(
            "Supabase credentials are missing. Please configure SUPABASE_URL and "
            "SUPABASE_PUBLISHABLE_KEY in backend/.env or environment variables."
        )

    _supabase_client = create_client(url.strip(), key.strip())
    return _supabase_client


def get_authenticated_supabase_client(token: str) -> Client:
    """
    Create a lightweight Supabase client scoped to an authenticated citizen's JWT session.
    PostgREST requests executed by this client include the citizen's bearer token in the
    Authorization header, allowing PostgreSQL Row Level Security (RLS) to evaluate auth.uid()
    correctly against the calling citizen's identity.
    """
    if not token or not token.strip():
        raise ValueError("A valid citizen authentication token is required.")

    url, key = get_supabase_config()
    if not url or not key:
        raise ValueError(
            "Supabase credentials are missing. Please configure SUPABASE_URL and "
            "SUPABASE_PUBLISHABLE_KEY."
        )

    options = ClientOptions(
        headers={"Authorization": f"Bearer {token.strip()}"},
        auto_refresh_token=False,
        persist_session=False,
    )
    client = create_client(url.strip(), key.strip(), options=options)
    client.postgrest.auth(token.strip())
    return client



def reset_supabase_client() -> None:
    """Reset both singleton instances (useful for testing and configuration changes)."""
    global _supabase_client, _supabase_admin_client
    _supabase_client = None
    _supabase_admin_client = None


def check_supabase_connection() -> dict:
    """
    Test connectivity to the configured Supabase instance.
    Returns a dict with 'status', 'configured', and 'error' or 'details'.
    """
    if not is_supabase_configured():
        return {
            "status": "unconfigured",
            "configured": False,
            "message": "SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY are not set in environment.",
        }

    try:
        client = get_supabase_client()
        # Perform a lightweight read against states or a public reference table
        response = client.table("states").select("id, code, name").limit(1).execute()
        return {
            "status": "connected",
            "configured": True,
            "sample_data": response.data,
            "message": "Successfully connected to Supabase.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "configured": True,
            "message": f"Failed to connect to Supabase: {str(exc)}",
        }
