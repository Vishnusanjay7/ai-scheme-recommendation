"""
Unit and Integration Tests: Deadline Monitoring & Notifications (Phase 8)
-------------------------------------------------------------------------
Comprehensive test matrix covering:
  1. Eligible saved scheme nearing deadline -> DEADLINE_APPROACHING notification created
  2. Eligible saved scheme urgent -> DEADLINE_URGENT notification created
  3. Eligible saved scheme closes today -> DEADLINE_TODAY notification created
  4. More than 15 days remaining -> no notification generated
  5. Scheme with no deadline (rolling) -> no notification generated
  6. Expired scheme -> no notification generated
  7. Inactive scheme -> no notification generated
  8. Not yet open scheme -> no notification generated
  9. Unknown activity scheme -> no notification generated
  10. NOT_ELIGIBLE scheme -> no notification generated
  11. POSSIBLY_ELIGIBLE scheme -> no notification generated
  12. Saved scheme does not equal eligibility (re-evaluated strictly against current profile)
  13. Duplicate monitor execution -> no duplicate notification created (idempotent)
  14. New deadline cycle -> new notification allowed
  15. Unauthenticated notification API calls rejected with 401
  16. Cross-user notification access rejected (403/404)
  17. Mark notification as read allowed only for owner
  18. Email provider mocked in unit tests
  19. Missing email configuration does not break in-app notification creation
  20. Email failure does not falsely mark notification as sent (remains PENDING)
  21. Scheme deleted / nonexistent -> safely skipped without crashing
  22. Monitoring script executes safely
"""

import os
import sys
import unittest
import uuid
from datetime import date, datetime, timedelta
from typing import Optional
from unittest.mock import MagicMock, patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import jwt
from fastapi.testclient import TestClient
from app.main import app
from app.integrations.email_service import EmailService
from app.models.deadline import ActivityStatus, DeadlineClassification, SchemeActivityInfo
from app.models.eligibility import EligibilityStatus, EligibilityExplanation
from app.models.notification import NotificationType
from app.services.deadline_service import IST
from app.services.notification_service import NotificationService


def _create_mock_jwt(user_id: str) -> str:
    """Generate mock JWT with 32+ byte key."""
    return jwt.encode({"sub": user_id}, "mock_secret_key_at_least_32_bytes_long_12345", algorithm="HS256")


