"""
Unit Tests: Data Processing & Normalization
-------------------------------------------
Tests the normalization routines for:
  - Scheme names and whitespace
  - Diverse date formats (ISO, DD-MM-YYYY, DD/MM/YYYY, text)
  - Government level ('CENTRAL' vs 'STATE')
  - Central schemes state nullification
  - State schemes lookup matching
  - Status canonicalization
"""

import os
import sys
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.data_pipeline.data_processor import DataProcessor
from app.models.scheme import RawScheme


class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DataProcessor()
        self.state_lookup = {
            "tamil nadu": (23, "Tamil Nadu"),
            "tn": (23, "Tamil Nadu"),
            "delhi": (4, "Delhi"),
            "dl": (4, "Delhi"),
            "maharashtra": (14, "Maharashtra"),
            "mh": (14, "Maharashtra"),
        }
        self.category_lookup = {
            "agriculture, rural & environment": (1, "Agriculture, Rural & Environment"),
            "education & learning": (4, "Education & Learning"),
            "health & wellness": (5, "Health & Wellness"),
        }

    def test_whitespace_normalization(self):
        """Verify irregular whitespace and tabs are collapsed."""
        self.assertEqual(
            DataProcessor.normalize_whitespace("  Pradhan   Mantri    Awas   Yojana  \t"),
            "Pradhan Mantri Awas Yojana",
        )
        self.assertIsNone(DataProcessor.normalize_whitespace(None))
        self.assertIsNone(DataProcessor.normalize_whitespace("   "))

    def test_name_normalization(self):
        """Verify scheme names are stripped of whitespace and trailing quotes/periods."""
        self.assertEqual(
            DataProcessor.normalize_name(' "PM-KISAN Samman Nidhi." '),
            "PM-KISAN Samman Nidhi",
        )
        self.assertEqual(DataProcessor.normalize_name(""), "")

    def test_url_normalization(self):
        """Verify URL canonicalization, trailing slashes, and protocol addition."""
        self.assertEqual(
            DataProcessor.normalize_url("https://www.myscheme.gov.in/schemes/pm-kisan/"),
            "https://www.myscheme.gov.in/schemes/pm-kisan",
        )
        self.assertEqual(
            DataProcessor.normalize_url("myscheme.gov.in/schemes/"),
            "https://myscheme.gov.in/schemes",
        )
        self.assertIsNone(DataProcessor.normalize_url("invalid-url-string"))

    def test_date_normalization(self):
        """Verify safe parsing of multiple date formats into YYYY-MM-DD."""
        # ISO format
        self.assertEqual(DataProcessor.normalize_date("2026-05-31"), "2026-05-31")
        self.assertEqual(DataProcessor.normalize_date("2026-05-31T12:00:00Z"), "2026-05-31")

        # Indian formats
        self.assertEqual(DataProcessor.normalize_date("31-05-2026"), "2026-05-31")
        self.assertEqual(DataProcessor.normalize_date("31/05/2026"), "2026-05-31")

        # Alternative formats
        self.assertEqual(DataProcessor.normalize_date("2026/05/31"), "2026-05-31")
        self.assertEqual(DataProcessor.normalize_date("31.05.2026"), "2026-05-31")
        self.assertEqual(DataProcessor.normalize_date("31 May 2026"), "2026-05-31")

        # None / unparseable
        self.assertIsNone(DataProcessor.normalize_date(None))
        self.assertIsNone(DataProcessor.normalize_date("ongoing"))
        self.assertIsNone(DataProcessor.normalize_date("not-a-date"))

    def test_government_level_normalization(self):
        """Verify level resolves strictly to CENTRAL or STATE."""
        self.assertEqual(DataProcessor.normalize_government_level("Central"), "CENTRAL")
        self.assertEqual(DataProcessor.normalize_government_level("National"), "CENTRAL")
        self.assertEqual(DataProcessor.normalize_government_level("Union Territory"), "STATE")
        self.assertEqual(DataProcessor.normalize_government_level("State Govt"), "STATE")
        self.assertEqual(DataProcessor.normalize_government_level("state"), "STATE")
        self.assertEqual(DataProcessor.normalize_government_level(None), "CENTRAL")

    def test_central_scheme_state_nullification(self):
        """Strict rule: CENTRAL schemes must NEVER have a state_id assigned."""
        state_id, state_name = DataProcessor.normalize_state(
            "Tamil Nadu", "CENTRAL", self.state_lookup
        )
        self.assertIsNone(state_id)
        self.assertIsNone(state_name)

    def test_state_scheme_lookup(self):
        """Verify STATE schemes correctly resolve to known states."""
        state_id, state_name = DataProcessor.normalize_state(
            "Tamil Nadu", "STATE", self.state_lookup
        )
        self.assertEqual(state_id, 23)
        self.assertEqual(state_name, "Tamil Nadu")

        # Code match
        code_id, code_name = DataProcessor.normalize_state("TN", "STATE", self.state_lookup)
        self.assertEqual(code_id, 23)

    def test_status_normalization(self):
        """Verify scheme status maps to ACTIVE, INACTIVE, or EXPIRED."""
        self.assertEqual(DataProcessor.normalize_status("Live"), "ACTIVE")
        self.assertEqual(DataProcessor.normalize_status("Open"), "ACTIVE")
        self.assertEqual(DataProcessor.normalize_status("Closed"), "EXPIRED")
        self.assertEqual(DataProcessor.normalize_status("Disabled"), "INACTIVE")
        self.assertEqual(DataProcessor.normalize_status(None), "ACTIVE")

    def test_process_raw_scheme_end_to_end(self):
        """Verify transformation from RawScheme to NormalizedScheme."""
        raw = RawScheme(
            external_id="PMK-001",
            scheme_name="  Pradhan Mantri Kisan Samman Nidhi  ",
            government_level="Central Government",
            state="Tamil Nadu",  # Should be cleared for Central
            category="Agriculture",
            source_url="https://www.myscheme.gov.in/schemes/pm-kisan",
            start_date="01-12-2018",
            last_date="31/12/2030",
            status="Ongoing",
        )
        norm = DataProcessor.process_raw_scheme(raw, self.state_lookup, self.category_lookup)
        self.assertEqual(norm.scheme_name, "Pradhan Mantri Kisan Samman Nidhi")
        self.assertEqual(norm.government_level, "CENTRAL")
        self.assertIsNone(norm.state_id)  # Ensured NULL for Central
        self.assertEqual(norm.category_id, 1)
        self.assertEqual(norm.start_date, "2018-12-01")
        self.assertEqual(norm.last_date, "2030-12-31")
        self.assertEqual(norm.status, "ACTIVE")


if __name__ == "__main__":
    unittest.main()
