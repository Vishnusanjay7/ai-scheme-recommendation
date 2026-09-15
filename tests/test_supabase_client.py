import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.integrations.supabase_client import (
    get_supabase_config,
    is_supabase_configured,
    get_supabase_client,
    reset_supabase_client,
    check_supabase_connection,
)


class TestSupabaseClientIntegration(unittest.TestCase):
    def setUp(self):
        reset_supabase_client()

    def tearDown(self):
        reset_supabase_client()

    def test_unconfigured_credentials_handling(self):
        """Test behavior when credentials are missing from environment."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure keys are absent
            for key in ["SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_KEY"]:
                os.environ.pop(key, None)

            self.assertFalse(is_supabase_configured())
            status = check_supabase_connection()
            self.assertEqual(status["status"], "unconfigured")
            self.assertFalse(status["configured"])

            with self.assertRaises(ValueError) as ctx:
                get_supabase_client()
            self.assertIn("Supabase credentials are missing", str(ctx.exception))

    def test_configured_credentials_recognition(self):
        """Test that is_supabase_configured correctly recognizes valid credentials."""
        test_env = {
            "SUPABASE_URL": "https://xyzexampleproject.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "sample-publishable-key-12345",
        }
        with patch.dict(os.environ, test_env, clear=True):
            url, key = get_supabase_config()
            self.assertEqual(url, "https://xyzexampleproject.supabase.co")
            self.assertEqual(key, "sample-publishable-key-12345")
            self.assertTrue(is_supabase_configured())

    @patch("app.integrations.supabase_client.create_client")
    def test_singleton_client_creation(self, mock_create_client):
        """Verify client is created as a singleton and cached."""
        mock_instance = MagicMock()
        mock_create_client.return_value = mock_instance

        test_env = {
            "SUPABASE_URL": "https://xyzexampleproject.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "sample-publishable-key-12345",
        }
        with patch.dict(os.environ, test_env, clear=True):
            client1 = get_supabase_client()
            client2 = get_supabase_client()

            self.assertIs(client1, client2)
            mock_create_client.assert_called_once_with(
                "https://xyzexampleproject.supabase.co", "sample-publishable-key-12345"
            )

    @patch("app.integrations.supabase_client.create_client")
    def test_connection_check_success(self, mock_create_client):
        """Verify check_supabase_connection handles a successful ping."""
        mock_table = MagicMock()
        mock_table.select.return_value.limit.return_value.execute.return_value.data = [
            {"id": 1, "code": "TN", "name": "Tamil Nadu"}
        ]
        mock_client = MagicMock()
        mock_client.table.return_value = mock_table
        mock_create_client.return_value = mock_client

        test_env = {
            "SUPABASE_URL": "https://xyzexampleproject.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "sample-key",
        }
        with patch.dict(os.environ, test_env, clear=True):
            result = check_supabase_connection()
            self.assertEqual(result["status"], "connected")
            self.assertTrue(result["configured"])
            self.assertEqual(len(result["sample_data"]), 1)


if __name__ == "__main__":
    unittest.main()
