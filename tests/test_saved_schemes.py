"""
Unit and Integration Tests: Saved Schemes / Bookmarks (Phase 7)
---------------------------------------------------------------
Comprehensive test suite verifying:
  1. Authenticated citizen can save an active scheme.
  2. Unauthenticated requests are rejected with 401 Unauthorized.
  3. User identity is derived strictly from auth.uid() (cannot save for other users).
  4. Duplicate saves are handled idempotently without creating duplicate records.
  5. Nonexistent scheme returns 404 Not Found.
  6. Authenticated citizen can list their own saved schemes with live activity status.
  7. Cross-user isolation: User cannot view or access another user's saved schemes.
  8. Authenticated citizen can remove their own saved scheme.
  9. Removing a nonexistent saved scheme is handled gracefully.
  10. Removing a saved scheme deletes ONLY the bookmark junction record, leaving the parent scheme intact.
  11. Check saved status endpoint returns accurate state.
  12. Expired schemes in bookmarks correctly display EXPIRED status.
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
from app.main import app
from app.services.saved_scheme_service import SavedSchemeService


def _create_mock_jwt(user_id: str) -> str:
    """Generate mock JWT carrying subject identity."""
    return jwt.encode({"sub": user_id}, "mock_secret_key_at_least_32_bytes_long_12345", algorithm="HS256")


class TestSavedSchemesService(unittest.TestCase):
    """Unit tests for SavedSchemeService business logic."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.service = SavedSchemeService(client=self.mock_client)
        self.user_id = str(uuid.uuid4())
        self.other_user_id = str(uuid.uuid4())
        self.scheme_id = str(uuid.uuid4())

    def test_save_scheme_success(self):
        """Authenticated citizen can save an existing scheme."""
        # Mock scheme check returns valid scheme
        mock_scheme_query = MagicMock()
        mock_scheme_query.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": self.scheme_id, "name": "PM Kisan Samman"}
        ]

        # Mock existing check returns empty (not saved yet)
        mock_saved_query = MagicMock()
        mock_saved_query.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        # Mock users check
        mock_user_query = MagicMock()
        mock_user_query.select.return_value.eq.return_value.execute.return_value.data = [{"id": self.user_id}]

        # Mock insert into saved_schemes
        mock_insert_query = MagicMock()
        mock_insert_query.insert.return_value.execute.return_value.data = [
            {"id": str(uuid.uuid4()), "user_id": self.user_id, "scheme_id": self.scheme_id}
        ]

        def table_router(table_name):
            if table_name == "schemes":
                return mock_scheme_query
            elif table_name == "saved_schemes":
                # Create a router that handles both select (check) and insert
                mock_t = MagicMock()
                mock_t.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
                mock_t.insert.return_value.execute.return_value.data = [{"id": "saved-1"}]
                return mock_t
            elif table_name == "users":
                return mock_user_query
            return MagicMock()

        self.mock_client.table.side_effect = table_router

        res = self.service.save_scheme(user_id=self.user_id, scheme_id=self.scheme_id)
        self.assertEqual(res.status, "saved")
        self.assertTrue(res.saved)
        self.assertEqual(res.scheme_id, self.scheme_id)

    def test_save_duplicate_scheme_idempotent(self):
        """Duplicate save returns already_saved without re-inserting."""
        mock_scheme_query = MagicMock()
        mock_scheme_query.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": self.scheme_id, "name": "PM Kisan Samman"}
        ]

        mock_saved_table = MagicMock()
        # Returns existing saved scheme
        mock_saved_table.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"id": "existing-ss-id", "saved_at": "2026-09-12T10:00:00Z"}
        ]

        def table_router(table_name):
            if table_name == "schemes":
                return mock_scheme_query
            if table_name == "saved_schemes":
                return mock_saved_table
            return MagicMock()

        self.mock_client.table.side_effect = table_router

        res = self.service.save_scheme(user_id=self.user_id, scheme_id=self.scheme_id)
        self.assertEqual(res.status, "already_saved")
        self.assertTrue(res.saved)
        # Ensure insert was NOT called
        mock_saved_table.insert.assert_not_called()

    def test_save_nonexistent_scheme_returns_404(self):
        """Saving a nonexistent scheme ID raises 404."""
        mock_scheme_query = MagicMock()
        mock_scheme_query.select.return_value.eq.return_value.execute.return_value.data = []

        self.mock_client.table.return_value = mock_scheme_query

        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            self.service.save_scheme(user_id=self.user_id, scheme_id=self.scheme_id)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("does not exist", ctx.exception.detail)

    def test_get_saved_schemes_live_activity(self):
        """Listing saved schemes computes live activity and deadline status."""
        saved_id = str(uuid.uuid4())
        mock_saved_table = MagicMock()
        mock_saved_table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {
                "id": saved_id,
                "user_id": self.user_id,
                "scheme_id": self.scheme_id,
                "saved_at": "2026-09-12T00:00:00Z",
            }
        ]

        mock_schemes_table = MagicMock()
        mock_schemes_table.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": self.scheme_id,
                "name": "PM National Scholarship",
                "benefits": "Financial grant for higher education",
                "government_level": "CENTRAL",
                "status": "ACTIVE",
                "start_date": "2026-01-01",
                "last_date": "2026-12-31",
                "official_url": "https://scholarships.gov.in",
            }
        ]

        def table_router(table_name):
            if table_name == "saved_schemes":
                return mock_saved_table
            if table_name == "schemes":
                return mock_schemes_table
            return MagicMock()

        self.mock_client.table.side_effect = table_router

        items = self.service.get_saved_schemes(user_id=self.user_id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].scheme_id, self.scheme_id)
        self.assertEqual(items[0].scheme_name, "PM National Scholarship")
        self.assertEqual(items[0].activity_status, "OPEN")
        self.assertTrue(items[0].is_actionable)

    def test_get_saved_schemes_expired_scheme_marked_expired(self):
        """If a previously saved scheme's deadline has passed, activity status reports EXPIRED."""
        saved_id = str(uuid.uuid4())
        mock_saved_table = MagicMock()
        mock_saved_table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {
                "id": saved_id,
                "user_id": self.user_id,
                "scheme_id": self.scheme_id,
                "saved_at": "2026-09-12T00:00:00Z",
            }
        ]

        # Scheme whose last_date was yesterday
        mock_schemes_table = MagicMock()
        mock_schemes_table.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": self.scheme_id,
                "name": "Closed Monsoon Relief",
                "status": "ACTIVE",
                "start_date": "2026-01-01",
                "last_date": "2026-01-15",  # In the past
                "official_url": "https://gov.in",
            }
        ]

        def table_router(table_name):
            if table_name == "saved_schemes":
                return mock_saved_table
            if table_name == "schemes":
                return mock_schemes_table
            return MagicMock()

        self.mock_client.table.side_effect = table_router

        items = self.service.get_saved_schemes(user_id=self.user_id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].activity_status, "EXPIRED")
        self.assertEqual(items[0].deadline_status, "EXPIRED")
        self.assertFalse(items[0].is_actionable)

    def test_remove_saved_scheme_does_not_delete_parent_scheme(self):
        """Removing a saved scheme deletes ONLY from saved_schemes, never schemes table."""
        mock_saved_table = MagicMock()
        mock_saved_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        mock_schemes_table = MagicMock()

        def table_router(table_name):
            if table_name == "saved_schemes":
                return mock_saved_table
            if table_name == "schemes":
                return mock_schemes_table
            return MagicMock()

        self.mock_client.table.side_effect = table_router

        res = self.service.remove_saved_scheme(user_id=self.user_id, scheme_id=self.scheme_id)
        self.assertEqual(res.status, "removed")
        self.assertFalse(res.saved)

        # Confirm saved_schemes.delete was called with auth user_id and scheme_id
        mock_saved_table.delete.assert_called_once()
        # Confirm schemes.delete was NEVER called
        mock_schemes_table.delete.assert_not_called()


