"""
Integration Tests: Pipeline Execution
-------------------------------------
Tests end-to-end data acquisition workflow:
  - Valid record processing
  - Invalid record rejection
  - Provenance storage
  - Dry run summary output
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.data_pipeline.importers.official_importer import OfficialImporter
from app.data_pipeline.scheme_collector import SchemeCollector


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.importer = OfficialImporter(dry_run=True)
        # Mock lookup data so tests run deterministically offline
        self.importer.state_lookup = {
            "tamil nadu": (23, "Tamil Nadu"),
            "tn": (23, "Tamil Nadu"),
        }
        self.importer.category_lookup = {
            "agriculture": (1, "Agriculture, Rural & Environment"),
            "education": (4, "Education & Learning"),
        }
        self.importer._initialized = True

    def test_valid_record_flow(self):
        """Verify valid records are normalized, validated, and staged."""
        records = [
            {
                "external_id": "GOV-001",
                "scheme_name": "National Apprenticeship Training Scheme",
                "government_level": "CENTRAL",
                "category": "education",
                "source_url": "https://www.myscheme.gov.in/schemes/nats",
                "official_url": "https://nats.education.gov.in",
                "required_documents": ["Aadhaar Card", "Degree Certificate"],
                "eligibility": {"min_age": 18, "max_age": 30},
            }
        ]
        summary = self.importer.import_records(records, source_identifier="test_run")
        self.assertEqual(summary["records_received"], 1)
        self.assertEqual(summary["records_valid"], 1)
        self.assertEqual(summary["records_rejected"], 0)
        self.assertEqual(summary["new_schemes"], 1)
        self.assertEqual(len(summary["errors"]), 0)

    def test_invalid_record_rejection(self):
        """Verify invalid records are rejected and structured errors logged."""
        records = [
            {
                "scheme_name": "X",  # Too short
                "government_level": "INVALID_LEVEL",
                "source_url": "bad-url",
            }
        ]
        summary = self.importer.import_records(records, source_identifier="test_bad_run")
        self.assertEqual(summary["records_received"], 1)
        self.assertEqual(summary["records_valid"], 0)
        self.assertEqual(summary["records_rejected"], 1)
        self.assertEqual(summary["new_schemes"], 0)
        self.assertGreater(len(summary["errors"]), 0)

    def test_deduplication_and_update_behavior(self):
        """Verify identical scheme in subsequent batch triggers UPDATE."""
        record = {
            "external_id": "SAME-100",
            "scheme_name": "Prime Minister Special Scholarship",
            "government_level": "CENTRAL",
            "source_url": "https://www.myscheme.gov.in/schemes/pmsss",
        }
        # First import
        summary1 = self.importer.import_records([record])
        self.assertEqual(summary1["new_schemes"], 1)
        self.assertEqual(summary1["updated_schemes"], 0)

        # Second import of same scheme
        summary2 = self.importer.import_records([record])
        self.assertEqual(summary2["new_schemes"], 0)
        self.assertEqual(summary2["updated_schemes"], 1)
        self.assertEqual(summary2["duplicates"], 1)

    @patch("app.data_pipeline.importers.official_importer.get_supabase_admin_client")
    def test_live_persistence_call_flow(self, mock_get_admin_client):
        """Verify live persistence interacts with all 4 Supabase tables."""
        mock_admin = MagicMock()
        mock_admin.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "mocked-uuid-1234"}
        ]
        mock_get_admin_client.return_value = mock_admin

        live_importer = OfficialImporter(dry_run=False)
        live_importer.state_lookup = {"tamil nadu": (23, "Tamil Nadu")}
        live_importer.category_lookup = {"agriculture": (1, "Agriculture")}
        live_importer._initialized = True

        record = {
            "external_id": "LIVE-01",
            "scheme_name": "Tamil Nadu Uzhavar Pathukappu Thittam",
            "government_level": "STATE",
            "state": "Tamil Nadu",
            "source_url": "https://tn.gov.in/scheme",
            "required_documents": ["Farmer ID Card"],
            "eligibility": {"min_age": 18},
        }

        summary = live_importer.import_records([record])
        self.assertEqual(summary["records_valid"], 1)
        self.assertEqual(summary["new_schemes"], 1)

        # Verify table insert calls
        called_tables = [c[0][0] for c in mock_admin.table.call_args_list]
        self.assertIn("schemes", called_tables)
        self.assertIn("scheme_eligibility", called_tables)
        self.assertIn("scheme_documents", called_tables)
        self.assertIn("scheme_sources", called_tables)


if __name__ == "__main__":
    unittest.main()
