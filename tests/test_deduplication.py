"""
Unit Tests: Deduplication Engine
---------------------------------
Tests the 3-tier priority deduplication logic:
  1. Official External Scheme ID match
  2. Canonical Official URL match
  3. Normalized Name + Government Level + State match
  - Distinguishing UPDATE vs genuinely NEW schemes
"""

import os
import sys
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.data_pipeline.deduplication import Deduplicator
from app.models.scheme import NormalizedScheme


class TestDeduplicator(unittest.TestCase):
    def setUp(self):
        self.deduplicator = Deduplicator()
        self.existing_records = [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "external_id": "MYSCHEME-101",
                "scheme_name": "Pradhan Mantri Awas Yojana - Gramin",
                "government_level": "CENTRAL",
                "state_id": None,
                "official_url": "https://pmayg.nic.in",
                "source_url": "https://www.myscheme.gov.in/schemes/pmay-g",
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "external_id": None,
                "scheme_name": "Kalaignar Magalir Urimai Thittam",
                "government_level": "STATE",
                "state_id": 23,
                "official_url": "https://kmut.tn.gov.in",
                "source_url": "https://tnega.tn.gov.in/schemes/kmut",
            },
        ]
        self.deduplicator.build_index(self.existing_records)

    def test_match_by_external_id(self):
        """Priority 1: Candidate with matching external ID must resolve to UPDATE."""
        candidate = NormalizedScheme(
            external_id="MYSCHEME-101",
            scheme_name="PMAY Gramin (Renamed Title)",
            government_level="CENTRAL",
            source_url="https://other-source.gov.in",
        )
        action, existing, reason = self.deduplicator.find_duplicate(candidate)
        self.assertEqual(action, "UPDATE")
        self.assertEqual(existing["id"], "11111111-1111-1111-1111-111111111111")
        self.assertEqual(reason, "EXTERNAL_ID")

    def test_match_by_canonical_url(self):
        """Priority 2: Candidate with matching official URL must resolve to UPDATE."""
        candidate = NormalizedScheme(
            external_id=None,
            scheme_name="Gramin Housing Initiative",
            government_level="CENTRAL",
            official_url="https://pmayg.nic.in/",  # Note trailing slash
            source_url="https://different.gov.in",
        )
        action, existing, reason = self.deduplicator.find_duplicate(candidate)
        self.assertEqual(action, "UPDATE")
        self.assertEqual(existing["id"], "11111111-1111-1111-1111-111111111111")
        self.assertEqual(reason, "CANONICAL_OFFICIAL_URL")

    def test_match_by_name_level_state(self):
        """Priority 3: Matching normalized name + level + state must resolve to UPDATE."""
        candidate = NormalizedScheme(
            external_id=None,
            scheme_name="  kalaignar   magalir  urimai   thittam  ",
            government_level="STATE",
            state_id=23,
            official_url="https://new-portal.tn.gov.in",
            source_url="https://new-source.tn.gov.in",
        )
        action, existing, reason = self.deduplicator.find_duplicate(candidate)
        self.assertEqual(action, "UPDATE")
        self.assertEqual(existing["id"], "22222222-2222-2222-2222-222222222222")
        self.assertEqual(reason, "NAME_LEVEL_STATE")

    def test_genuinely_new_scheme(self):
        """Verify unprecedented scheme resolves to INSERT."""
        candidate = NormalizedScheme(
            external_id="NEW-999",
            scheme_name="Ayushman Bharat National Health Protection Mission",
            government_level="CENTRAL",
            state_id=None,
            official_url="https://pmjay.gov.in",
            source_url="https://www.myscheme.gov.in/schemes/pmjay",
        )
        action, existing, reason = self.deduplicator.find_duplicate(candidate)
        self.assertEqual(action, "INSERT")
        self.assertIsNone(existing)
        self.assertEqual(reason, "GENUINELY_NEW")


if __name__ == "__main__":
    unittest.main()
