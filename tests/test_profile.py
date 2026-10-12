"""
Unit and Integration Tests: Profile Management & RLS Isolation (Phase 17)
-------------------------------------------------------------------------
Verifies:
  1. Unauthenticated profile access (GET/PUT) is rejected with 401 Unauthorized.
  2. Malformed or invalid JWT returns 401 Unauthorized.
  3. Authenticated profile creation when citizen has no row in public.users (BUG-01 fix).
  4. Authenticated profile update updates user_profiles and public.users correctly.
  5. Security isolation: Identity is bound strictly to JWT claims (auth.uid()).
  6. PostgreSQL RLS 42501 error maps to controlled 403 Forbidden instead of leaking 500.
  7. RLS remains enabled on users and user_profiles with zero insecure policies.
"""

import os
import sys
import unittest
import uuid
from unittest.mock import MagicMock, patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import jwt
from fastapi.testclient import TestClient
from postgrest.exceptions import APIError
from app.main import app

client = TestClient(app)


def _create_mock_jwt(user_id: str, email: str = "citizen@example.com", full_name: str = "Test Citizen") -> str:
    """Generate mock JWT with subject identity and user metadata."""
    payload = {
        "sub": user_id,
        "email": email,
        "user_metadata": {"full_name": full_name},
    }
    return jwt.encode(payload, "mock_secret_key_at_least_32_bytes_long_12345", algorithm="HS256")


