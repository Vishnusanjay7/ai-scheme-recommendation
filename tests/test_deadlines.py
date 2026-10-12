"""
Unit and Integration Tests: Active/Open Registration and Deadline Engine (Phase 4)
--------------------------------------------------------------------------------
Comprehensive test matrix for:
  - Scheme activity determination (OPEN, NOT_YET_OPEN, EXPIRED, INACTIVE, UNKNOWN)
  - Deadline classification intervals (MORE_THAN_15_DAYS, APPROACHING, URGENT, CLOSING_TODAY, EXPIRED, NO_DEADLINE)
  - Inclusive last-date behavior (up to 23:59:59 IST)
  - Midnight start-date behavior (opens at 00:00:00 IST)
  - Invalid date ranges (start_date > last_date)
  - Timezone awareness (Asia/Kolkata / IST)
  - Status precedence rules (date overrides DB status, etc.)
  - API responses for /api/schemes/active and /api/schemes/{id}
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import MagicMock, patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.models.deadline import ActivityStatus, DeadlineClassification, SchemeActivityInfo
from app.services.deadline_service import (
    IST,
    calculate_days_remaining,
    classify_deadline,
    get_scheme_activity,
    is_scheme_actionable,
    is_scheme_active,
    parse_scheme_datetime,
)
from app.services.scheme_service import SchemeService


class TestActiveStatus(unittest.TestCase):
    """Tests for ActivityStatus determination."""

    def setUp(self):
        self.ref_now = datetime(2026, 9, 12, 12, 0, 0, tzinfo=IST)

    def test_future_start_date(self):
        """Scheme with future start_date -> NOT_YET_OPEN."""
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-09-20",
            "last_date": "2026-10-20",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.NOT_YET_OPEN)
        self.assertFalse(info.is_actionable)
        self.assertFalse(is_scheme_active(scheme, current_datetime=self.ref_now))
        self.assertFalse(is_scheme_actionable(scheme, current_datetime=self.ref_now))

    def test_past_start_date_and_future_last_date(self):
        """Scheme with past start_date and future last_date -> OPEN."""
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-09-01",
            "last_date": "2026-09-30",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.OPEN)
        self.assertTrue(info.is_actionable)
        self.assertTrue(is_scheme_active(scheme, current_datetime=self.ref_now))

    def test_past_last_date(self):
        """Scheme with past last_date -> EXPIRED."""
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-08-01",
            "last_date": "2026-09-10",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.EXPIRED)
        self.assertFalse(info.is_actionable)
        self.assertEqual(info.deadline_status, DeadlineClassification.EXPIRED)

    def test_no_dates_status_active(self):
        """Scheme with no dates, status='active' (backwards-compatible default) -> OPEN."""
        scheme = {
            "status": "ACTIVE",
            "start_date": None,
            "last_date": None,
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.OPEN)
        self.assertTrue(info.is_actionable)
        self.assertEqual(info.deadline_status, DeadlineClassification.NO_DEADLINE)
        self.assertIsNone(info.days_remaining)

    def test_no_deadline_with_explicit_application_evidence(self):
        """Scheme with NO_DEADLINE and explicit application instructions -> OPEN and actionable."""
        scheme = {
            "status": "ACTIVE",
            "start_date": None,
            "last_date": None,
            "application_process": "[Offline Mode]\n**Step 1:** Submit form at district office",
            "official_url": "https://tn.gov.in/scheme/123",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.OPEN)
        self.assertTrue(info.is_actionable)
        self.assertEqual(info.deadline_status, DeadlineClassification.NO_DEADLINE)

    def test_no_deadline_without_explicit_application_evidence(self):
        """Scheme with NO_DEADLINE and missing application evidence -> UNKNOWN and non-actionable."""
        scheme = {
            "status": "ACTIVE",
            "start_date": None,
            "last_date": None,
            "application_process": None,
            "official_url": None,
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.UNKNOWN)
        self.assertFalse(info.is_actionable)
        self.assertEqual(info.deadline_status, DeadlineClassification.NO_DEADLINE)
        self.assertIn("cannot be confirmed due to lack of application process", info.reason)

    def test_status_inactive(self):
        """Scheme with status='inactive' -> INACTIVE."""
        scheme = {
            "status": "inactive",
            "start_date": "2026-09-01",
            "last_date": "2026-09-30",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.INACTIVE)
        self.assertFalse(info.is_actionable)

    def test_status_closed(self):
        """Scheme with status='closed' -> INACTIVE."""
        scheme = {
            "status": "closed",
            "start_date": "2026-09-01",
            "last_date": "2026-09-30",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.INACTIVE)
        self.assertFalse(info.is_actionable)

    def test_status_expired(self):
        """Scheme with status='expired' -> EXPIRED."""
        scheme = {
            "status": "expired",
            "start_date": "2026-09-01",
            "last_date": "2026-09-30",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.EXPIRED)
        self.assertFalse(info.is_actionable)

    def test_status_active_but_past_last_date(self):
        """Scheme with status='active' but past last_date -> EXPIRED (date overrides status)."""
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-08-01",
            "last_date": "2026-09-11",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.EXPIRED)
        self.assertFalse(info.is_actionable)

    def test_status_active_but_future_start_date(self):
        """Scheme with status='active' but future start_date -> NOT_YET_OPEN (date overrides status)."""
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-09-15",
            "last_date": "2026-10-15",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.NOT_YET_OPEN)
        self.assertFalse(info.is_actionable)


class TestDeadlineIntervals(unittest.TestCase):
    """Tests for DeadlineClassification and days_remaining."""

    def setUp(self):
        self.ref_now = datetime(2026, 9, 12, 10, 0, 0, tzinfo=IST)

    def test_deadline_more_than_15_days(self):
        """Scheme with last_date 20 days away -> MORE_THAN_15_DAYS."""
        last_date = "2026-10-02"  # 20 days from Sep 12
        days = calculate_days_remaining(last_date, self.ref_now)
        self.assertEqual(days, 20)
        classification, calc_days, reason = classify_deadline(last_date, self.ref_now)
        self.assertEqual(classification, DeadlineClassification.MORE_THAN_15_DAYS)
        self.assertEqual(calc_days, 20)

    def test_deadline_15_days_away(self):
        """Scheme with last_date 15 days away -> APPROACHING (upper boundary)."""
        last_date = "2026-09-27"  # 15 days from Sep 12
        days = calculate_days_remaining(last_date, self.ref_now)
        self.assertEqual(days, 15)
        classification, calc_days, reason = classify_deadline(last_date, self.ref_now)
        self.assertEqual(classification, DeadlineClassification.APPROACHING)
        self.assertEqual(calc_days, 15)

    def test_deadline_8_days_away(self):
        """Scheme with last_date 8 days away -> APPROACHING (lower boundary)."""
        last_date = "2026-09-20"  # 8 days from Sep 12
        days = calculate_days_remaining(last_date, self.ref_now)
        self.assertEqual(days, 8)
        classification, calc_days, reason = classify_deadline(last_date, self.ref_now)
        self.assertEqual(classification, DeadlineClassification.APPROACHING)
        self.assertEqual(calc_days, 8)

    def test_deadline_7_days_away(self):
        """Scheme with last_date 7 days away -> URGENT (upper boundary)."""
        last_date = "2026-09-19"  # 7 days from Sep 12
        days = calculate_days_remaining(last_date, self.ref_now)
        self.assertEqual(days, 7)
        classification, calc_days, reason = classify_deadline(last_date, self.ref_now)
        self.assertEqual(classification, DeadlineClassification.URGENT)
        self.assertEqual(calc_days, 7)

    def test_deadline_3_days_away(self):
        """Scheme with last_date 3 days away -> URGENT."""
        last_date = "2026-09-15"  # 3 days from Sep 12
        days = calculate_days_remaining(last_date, self.ref_now)
        self.assertEqual(days, 3)
        classification, calc_days, reason = classify_deadline(last_date, self.ref_now)
        self.assertEqual(classification, DeadlineClassification.URGENT)
        self.assertEqual(calc_days, 3)

    def test_deadline_1_day_away(self):
        """Scheme with last_date 1 day away -> URGENT (lower boundary)."""
        last_date = "2026-09-13"  # 1 day from Sep 12
        days = calculate_days_remaining(last_date, self.ref_now)
        self.assertEqual(days, 1)
        classification, calc_days, reason = classify_deadline(last_date, self.ref_now)
        self.assertEqual(classification, DeadlineClassification.URGENT)
        self.assertEqual(calc_days, 1)

    def test_deadline_today(self):
        """Scheme with last_date today -> CLOSING_TODAY."""
        last_date = "2026-09-12"
        days = calculate_days_remaining(last_date, self.ref_now)
        self.assertEqual(days, 0)
        classification, calc_days, reason = classify_deadline(last_date, self.ref_now)
        self.assertEqual(classification, DeadlineClassification.CLOSING_TODAY)
        self.assertEqual(calc_days, 0)

    def test_deadline_yesterday(self):
        """Scheme with last_date yesterday -> EXPIRED."""
        last_date = "2026-09-11"
        days = calculate_days_remaining(last_date, self.ref_now)
        self.assertEqual(days, -1)
        classification, calc_days, reason = classify_deadline(last_date, self.ref_now)
        self.assertEqual(classification, DeadlineClassification.EXPIRED)
        self.assertEqual(calc_days, -1)

    def test_no_last_date(self):
        """Scheme with no last_date -> NO_DEADLINE."""
        days = calculate_days_remaining(None, self.ref_now)
        self.assertIsNone(days)
        classification, calc_days, reason = classify_deadline(None, self.ref_now)
        self.assertEqual(classification, DeadlineClassification.NO_DEADLINE)
        self.assertIsNone(calc_days)


class TestStartDateBehavior(unittest.TestCase):
    """Tests for start_date boundaries."""

    def setUp(self):
        self.ref_now = datetime(2026, 9, 12, 10, 0, 0, tzinfo=IST)

    def test_start_date_tomorrow(self):
        """start_date tomorrow -> NOT_YET_OPEN, 0 actionable."""
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-09-13",
            "last_date": "2026-09-30",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.NOT_YET_OPEN)
        self.assertFalse(info.is_actionable)

    def test_start_date_today(self):
        """start_date today -> OPEN (opens at midnight today)."""
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-09-12",
            "last_date": "2026-09-30",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.OPEN)
        self.assertTrue(info.is_actionable)

    def test_start_date_yesterday(self):
        """start_date yesterday -> OPEN."""
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-09-11",
            "last_date": "2026-09-30",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.OPEN)
        self.assertTrue(info.is_actionable)


class TestLastDateInclusive(unittest.TestCase):
    """Tests for inclusive last-date rule (valid until 23:59:59.999999 IST)."""

    def test_last_date_today_at_23_59(self):
        """last_date today at 23:59:00 IST -> still OPEN."""
        current_time = datetime(2026, 9, 12, 23, 59, 0, tzinfo=IST)
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-09-01",
            "last_date": "2026-09-12",
        }
        info = get_scheme_activity(scheme, current_datetime=current_time)
        self.assertEqual(info.status, ActivityStatus.OPEN)
        self.assertEqual(info.deadline_status, DeadlineClassification.CLOSING_TODAY)
        self.assertTrue(info.is_actionable)

    def test_last_date_yesterday_at_23_59_59(self):
        """last_date yesterday at 23:59:59 -> EXPIRED today at 00:00:01."""
        current_time = datetime(2026, 9, 13, 0, 0, 1, tzinfo=IST)
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-09-01",
            "last_date": "2026-09-12",
        }
        info = get_scheme_activity(scheme, current_datetime=current_time)
        self.assertEqual(info.status, ActivityStatus.EXPIRED)
        self.assertEqual(info.deadline_status, DeadlineClassification.EXPIRED)
        self.assertFalse(info.is_actionable)


class TestDateRangeValidation(unittest.TestCase):
    """Tests for invalid date ranges."""

    def test_start_date_after_last_date(self):
        """start_date > last_date -> UNKNOWN, reason explains invalid range."""
        current_time = datetime(2026, 9, 12, 12, 0, 0, tzinfo=IST)
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-10-01",
            "last_date": "2026-09-01",
        }
        info = get_scheme_activity(scheme, current_datetime=current_time)
        self.assertEqual(info.status, ActivityStatus.UNKNOWN)
        self.assertEqual(info.deadline_status, DeadlineClassification.UNKNOWN)
        self.assertFalse(info.is_actionable)
        self.assertIn("Invalid date range", info.reason)


class TestTimezoneHandling(unittest.TestCase):
    """Tests confirming strict Asia/Kolkata timezone handling."""

    def test_utc_conversion_boundary(self):
        """
        Scheme expiring on 2026-09-12 23:59:59 IST.
        In UTC, 23:59:59 IST corresponds to 18:29:59 UTC on 2026-09-12.
        At 19:00:00 UTC (00:30:00 IST on Sep 13), it should be expired.
        """
        utc_zone = ZoneInfo("UTC")

        # 18:00:00 UTC on Sep 12 is 23:30:00 IST on Sep 12 -> should be CLOSING_TODAY / OPEN
        current_utc_active = datetime(2026, 9, 12, 18, 0, 0, tzinfo=utc_zone)
        scheme = {
            "status": "ACTIVE",
            "start_date": "2026-09-01",
            "last_date": "2026-09-12",
        }
        info_active = get_scheme_activity(scheme, current_datetime=current_utc_active)
        self.assertEqual(info_active.status, ActivityStatus.OPEN)
        self.assertEqual(info_active.deadline_status, DeadlineClassification.CLOSING_TODAY)
        self.assertTrue(info_active.is_actionable)

        # 19:00:00 UTC on Sep 12 is 00:30:00 IST on Sep 13 -> should be EXPIRED
        current_utc_expired = datetime(2026, 9, 12, 19, 0, 0, tzinfo=utc_zone)
        info_expired = get_scheme_activity(scheme, current_datetime=current_utc_expired)
        self.assertEqual(info_expired.status, ActivityStatus.EXPIRED)
        self.assertEqual(info_expired.deadline_status, DeadlineClassification.EXPIRED)
        self.assertFalse(info_expired.is_actionable)


class TestStatusPrecedence(unittest.TestCase):
    """Tests for precedence order defined in Section 10."""

    def setUp(self):
        self.ref_now = datetime(2026, 9, 12, 12, 0, 0, tzinfo=IST)

    def test_precedence_invalid_range_over_everything(self):
        """Invalid date range takes precedence over DB status."""
        scheme = {
            "status": "inactive",
            "start_date": "2026-12-01",
            "last_date": "2026-11-01",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.UNKNOWN)

    def test_precedence_inactive_over_valid_dates(self):
        """Explicit inactive status overrides valid open dates."""
        scheme = {
            "status": "inactive",
            "start_date": "2026-09-01",
            "last_date": "2026-09-30",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.INACTIVE)

    def test_precedence_expired_db_status_over_future_date(self):
        """Explicit 'expired' DB status overrides future last_date."""
        scheme = {
            "status": "expired",
            "start_date": "2026-09-01",
            "last_date": "2026-09-30",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.EXPIRED)

    def test_precedence_future_start_date_over_active_status(self):
        """Future start_date overrides 'active' status."""
        scheme = {
            "status": "active",
            "start_date": "2026-09-20",
            "last_date": "2026-10-20",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.NOT_YET_OPEN)

    def test_precedence_past_last_date_over_active_status(self):
        """Past last_date overrides 'active' status."""
        scheme = {
            "status": "active",
            "start_date": "2026-08-01",
            "last_date": "2026-09-01",
        }
        info = get_scheme_activity(scheme, current_datetime=self.ref_now)
        self.assertEqual(info.status, ActivityStatus.EXPIRED)


class TestSchemeServiceActiveFiltering(unittest.TestCase):
    """Tests for SchemeService.get_active_schemes filtering."""

    @patch("app.services.scheme_service.get_supabase_client")
    def test_service_filters_actionable_only(self, mock_sb):
        """Verify get_active_schemes only returns schemes where is_actionable=True."""
        mock_client = MagicMock()
        mock_sb.return_value = mock_client

        # Mock database rows: one truly active, one past deadline but marked ACTIVE, one future
        rows = [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "scheme_name": "Truly Active Scheme",
                "government_level": "CENTRAL",
                "status": "ACTIVE",
                "start_date": "2026-09-01",
                "last_date": "2026-09-30",
                "source_url": "https://active.gov.in",
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "scheme_name": "Stale DB Active but Expired Date",
                "government_level": "CENTRAL",
                "status": "ACTIVE",
                "start_date": "2026-08-01",
                "last_date": "2026-08-31",
                "source_url": "https://expired.gov.in",
            },
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "scheme_name": "Future Start Scheme",
                "government_level": "CENTRAL",
                "status": "ACTIVE",
                "start_date": "2026-10-01",
                "last_date": "2026-10-31",
                "source_url": "https://future.gov.in",
            },
        ]

        # Setup mock chain
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=rows)

        service = SchemeService()
        result = service.get_active_schemes(current_datetime=datetime(2026, 9, 12, 12, 0, 0, tzinfo=IST))

        # Only row 1 should pass
        self.assertEqual(result.count, 1)
        self.assertEqual(result.data[0].id, "11111111-1111-1111-1111-111111111111")
        self.assertTrue(result.data[0].activity.is_actionable)
        self.assertEqual(result.data[0].activity.status, ActivityStatus.OPEN)


class TestSchemeAPIDeadlines(unittest.TestCase):
    """Tests for API endpoints returning activity and deadline data."""

    def setUp(self):
        self.client = TestClient(app)

    @patch("app.routes.schemes.scheme_service.get_active_schemes")
    def test_get_active_schemes_endpoint(self, mock_active):
        """Verify GET /api/schemes/active returns actionable schemes."""
        mock_active.return_value = {
            "total": 1,
            "count": 1,
            "offset": 0,
            "limit": 50,
            "data": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "scheme_name": "Active Scheme",
                    "government_level": "CENTRAL",
                    "status": "ACTIVE",
                    "start_date": "2026-09-01",
                    "last_date": "2026-09-30",
                    "source_url": "https://active.gov.in",
                    "activity": {
                        "status": "OPEN",
                        "deadline_status": "APPROACHING",
                        "days_remaining": 10,
                        "is_actionable": True,
                        "reason": "Registration is open (10 days remaining)",
                    },
                }
            ],
        }

        response = self.client.get("/api/schemes/active")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        item = data["data"][0]
        self.assertIn("activity", item)
        self.assertTrue(item["activity"]["is_actionable"])
        self.assertEqual(item["activity"]["status"], "OPEN")
        self.assertEqual(item["activity"]["deadline_status"], "APPROACHING")

    @patch("app.routes.schemes.scheme_service.get_scheme_by_id")
    def test_get_scheme_by_id_includes_activity(self, mock_get_by_id):
        """Verify GET /api/schemes/{id} returns deadline/activity information."""
        mock_get_by_id.return_value = {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "scheme_name": "Urgent Scholarship",
            "government_level": "CENTRAL",
            "status": "ACTIVE",
            "start_date": "2026-09-01",
            "last_date": "2026-09-15",
            "source_url": "https://scholarship.gov.in",
            "activity": {
                "status": "OPEN",
                "deadline_status": "URGENT",
                "days_remaining": 3,
                "is_actionable": True,
                "reason": "Registration is open and closing soon (3 days remaining)",
            },
        }

        response = self.client.get("/api/schemes/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("activity", data)
        self.assertEqual(data["activity"]["status"], "OPEN")
        self.assertEqual(data["activity"]["deadline_status"], "URGENT")
        self.assertEqual(data["activity"]["days_remaining"], 3)

    @patch("app.routes.schemes.scheme_service.get_scheme_by_id")
    def test_scheme_with_missing_dates_handled_gracefully(self, mock_get_by_id):
        """Verify schemes with missing dates return gracefully in API."""
        mock_get_by_id.return_value = {
            "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "scheme_name": "Ongoing Welfare Program",
            "government_level": "CENTRAL",
            "status": "ACTIVE",
            "start_date": None,
            "last_date": None,
            "source_url": "https://welfare.gov.in",
            "activity": {
                "status": "OPEN",
                "deadline_status": "NO_DEADLINE",
                "days_remaining": None,
                "is_actionable": True,
                "reason": "Ongoing scheme with no fixed deadline",
            },
        }

        response = self.client.get("/api/schemes/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("activity", data)
        self.assertEqual(data["activity"]["deadline_status"], "NO_DEADLINE")
        self.assertIsNone(data["activity"]["days_remaining"])
        self.assertTrue(data["activity"]["is_actionable"])


if __name__ == "__main__":
    unittest.main()
