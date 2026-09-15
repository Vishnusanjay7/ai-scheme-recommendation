"""
Integration Tests: Scheme API Endpoints
---------------------------------------
Tests FastAPI endpoints for scheme discovery:
  - GET /api/schemes
  - GET /api/schemes/{scheme_id}
  - GET /api/schemes/search?q=
  - GET /api/schemes/state/{state_id}
  - GET /api/schemes/central
  - GET /api/schemes/active
  - 404 handling on non-existent / invalid UUID
  - Empty search results
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.models.scheme import SchemeDetailResponse, SchemeItemResponse, SchemeListResponse


class TestSchemeAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.routes.schemes.scheme_service.get_schemes")
    def test_list_schemes(self, mock_get_schemes):
        """Verify GET /api/schemes returns paginated schemes list."""
        mock_get_schemes.return_value = SchemeListResponse(
            total=1,
            count=1,
            offset=0,
            limit=50,
            data=[
                SchemeItemResponse(
                    id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    scheme_name="Pradhan Mantri Awas Yojana",
                    government_level="CENTRAL",
                    status="ACTIVE",
                    source_url="https://www.myscheme.gov.in/schemes/pmay",
                )
            ],
        )

        response = self.client.get("/api/schemes")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["data"][0]["scheme_name"], "Pradhan Mantri Awas Yojana")

    @patch("app.routes.schemes.scheme_service.get_scheme_by_id")
    def test_get_scheme_detail_success(self, mock_get_by_id):
        """Verify GET /api/schemes/{scheme_id} returns detailed relations."""
        test_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        mock_get_by_id.return_value = SchemeDetailResponse(
            id=test_id,
            scheme_name="PM Kisan Samman Nidhi",
            government_level="CENTRAL",
            status="ACTIVE",
            source_url="https://pmkisan.gov.in",
            eligibility={"min_age": 18, "category": "Farmer"},
            documents=[{"document_name": "Aadhaar Card", "mandatory": True}],
            sources=[{"source_url": "https://pmkisan.gov.in"}],
        )

        response = self.client.get(f"/api/schemes/{test_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], test_id)
        self.assertIsNotNone(data["eligibility"])
        self.assertEqual(len(data["documents"]), 1)

    @patch("app.routes.schemes.scheme_service.get_scheme_by_id")
    def test_get_scheme_detail_not_found(self, mock_get_by_id):
        """Verify GET /api/schemes/{invalid_id} returns 404."""
        mock_get_by_id.return_value = None
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(f"/api/schemes/{fake_uuid}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"].lower())

    @patch("app.routes.schemes.scheme_service.search_schemes")
    def test_search_schemes(self, mock_search):
        """Verify GET /api/schemes/search?q=query returns matching results."""
        mock_search.return_value = SchemeListResponse(
            total=1,
            count=1,
            offset=0,
            limit=50,
            data=[
                SchemeItemResponse(
                    id="cccccccc-cccc-cccc-cccc-cccccccccccc",
                    scheme_name="National Scholarship Portal Scheme",
                    government_level="CENTRAL",
                    status="ACTIVE",
                    source_url="https://scholarships.gov.in",
                )
            ],
        )

        response = self.client.get("/api/schemes/search?q=scholarship")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertIn("Scholarship", data["data"][0]["scheme_name"])

    @patch("app.routes.schemes.scheme_service.search_schemes")
    def test_search_schemes_empty_result(self, mock_search):
        """Verify search with no matches returns 200 with empty list."""
        mock_search.return_value = SchemeListResponse(
            total=0, count=0, offset=0, limit=50, data=[]
        )

        response = self.client.get("/api/schemes/search?q=nonexistentkeyword123")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(len(data["data"]), 0)

    @patch("app.routes.schemes.scheme_service.get_central_schemes")
    def test_list_central_schemes(self, mock_central):
        """Verify GET /api/schemes/central."""
        mock_central.return_value = SchemeListResponse(
            total=1,
            count=1,
            offset=0,
            limit=50,
            data=[
                SchemeItemResponse(
                    id="dddddddd-dddd-dddd-dddd-dddddddddddd",
                    scheme_name="Central Scheme Example",
                    government_level="CENTRAL",
                    status="ACTIVE",
                    source_url="https://central.gov.in",
                )
            ],
        )

        response = self.client.get("/api/schemes/central")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"][0]["government_level"], "CENTRAL")

    @patch("app.routes.schemes.scheme_service.get_active_schemes")
    def test_list_active_schemes(self, mock_active):
        """Verify GET /api/schemes/active."""
        mock_active.return_value = SchemeListResponse(
            total=1,
            count=1,
            offset=0,
            limit=50,
            data=[
                SchemeItemResponse(
                    id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
                    scheme_name="Active Scheme Example",
                    government_level="CENTRAL",
                    status="ACTIVE",
                    source_url="https://active.gov.in",
                )
            ],
        )

        response = self.client.get("/api/schemes/active")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"][0]["status"], "ACTIVE")

    @patch("app.routes.schemes.scheme_service.get_schemes_by_state")
    def test_list_state_schemes(self, mock_state):
        """Verify GET /api/schemes/state/{state_id}."""
        mock_state.return_value = SchemeListResponse(
            total=1,
            count=1,
            offset=0,
            limit=50,
            data=[
                SchemeItemResponse(
                    id="ffffffff-ffff-ffff-ffff-ffffffffffff",
                    scheme_name="Tamil Nadu Moovalur Scheme",
                    government_level="STATE",
                    state_id=23,
                    status="ACTIVE",
                    source_url="https://tn.gov.in",
                )
            ],
        )

        response = self.client.get("/api/schemes/state/TN")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"][0]["state_id"], 23)


if __name__ == "__main__":
    unittest.main()