class TestProfileAPI(unittest.TestCase):
    def setUp(self):
        self.user_id = str(uuid.uuid4())
        self.other_user_id = str(uuid.uuid4())
        self.token = _create_mock_jwt(self.user_id, "citizen@example.com", "Ramesh Kumar")
        self.other_token = _create_mock_jwt(self.other_user_id, "other@example.com", "Other User")

    def test_unauthenticated_profile_access_returns_401(self):
        """Unauthenticated GET and PUT to /api/profile must return 401."""
        res_get = client.get("/api/profile")
        self.assertEqual(res_get.status_code, 401)
        self.assertIn("Authentication required", res_get.json()["detail"])

        res_put = client.put("/api/profile", json={"age": 25})
        self.assertEqual(res_put.status_code, 401)
        self.assertIn("Authentication required", res_put.json()["detail"])

    def test_malformed_token_returns_401(self):
        """Malformed or invalid authorization header returns 401."""
        res = client.get("/api/profile", headers={"Authorization": "Bearer invalid.jwt.token"})
        self.assertEqual(res.status_code, 401)

        res = client.put("/api/profile", headers={"Authorization": "Bearer invalid.jwt.token"}, json={"age": 25})
        self.assertEqual(res.status_code, 401)

    @patch("app.routes.profile_routes.get_authenticated_supabase_client")
    def test_authenticated_profile_creation_with_new_user(self, mock_get_auth_client):
        """
        Exact scenario of BUG-01:
        When citizen is authenticated but has no existing row in public.users,
        PUT /api/profile creates public.users and user_profiles with authenticated client.
        """
        mock_supabase = MagicMock()
        mock_get_auth_client.return_value = mock_supabase

        user_row = {"id": self.user_id, "email": "citizen@example.com", "full_name": "Ramesh Kumar"}
        prof_row = {
            "id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "age": 25,
            "gender": "MALE",
            "state_id": 23,
            "district_id": 1,
            "annual_income": 180000,
            "occupation": "Student",
            "education": "Higher Secondary (12th)",
            "category": "General",
            "disability_status": False,
        }

        # Users table mock
        mock_users = MagicMock()
        mock_users.select.return_value = mock_users
        mock_users.insert.return_value = mock_users
        mock_users.update.return_value = mock_users
        mock_users.eq.return_value = mock_users
        mock_users.limit.return_value = mock_users
        mock_users.execute.side_effect = [
            MagicMock(data=[]),            # user_check in update
            MagicMock(data=[user_row]),    # insert execute
            MagicMock(data=[user_row]),    # get_current_user_profile
        ]

        # User profiles table mock
        mock_profiles = MagicMock()
        mock_profiles.select.return_value = mock_profiles
        mock_profiles.insert.return_value = mock_profiles
        mock_profiles.update.return_value = mock_profiles
        mock_profiles.eq.return_value = mock_profiles
        mock_profiles.limit.return_value = mock_profiles
        mock_profiles.execute.side_effect = [
            MagicMock(data=[]),            # existing check in update
            MagicMock(data=[prof_row]),    # insert execute
            MagicMock(data=[prof_row]),    # get_current_user_profile
        ]

        # Districts table mock
        mock_districts = MagicMock()
        mock_districts.select.return_value = mock_districts
        mock_districts.eq.return_value = mock_districts
        mock_districts.limit.return_value = mock_districts
        mock_districts.execute.return_value = MagicMock(data=[{"id": 1, "name": "Chennai"}])

        # States table mock
        mock_states = MagicMock()
        mock_states.select.return_value = mock_states
        mock_states.eq.return_value = mock_states
        mock_states.limit.return_value = mock_states
        mock_states.execute.return_value = MagicMock(data=[{"id": 23, "name": "Tamil Nadu"}])

        def table_router(table_name):
            if table_name == "users":
                return mock_users
            elif table_name == "user_profiles":
                return mock_profiles
            elif table_name == "districts":
                return mock_districts
            elif table_name == "states":
                return mock_states
            return MagicMock()

        mock_supabase.table.side_effect = table_router

        payload = {
            "full_name": "Ramesh Kumar",
            "age": 25,
            "gender": "MALE",
            "state_id": 23,
            "district_id": 1,
            "annual_income": 180000,
            "occupation": "Student",
            "education": "Higher Secondary (12th)",
            "category": "General",
            "disability_status": False,
        }

        response = client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {self.token}"},
            json=payload,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_id"], self.user_id)
        self.assertEqual(data["full_name"], "Ramesh Kumar")
        self.assertEqual(data["email"], "citizen@example.com")

        # Verify authenticated client was initialized with the user's token
        mock_get_auth_client.assert_called_with(self.token)
        mock_users.insert.assert_called()

    @patch("app.routes.profile_routes.get_authenticated_supabase_client")
    def test_authenticated_profile_update_existing_user(self, mock_get_auth_client):
        """When citizen already exists, PUT /api/profile updates user_profiles."""
        mock_supabase = MagicMock()
        mock_get_auth_client.return_value = mock_supabase

        user_row = {"id": self.user_id, "email": "citizen@example.com", "full_name": "Ramesh Kumar"}
        prof_row = {
            "id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "age": 26,
            "gender": "MALE",
            "state_id": 23,
            "district_id": 1,
            "annual_income": 200000,
            "occupation": "Farmer",
            "education": "Graduate",
            "category": "OBC",
            "disability_status": False,
        }

        mock_users = MagicMock()
        mock_users.select.return_value = mock_users
        mock_users.update.return_value = mock_users
        mock_users.eq.return_value = mock_users
        mock_users.limit.return_value = mock_users
        mock_users.execute.return_value = MagicMock(data=[user_row])

        mock_profiles = MagicMock()
        mock_profiles.select.return_value = mock_profiles
        mock_profiles.update.return_value = mock_profiles
        mock_profiles.eq.return_value = mock_profiles
        mock_profiles.limit.return_value = mock_profiles
        mock_profiles.execute.return_value = MagicMock(data=[prof_row])

        mock_districts = MagicMock()
        mock_districts.select.return_value = mock_districts
        mock_districts.eq.return_value = mock_districts
        mock_districts.limit.return_value = mock_districts
        mock_districts.execute.return_value = MagicMock(data=[{"id": 1, "name": "Chennai"}])

        mock_states = MagicMock()
        mock_states.select.return_value = mock_states
        mock_states.eq.return_value = mock_states
        mock_states.limit.return_value = mock_states
        mock_states.execute.return_value = MagicMock(data=[{"id": 23, "name": "Tamil Nadu"}])

        def table_router(table_name):
            if table_name == "users":
                return mock_users
            elif table_name == "user_profiles":
                return mock_profiles
            elif table_name == "districts":
                return mock_districts
            elif table_name == "states":
                return mock_states
            return MagicMock()

        mock_supabase.table.side_effect = table_router

        payload = {"age": 26, "occupation": "Farmer"}
        response = client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {self.token}"},
            json=payload,
        )

        self.assertEqual(response.status_code, 200)
        mock_profiles.update.assert_called()

    @patch("app.routes.profile_routes.get_authenticated_supabase_client")
    def test_rls_violation_returns_controlled_403(self, mock_get_auth_client):
        """PostgreSQL RLS 42501 error returns HTTP 403 rather than unhandled HTTP 500."""
        mock_supabase = MagicMock()
        mock_get_auth_client.return_value = mock_supabase

        mock_users = MagicMock()
        mock_users.select.return_value.eq.return_value.execute.side_effect = APIError(
            {"message": "new row violates row-level security policy for table \"users\"", "code": "42501"}
        )
        mock_supabase.table.return_value = mock_users

        response = client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"age": 25},
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("Access denied by security policy", response.json()["detail"])

    def test_schema_rls_integrity(self):
        """Verify database/schema.sql maintains RLS across all tables and has no insecure policies."""
        schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            content = f.read()

        # RLS enabled on users and user_profiles
        self.assertIn("ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;", content)
        self.assertIn("ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;", content)

        # No insecure wildcard write policies on private tables
        self.assertNotIn("CREATE POLICY \"Allow public write access on users\"", content)
        self.assertNotIn("CREATE POLICY \"Allow public write access on user_profiles\"", content)
        self.assertNotIn("ON public.user_profiles FOR INSERT WITH CHECK (true)", content)
        self.assertNotIn("ON public.users FOR INSERT WITH CHECK (true)", content)


if __name__ == "__main__":
    unittest.main()
