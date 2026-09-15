"""
Unit Tests: Data Validation
---------------------------
Tests validation rules against scheme entity constraints:
  - Missing or too short scheme names
  - Invalid government levels
  - Malformed URLs
  - Inconsistent dates (last_date < start_date)
  - State scheme missing state_id
  - Central scheme erroneously assigned state_id
"""

import os
import sys
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.data_pipeline.data_validator import DataValidator
from app.models.scheme import NormalizedScheme


class TestDataValidator(unittest.TestCase):
    def _create_base_scheme(self, **kwargs):
        defaults = {
            "scheme_name": "National Scholarship Scheme",
            "government_level": "CENTRAL",
            "state_id": None,
            "category_id": 1,
            "source_url": "https://www.myscheme.gov.in/schemes/scholarship",
            "status": "ACTIVE",
        }
        defaults.update(kwargs)
        return NormalizedScheme(**defaults)

    def test_valid_scheme_passes(self):
        """Verify standard valid central and state schemes pass."""
        central = self._create_base_scheme()
        res_central = DataValidator.validate_scheme(central)
        self.assertTrue(res_central.is_valid)
        self.assertEqual(len(res_central.errors), 0)

        state_scheme = self._create_base_scheme(
            government_level="STATE",
            state_id=23,
            scheme_name="Tamil Nadu Moovalur Ramamirtham Scheme",
        )
        res_state = DataValidator.validate_scheme(state_scheme)
        self.assertTrue(res_state.is_valid)
        self.assertEqual(len(res_state.errors), 0)

    def test_missing_scheme_name(self):
        """Verify empty or short scheme name is rejected."""
        scheme_empty = self._create_base_scheme(scheme_name="")
        res = DataValidator.validate_scheme(scheme_empty)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("name is missing" in e for e in res.errors))

        scheme_short = self._create_base_scheme(scheme_name="AB")
        res_short = DataValidator.validate_scheme(scheme_short)
        self.assertFalse(res_short.is_valid)

    def test_invalid_government_level(self):
        """Verify non-central/state level is rejected."""
        scheme = self._create_base_scheme(government_level="MUNICIPAL")
        res = DataValidator.validate_scheme(scheme)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("government level" in e for e in res.errors))

    def test_state_scheme_without_state_id(self):
        """Verify STATE scheme without state_id is rejected."""
        scheme = self._create_base_scheme(government_level="STATE", state_id=None)
        res = DataValidator.validate_scheme(scheme)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("requires a valid state_id" in e for e in res.errors))

    def test_central_scheme_with_state_id(self):
        """Verify CENTRAL scheme with state_id is rejected."""
        scheme = self._create_base_scheme(government_level="CENTRAL", state_id=23)
        res = DataValidator.validate_scheme(scheme)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("must not be assigned a state_id" in e for e in res.errors))

    def test_invalid_urls(self):
        """Verify malformed source or official URLs are rejected."""
        scheme_bad_source = self._create_base_scheme(source_url="not-a-valid-url")
        res = DataValidator.validate_scheme(scheme_bad_source)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("source URL" in e for e in res.errors))

        scheme_bad_official = self._create_base_scheme(official_url="ftp://bad-url")
        res_official = DataValidator.validate_scheme(scheme_bad_official)
        self.assertFalse(res_official.is_valid)
        self.assertTrue(any("official application URL" in e for e in res_official.errors))

    def test_invalid_date_order(self):
        """Verify last_date earlier than start_date is rejected."""
        scheme = self._create_base_scheme(
            start_date="2026-06-01",
            last_date="2026-01-01",
        )
        res = DataValidator.validate_scheme(scheme)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("cannot be earlier than start_date" in e for e in res.errors))


if __name__ == "__main__":
    unittest.main()