class TestDeadlineMonitoring(unittest.TestCase):
    """Tests for NotificationService.check_saved_scheme_deadlines()."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_email = MagicMock(spec=EmailService)
        self.mock_email.is_configured.return_value = True
        self.mock_email.send_deadline_notification.return_value = True
        self.service = NotificationService(client=self.mock_client, email_service=self.mock_email)

        self.user_id = str(uuid.uuid4())
        self.scheme_id = str(uuid.uuid4())
        self.today = datetime.now(IST).date()

    def _setup_pipeline_mocks(
        self,
        days_offset: int,
        eligibility_status: EligibilityStatus,
        activity_status: ActivityStatus = ActivityStatus.OPEN,
        deadline_classification: Optional[DeadlineClassification] = None,
        has_last_date: bool = True,
        existing_notifications: list = None,
    ):
        """Helper to configure database and service mocks for a deadline monitoring run."""
        last_date = (self.today + timedelta(days=days_offset)).isoformat() if has_last_date else None

        # 1. Saved schemes mock
        mock_saved_table = MagicMock()
        mock_saved_table.select.return_value.execute.return_value.data = [
            {"user_id": self.user_id, "scheme_id": self.scheme_id}
        ]

        # 2. Schemes mock
        mock_schemes_table = MagicMock()
        mock_schemes_table.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": self.scheme_id,
                "name": "Kisan Credit Assistance",
                "status": "ACTIVE",
                "start_date": (self.today - timedelta(days=30)).isoformat(),
                "last_date": last_date,
                "official_url": "https://gov.in/kisan",
            }
        ]

        # 3. User profiles mock
        mock_profiles_table = MagicMock()
        mock_profiles_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {
                "user_id": self.user_id,
                "age": 35,
                "gender": "MALE",
                "state_id": 1,
                "district_id": 1,
                "annual_income": 80000.0,
                "occupation": "FARMER",
            }
        ]

        # 4. Scheme eligibility rules mock
        mock_elig_table = MagicMock()
        mock_elig_table.select.return_value.eq.return_value.execute.return_value.data = [
            {"scheme_id": self.scheme_id, "min_age": 18, "max_age": 60}
        ]

        # 5. Notifications mock (existing check and insert)
        mock_notif_table = MagicMock()
        mock_notif_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
            existing_notifications or []
        )
        mock_notif_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
            existing_notifications or []
        )
        mock_notif_table.insert.return_value.execute.return_value.data = [{"id": str(uuid.uuid4())}]
        mock_notif_table.update.return_value.eq.return_value.execute.return_value.data = []

        # 6. Users table mock (email)
        mock_users_table = MagicMock()
        mock_users_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"email": "citizen@example.com", "full_name": "Ramesh Kumar"}
        ]

        def table_router(table_name):
            if table_name == "saved_schemes":
                return mock_saved_table
            elif table_name == "schemes":
                return mock_schemes_table
            elif table_name == "user_profiles":
                return mock_profiles_table
            elif table_name == "scheme_eligibility":
                return mock_elig_table
            elif table_name == "notifications":
                return mock_notif_table
            elif table_name == "users":
                return mock_users_table
            return MagicMock()

        self.mock_client.table.side_effect = table_router
        return mock_notif_table

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_eligible_saved_scheme_approaching_creates_notification(self, mock_eval):
        """Case 1: Eligible saved scheme 12 days before deadline -> DEADLINE_APPROACHING created."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=12, eligibility_status=EligibilityStatus.ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 1)
        self.assertEqual(res.eligible_saved_schemes, 1)
        notif_table.insert.assert_called_once()
        inserted_row = notif_table.insert.call_args[0][0]
        self.assertEqual(inserted_row["notification_type"], NotificationType.DEADLINE_APPROACHING.value)
        self.assertIn("approaching", inserted_row["message"].lower())

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_eligible_saved_scheme_urgent_creates_urgent_notification(self, mock_eval):
        """Case 2: Eligible saved scheme 3 days before deadline -> DEADLINE_URGENT created."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=3, eligibility_status=EligibilityStatus.ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 1)
        inserted_row = notif_table.insert.call_args[0][0]
        self.assertEqual(inserted_row["notification_type"], NotificationType.DEADLINE_URGENT.value)
        self.assertIn("urgent", inserted_row["message"].lower())

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_eligible_saved_scheme_closing_today_creates_today_notification(self, mock_eval):
        """Case 3: Eligible saved scheme closing today -> DEADLINE_TODAY created."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=0, eligibility_status=EligibilityStatus.ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 1)
        inserted_row = notif_table.insert.call_args[0][0]
        self.assertEqual(inserted_row["notification_type"], NotificationType.DEADLINE_TODAY.value)
        self.assertIn("closes today", inserted_row["message"].lower())

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_more_than_15_days_no_notification(self, mock_eval):
        """Case 4: Deadline in 25 days -> normally no notification yet."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=25, eligibility_status=EligibilityStatus.ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_no_deadline_no_notification(self, mock_eval):
        """Case 5: Scheme with no closing deadline -> no notification."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(
            days_offset=0, eligibility_status=EligibilityStatus.ELIGIBLE, has_last_date=False
        )

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_expired_scheme_no_notification(self, mock_eval):
        """Case 6: Deadline in the past -> no notification."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=-5, eligibility_status=EligibilityStatus.ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_inactive_scheme_no_notification(self, mock_eval):
        """Case 7: Administratively INACTIVE scheme -> no notification."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=3, eligibility_status=EligibilityStatus.ELIGIBLE)
        # Override schemes status to INACTIVE
        self.mock_client.table("schemes").select.return_value.eq.return_value.execute.return_value.data = [
            {"id": self.scheme_id, "name": "Suspended Scheme", "status": "INACTIVE", "last_date": (self.today + timedelta(days=3)).isoformat()}
        ]

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_not_yet_open_scheme_no_notification(self, mock_eval):
        """Case 8: Registration starts in future -> no notification."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=10, eligibility_status=EligibilityStatus.ELIGIBLE)
        # Future start date
        self.mock_client.table("schemes").select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": self.scheme_id,
                "name": "Upcoming Program",
                "status": "ACTIVE",
                "start_date": (self.today + timedelta(days=5)).isoformat(),
                "last_date": (self.today + timedelta(days=10)).isoformat(),
            }
        ]

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_unknown_activity_no_notification(self, mock_eval):
        """Case 9: Invalid date range (last_date < start_date) -> no notification."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=3, eligibility_status=EligibilityStatus.ELIGIBLE)
        # Inverted dates
        self.mock_client.table("schemes").select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": self.scheme_id,
                "name": "Malformed Dates Scheme",
                "status": "ACTIVE",
                "start_date": (self.today + timedelta(days=10)).isoformat(),
                "last_date": (self.today + timedelta(days=3)).isoformat(),
            }
        ]

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_not_eligible_no_notification(self, mock_eval):
        """Case 10: Deterministic evaluation returns NOT_ELIGIBLE -> no notification."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.NOT_ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=3, eligibility_status=EligibilityStatus.NOT_ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_possibly_eligible_no_notification(self, mock_eval):
        """Case 11: Deterministic evaluation returns POSSIBLY_ELIGIBLE -> no notification."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.POSSIBLY_ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=3, eligibility_status=EligibilityStatus.POSSIBLY_ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_saved_scheme_does_not_equal_eligibility(self, mock_eval):
        """Case 12: A saved scheme is re-evaluated against the current profile before notification."""
        # Even though scheme is saved, citizen is currently NOT_ELIGIBLE (e.g. age/income changed)
        mock_eval.return_value = MagicMock(status=EligibilityStatus.NOT_ELIGIBLE)
        notif_table = self._setup_pipeline_mocks(days_offset=2, eligibility_status=EligibilityStatus.NOT_ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.eligible_saved_schemes, 0)
        self.assertEqual(res.notifications_created, 0)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_duplicate_monitor_execution_idempotent(self, mock_eval):
        """Case 13: Re-running deadline monitor does not create duplicate notifications."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        # Prior notification already exists for this cycle
        notif_table = self._setup_pipeline_mocks(
            days_offset=3,
            eligibility_status=EligibilityStatus.ELIGIBLE,
            existing_notifications=[{"id": "existing-notif-1"}],
        )

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        self.assertGreaterEqual(res.notifications_skipped, 1)
        notif_table.insert.assert_not_called()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_new_deadline_cycle_allows_new_notification(self, mock_eval):
        """Case 14: Scheme with a new deadline cycle (different scheduled_at) creates a new notification."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        # Empty existing for the new cycle
        notif_table = self._setup_pipeline_mocks(
            days_offset=2,
            eligibility_status=EligibilityStatus.ELIGIBLE,
            existing_notifications=[],
        )

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 1)
        notif_table.insert.assert_called_once()

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_missing_email_config_does_not_break_in_app(self, mock_eval):
        """Case 19: Unconfigured email service allows in-app notification to succeed with PENDING status."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        self.mock_email.is_configured.return_value = False
        self.mock_email.send_deadline_notification.return_value = False

        notif_table = self._setup_pipeline_mocks(days_offset=3, eligibility_status=EligibilityStatus.ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 1)
        inserted_row = notif_table.insert.call_args[0][0]
        self.assertEqual(inserted_row["status"], "PENDING")

    @patch("app.services.notification_service.evaluate_eligibility")
    def test_email_failure_does_not_falsely_mark_sent(self, mock_eval):
        """Case 20: If email dispatch fails, status remains PENDING and sent_at is not updated."""
        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        self.mock_email.is_configured.return_value = True
        self.mock_email.send_deadline_notification.return_value = False  # Failed delivery

        notif_table = self._setup_pipeline_mocks(days_offset=3, eligibility_status=EligibilityStatus.ELIGIBLE)

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 1)
        # notifications.update should NOT be called to set SENT
        notif_table.update.assert_not_called()

    def test_deleted_scheme_safely_skipped(self):
        """Case 21: Scheme deleted from schemes table is safely skipped without crashing."""
        mock_saved_table = MagicMock()
        mock_saved_table.select.return_value.execute.return_value.data = [
            {"user_id": self.user_id, "scheme_id": self.scheme_id}
        ]

        # Scheme query returns empty
        mock_schemes_table = MagicMock()
        mock_schemes_table.select.return_value.eq.return_value.execute.return_value.data = []

        def table_router(table_name):
            if table_name == "saved_schemes":
                return mock_saved_table
            if table_name == "schemes":
                return mock_schemes_table
            return MagicMock()

        self.mock_client.table.side_effect = table_router

        res = self.service.check_saved_scheme_deadlines()
        self.assertEqual(res.notifications_created, 0)
        self.assertEqual(res.notifications_skipped, 1)


class TestNotificationEndpoints(unittest.TestCase):
    """Integration tests for Notification API endpoints."""

    def setUp(self):
        self.client = TestClient(app)
        self.user_id = str(uuid.uuid4())
        self.auth_token = _create_mock_jwt(self.user_id)
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.notif_id = str(uuid.uuid4())

    def test_unauthenticated_requests_rejected_with_401(self):
        """Case 15: Unauthenticated access to all /api/notifications routes is rejected."""
        # 1. GET list
        res = self.client.get("/api/notifications")
        self.assertEqual(res.status_code, 401)

        # 2. GET unread
        res = self.client.get("/api/notifications/unread")
        self.assertEqual(res.status_code, 401)

        # 3. PATCH read
        res = self.client.patch(f"/api/notifications/{self.notif_id}/read")
        self.assertEqual(res.status_code, 401)

        # 4. PATCH read-all
        res = self.client.patch("/api/notifications/read-all")
        self.assertEqual(res.status_code, 401)

    @patch("app.routes.notification_routes.notification_service.mark_notification_as_read")
    def test_mark_notification_read_only_for_owner(self, mock_mark):
        """Case 17: Citizen marks their own notification as read."""
        from app.models.notification import NotificationActionResponse
        mock_mark.return_value = NotificationActionResponse(
            success=True, message="Marked as read.", notification_id=self.notif_id
        )

        res = self.client.patch(f"/api/notifications/{self.notif_id}/read", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        mock_mark.assert_called_once_with(notification_id=self.notif_id, user_id=self.user_id)

    def test_cross_user_notification_access_rejected(self):
        """Case 16: User A cannot modify or mark User B's notification as read."""
        user_b = str(uuid.uuid4())
        mock_supabase = MagicMock()
        # Mock DB returning notification owned by user_b
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": self.notif_id, "user_id": user_b}
        ]

        from fastapi import HTTPException
        service = NotificationService(client=mock_supabase)
        with self.assertRaises(HTTPException) as ctx:
            # Current user_id is NOT user_b
            service.mark_notification_as_read(notification_id=self.notif_id, user_id=self.user_id)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Access denied", ctx.exception.detail)


class TestCliMonitoringScript(unittest.TestCase):
    """Case 22: Tests verifying the CLI script backend/scripts/check_deadlines.py executes safely."""

    @patch("app.services.notification_service.NotificationService.check_saved_scheme_deadlines")
    def test_script_execution_safe(self, mock_check):
        from app.models.notification import DeadlineMonitoringResult
        from backend.scripts.check_deadlines import run_deadline_check

        mock_check.return_value = DeadlineMonitoringResult(
            users_checked=2,
            saved_schemes_checked=3,
            eligible_saved_schemes=1,
            notifications_created=1,
            notifications_skipped=2,
        )

        exit_code = run_deadline_check()
        self.assertEqual(exit_code, 0)
        mock_check.assert_called_once()


if __name__ == "__main__":
    unittest.main()
