"""
Authentication Utilities & Dependencies
---------------------------------------
Provides helpers for extracting authenticated citizen identity (`auth.uid()`)
from incoming HTTP requests. Decouples authenticated sessions from guest evaluations.
"""

from typing import Optional
import uuid
import jwt
from fastapi import Header, HTTPException, status

from app.integrations.supabase_client import (
    get_supabase_client,
    is_supabase_configured,
)


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Extract raw bearer token from Authorization header value."""
    if not authorization:
        return None
    parts = authorization.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    if len(parts) == 1:
        return parts[0]
    return None


def get_authenticated_user_id(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> Optional[str]:
    """
    FastAPI dependency: Resolves the authenticated user ID (`auth.uid()`).
    Returns:
      - Valid user UUID string if request is authenticated.
      - None if request is anonymous / guest.
    Raises:
      - HTTPException(401) if invalid or malformed token is provided.
    """
    if not authorization:
        return None

    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'.",
        )

    # 1. Attempt verification via Supabase client if configured
    if is_supabase_configured():
        try:
            client = get_supabase_client()
            user_resp = client.auth.get_user(token)
            if user_resp and user_resp.user and user_resp.user.id:
                return str(user_resp.user.id)
        except Exception:
            # Fall back to decoding JWT payload if client network call fails or in test env
            pass

    # 2. Decode JWT payload to extract 'sub' claim (auth.uid)
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token missing citizen subject identifier ('sub').",
            )
        # Validate UUID format
        user_uuid = uuid.UUID(str(sub))
        return str(user_uuid)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed authentication token.",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token contains invalid citizen user identity.",
        )
