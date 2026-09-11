import sys
import os

# Add backend directory to sys.path so app can be imported
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import unittest
from fastapi.testclient import TestClient
from app.main import app


class TestHealthEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        """Verify that GET /health returns 200 and expected status payload."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["message"], "AI Government Scheme Recommendation API is running")


if __name__ == "__main__":
    unittest.main()
