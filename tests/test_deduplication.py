"""
Unit Tests: Deterministic Scheme Deduplication Engine
------------------------------------------------------
Tests the high-confidence priority deduplication logic:
  1. Source Scheme ID match
  2. Source Slug match
  3. Normalized Name + Government Level + State ID match
  - Verifies that source_url / reference PDF alone NEVER identifies schemes as duplicates.
  - Verifies regression: cmgcpsii and gwwh sharing departmental PDF are NOT duplicates.
  - Verifies repeated ingestion of the SAME slug resolves to UPDATE (no duplicates created).
"""

import os
import sys
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.data_pipeline.deduplication import Deduplicator, extract_slug_from_source
from app.models.scheme import NormalizedScheme


class TestDeduplicator(unittest.TestCase):
    def setUp(self):
        self.deduplicator = Deduplicator()
        self.existing_records = [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "external_id": "MYSCHEME-101",
                "slug": "pmay-g",
                "scheme_name": "Pradhan Mantri Awas Yojana - Gramin",
                "government_level": "CENTRAL",
                "state_id": None,
                "official_url": "https://pmayg.nic.in",
                "source_url": "https://www.myscheme.gov.in/schemes/pmay-g",
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "external_id": None,
                "slug": "kmut",
                "scheme_name": "Kalaignar Magalir Urimai Thittam",
                "government_level": "STATE",
                "state_id": 23,
                "official_url": "https://kmut.tn.gov.in",
                "source_url": "https://tnega.tn.gov.in/schemes/kmut",
            },
        ]
        self.deduplicator.build_index(self.existing_records)

    def test_match_by_external_id(self):
        """Priority 1: Candidate with matching external scheme ID must resolve to UPDATE."""
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

    def test_match_by_source_slug(self):
        """Priority 2: Candidate with matching source slug must resolve to UPDATE."""
        candidate = NormalizedScheme(
            external_id=None,
            slug="kmut",
            scheme_name="KMUT Women Grant (Different Title)",
            government_level="STATE",
            state_id=23,
            source_url="https://different-source.gov.in",
        )
        action, existing, reason = self.deduplicator.find_duplicate(candidate)
        self.assertEqual(action, "UPDATE")
        self.assertEqual(existing["id"], "22222222-2222-2222-2222-222222222222")
        self.assertEqual(reason, "SLUG")

    def test_match_by_name_level_state(self):
        """Priority 3: Matching normalized name + level + state must resolve to UPDATE."""
        candidate = NormalizedScheme(
            external_id=None,
            slug=None,
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

    def test_shared_url_alone_does_not_create_duplicate(self):
        """
        Critical Rule: Source URL / official URL alone MUST NOT be treated as scheme identity.
        Two distinct schemes sharing the same official portal or policy page must be treated as independent.
        """
        candidate = NormalizedScheme(
            external_id=None,
            slug=None,
            scheme_name="Gramin Housing Initiative",  # Distinct scheme name
            government_level="CENTRAL",
            official_url="https://pmayg.nic.in/",     # Same portal URL as PMAY-G
            source_url="https://different.gov.in",
        )
        action, existing, reason = self.deduplicator.find_duplicate(candidate)
        self.assertEqual(action, "INSERT")
        self.assertIsNone(existing)
        self.assertEqual(reason, "GENUINELY_NEW")

    def test_regression_cmgcpsii_and_gwwh_are_not_duplicates(self):
        """
        Regression Test (Requirement 8):
        Chief Minister's Girl Child Protection Scheme-II (cmgcpsii)
        and Government Working Women's Hostel (gwwh)
        both cite the identical departmental PDF:
        'https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf'

        They MUST NOT be merged or identified as duplicates.
        Both must be preserved independently.
        """
        dedup = Deduplicator()

        # 1. Index cmgcpsii
        cmgcpsii_record = {
            "id": "cmgcpsii-uuid-0001",
            "external_id": "cmgcpsii",
            "slug": "cmgcpsii",
            "scheme_name": "Chief Minister's Girl Child Protection Scheme-II",
            "government_level": "STATE",
            "state_id": 23,
            "official_url": "https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
            "source_url": "https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
        }
        dedup.index_scheme(cmgcpsii_record)

        # 2. Candidate gwwh cites the exact same PDF URL
        candidate_gwwh = NormalizedScheme(
            external_id="gwwh",
            slug="gwwh",
            scheme_name="Government Working Women's Hostel",
            government_level="STATE",
            state_id=23,
            official_url="https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
            source_url="https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
        )

        action, existing, reason = dedup.find_duplicate(candidate_gwwh)

        # Crucial assertion: gwwh is NOT a duplicate of cmgcpsii
        self.assertEqual(action, "INSERT", "gwwh must be treated as an INSERT, not an UPDATE to cmgcpsii")
        self.assertIsNone(existing, "gwwh must not match cmgcpsii existing record")
        self.assertEqual(reason, "GENUINELY_NEW")

        # 3. Index gwwh as well
        gwwh_record = {
            "id": "gwwh-uuid-0002",
            "external_id": "gwwh",
            "slug": "gwwh",
            "scheme_name": "Government Working Women's Hostel",
            "government_level": "STATE",
            "state_id": 23,
            "official_url": "https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
            "source_url": "https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
        }
        dedup.index_scheme(gwwh_record)

        # Both records now exist independently in index
        self.assertIn("cmgcpsii", dedup.by_slug)
        self.assertIn("gwwh", dedup.by_slug)
        self.assertNotEqual(dedup.by_slug["cmgcpsii"]["id"], dedup.by_slug["gwwh"]["id"])

    def test_repeated_ingestion_of_same_slug_does_not_create_duplicates(self):
        """
        Requirement 9:
        Repeated ingestion of the SAME slug must always resolve to UPDATE
        and match the existing scheme record, preventing duplicates.
        """
        dedup = Deduplicator()

        scheme_record = {
            "id": "scheme-uuid-9999",
            "external_id": "cmgcpsii",
            "slug": "cmgcpsii",
            "scheme_name": "Chief Minister's Girl Child Protection Scheme-II",
            "government_level": "STATE",
            "state_id": 23,
            "official_url": "https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
            "source_url": "https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
        }
        dedup.index_scheme(scheme_record)

        # Subsequent ingestion with updated/same details but same slug
        repeated_candidate = NormalizedScheme(
            external_id="cmgcpsii",
            slug="cmgcpsii",
            scheme_name="Chief Minister's Girl Child Protection Scheme-II (Batch 2)",
            government_level="STATE",
            state_id=23,
            official_url="https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
            source_url="https://cms.tn.gov.in/sites/default/files/documents/swwe_e_cc_2022_23.pdf",
        )

        action, existing, reason = dedup.find_duplicate(repeated_candidate)
        self.assertEqual(action, "UPDATE")
        self.assertIsNotNone(existing)
        self.assertEqual(existing["id"], "scheme-uuid-9999")
        self.assertIn(reason, ["EXTERNAL_ID", "SLUG"])

    def test_build_index_extracts_slugs_from_sources(self):
        """Verify build_index extracts slugs from scheme_sources metadata and URLs."""
        schemes = [
            {
                "id": "uuid-1",
                "scheme_name": "Marriage Assistance Scheme",
                "government_level": "STATE",
                "state_id": 23,
                "official_url": "https://tn.gov.in/marriage",
                "source_url": "https://tn.gov.in/marriage",
            }
        ]
        sources = [
            {
                "scheme_id": "uuid-1",
                "source_url": "https://tn.gov.in/marriage",
                "source_type": "myScheme API mirror (slug: mranmas1)",
            }
        ]

        dedup = Deduplicator()
        dedup.build_index(schemes, sources)

        self.assertIn("mranmas1", dedup.by_slug)
        self.assertEqual(dedup.by_slug["mranmas1"]["id"], "uuid-1")

        # Candidate with slug mranmas1 resolves to UPDATE
        candidate = NormalizedScheme(
            external_id="mranmas1",
            slug="mranmas1",
            scheme_name="Marriage Assistance Scheme Updated",
            government_level="STATE",
            state_id=23,
            source_url="https://tn.gov.in/marriage",
        )
        action, existing, reason = dedup.find_duplicate(candidate)
        self.assertEqual(action, "UPDATE")
        self.assertEqual(existing["id"], "uuid-1")

    def test_extract_slug_helper(self):
        """Test slug extraction from source_type and source_url strings."""
        self.assertEqual(
            extract_slug_from_source("myScheme API mirror (slug: cmgcpsii)", None),
            "cmgcpsii",
        )
        self.assertEqual(
            extract_slug_from_source(None, "https://www.myscheme.gov.in/schemes/gwwh"),
            "gwwh",
        )
        self.assertIsNone(
            extract_slug_from_source("OFFICIAL_PORTAL", "https://tnsocialwelfare.tn.gov.in")
        )

    def test_genuinely_new_scheme(self):
        """Verify unprecedented scheme resolves to INSERT."""
        candidate = NormalizedScheme(
            external_id="NEW-999",
            slug="ayushman-bharat",
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