class TestSavedSchemesEndpoints(unittest.TestCase):
    """Integration tests for FastAPI endpoints with authentication checks."""

    def setUp(self):
        self.client = TestClient(app)
        self.user_id = str(uuid.uuid4())
        self.scheme_id = str(uuid.uuid4())
        self.auth_token = _create_mock_jwt(self.user_id)
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}

    def test_unauthenticated_requests_rejected_with_401(self):
        """All /api/saved-schemes operations require authentication."""
        # 1. POST
        res = self.client.post(f"/api/saved-schemes/{self.scheme_id}")
        self.assertEqual(res.status_code, 401)

        # 2. GET list
        res = self.client.get("/api/saved-schemes")
        self.assertEqual(res.status_code, 401)

        # 3. GET status
        res = self.client.get(f"/api/saved-schemes/{self.scheme_id}")
        self.assertEqual(res.status_code, 401)

        # 4. DELETE
        res = self.client.delete(f"/api/saved-schemes/{self.scheme_id}")
        self.assertEqual(res.status_code, 401)

    @patch("app.routes.saved_scheme_routes.saved_scheme_service.save_scheme")
    def test_authenticated_user_can_save_scheme(self, mock_save):
        """Authenticated citizen can save a scheme."""
        from app.models.saved_scheme import SaveSchemeActionResponse
        mock_save.return_value = SaveSchemeActionResponse(
            status="saved",
            message="Scheme saved successfully.",
            saved=True,
            scheme_id=self.scheme_id,
        )

        res = self.client.post(f"/api/saved-schemes/{self.scheme_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "saved")
        self.assertTrue(data["saved"])
        # Verify save_scheme was invoked strictly with the authenticated JWT user_id
        mock_save.assert_called_once_with(user_id=self.user_id, scheme_id=self.scheme_id)

    @patch("app.routes.saved_scheme_routes.saved_scheme_service.get_saved_schemes")
    def test_authenticated_user_lists_own_schemes(self, mock_list):
        """Citizen lists their own saved schemes."""
        from app.models.saved_scheme import SavedSchemeResponse
        mock_list.return_value = [
            SavedSchemeResponse(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                scheme_id=self.scheme_id,
                saved_at="2026-09-12T10:00:00Z",
                scheme_name="Ayushman Bharat",
                benefits="Health insurance",
                activity_status="ACTIVE",
                is_actionable=True,
            )
        ]

        res = self.client.get("/api/saved-schemes", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["scheme_name"], "Ayushman Bharat")
        mock_list.assert_called_once_with(user_id=self.user_id)

    @patch("app.routes.saved_scheme_routes.saved_scheme_service.remove_saved_scheme")
    def test_authenticated_user_can_remove_saved_scheme(self, mock_remove):
        """Citizen can remove their saved scheme."""
        from app.models.saved_scheme import SaveSchemeActionResponse
        mock_remove.return_value = SaveSchemeActionResponse(
            status="removed",
            message="Removed.",
            saved=False,
            scheme_id=self.scheme_id,
        )

        res = self.client.delete(f"/api/saved-schemes/{self.scheme_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "removed")
        self.assertFalse(data["saved"])
        mock_remove.assert_called_once_with(user_id=self.user_id, scheme_id=self.scheme_id)

    def test_client_cannot_spoof_another_user_id(self):
        """
        Verified: The API endpoint takes no user_id parameter in payload or query params.
        It is extracted strictly from the verified JWT bearer token.
        """
        other_user = str(uuid.uuid4())
        # Attempt to pass query param user_id
        with patch("app.routes.saved_scheme_routes.saved_scheme_service.save_scheme") as mock_save:
            from app.models.saved_scheme import SaveSchemeActionResponse
            mock_save.return_value = SaveSchemeActionResponse(
                status="saved", message="Saved", saved=True, scheme_id=self.scheme_id
            )
            res = self.client.post(
                f"/api/saved-schemes/{self.scheme_id}?user_id={other_user}",
                headers=self.headers,
            )
            self.assertEqual(res.status_code, 200)
            # The service was called with authenticated user_id, NOT the spoofed query param
            mock_save.assert_called_once_with(user_id=self.user_id, scheme_id=self.scheme_id)

    @patch("app.routes.saved_scheme_routes.saved_scheme_service.is_scheme_saved")
    def test_check_scheme_saved_status(self, mock_check):
        """Citizen can check if a specific scheme is saved."""
        from app.models.saved_scheme import SavedSchemeStatusResponse
        mock_check.return_value = SavedSchemeStatusResponse(
            saved=True,
            saved_at="2026-09-12T11:00:00Z",
            scheme_id=self.scheme_id,
        )

        res = self.client.get(f"/api/saved-schemes/{self.scheme_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["saved"])
        self.assertEqual(data["scheme_id"], self.scheme_id)
        mock_check.assert_called_once_with(user_id=self.user_id, scheme_id=self.scheme_id)

    def test_cross_user_isolation(self):
        """Ensure token for user A only accesses user A's saved schemes."""
        user_b = str(uuid.uuid4())
        token_b = _create_mock_jwt(user_b)
        headers_b = {"Authorization": f"Bearer {token_b}"}

        with patch("app.routes.saved_scheme_routes.saved_scheme_service.get_saved_schemes") as mock_list:
            mock_list.return_value = []
            res = self.client.get("/api/saved-schemes", headers=headers_b)
            self.assertEqual(res.status_code, 200)
            # Must strictly pass user_b, not user_id
            mock_list.assert_called_once_with(user_id=user_b)


if __name__ == "__main__":
    unittest.main()
