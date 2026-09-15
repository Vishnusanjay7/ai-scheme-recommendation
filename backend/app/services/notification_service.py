"""
Notification & Deadline Monitoring Service
-------------------------------------------
Implements citizen notification management and periodic deadline monitoring:
  - Fetches in-app notifications for authenticated citizens (enforcing auth.uid() isolation).
  - Marks individual and bulk notifications as read.
  - Periodic deadline monitoring:
      1. Inspects saved schemes.
      2. Re-evaluates current deterministic eligibility (strictly ELIGIBLE required).
      3. Evaluates current activity (strictly OPEN and within deadline window: CLOSING_TODAY, URGENT, APPROACHING).
      4. Idempotently skips already-sent notifications for the active deadline cycle.
      5. Creates in-app notifications and attempts email delivery.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from fastapi import HTTPException, status

from app.integrations.email_service import EmailService
from app.integrations.supabase_client import get_supabase_client
from app.models.deadline import ActivityStatus, DeadlineClassification
from app.models.eligibility import EligibilityStatus, UserProfileInput
from app.models.notification import (
    DeadlineMonitoringResult,
    NotificationActionResponse,
    NotificationResponse,
    NotificationType,
    UnreadNotificationsResponse,
)
from app.services.deadline_service import get_scheme_activity, parse_scheme_datetime, IST
from app.services.eligibility_engine import evaluate_eligibility

logger = logging.getLogger("notifications")


class NotificationService:
    """Service handling citizen notifications and scheduled deadline checks."""

    def __init__(self, client=None, email_service: Optional[EmailService] = None):
        self._client = client
        self._email_service = email_service or EmailService()

    def get_client(self):
        return self._client if self._client is not None else get_supabase_client()

    def _validate_uuid(self, val: str, field_name: str = "ID") -> str:
        try:
            return str(uuid.UUID(str(val)))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} format: '{val}'. Expected valid UUID.",
            )

    def get_user_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50
    ) -> List[NotificationResponse]:
        """Fetch notifications belonging strictly to the authenticated citizen."""
        u_id = self._validate_uuid(user_id, "user_id")
        client = self.get_client()

        query = (
            client.table("notifications")
            .select("*")
            .eq("user_id", u_id)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if unread_only:
            query = query.eq("is_read", False)

        res = query.execute()
        rows = res.data or []
        if not rows:
            return []

        # Enrich with scheme names if present
        results: List[NotificationResponse] = []
        for r in rows:
            scheme_name = None
            if r.get("scheme_id"):
                s_res = client.table("schemes").select("name").eq("id", r["scheme_id"]).execute()
                if s_res.data:
                    scheme_name = s_res.data[0].get("name")

            results.append(
                NotificationResponse(
                    id=str(r["id"]),
                    user_id=str(r["user_id"]),
                    scheme_id=str(r["scheme_id"]) if r.get("scheme_id") else None,
                    scheme_name=scheme_name,
                    message=r["message"],
                    notification_type=r["notification_type"],
                    scheduled_at=str(r["scheduled_at"]) if r.get("scheduled_at") else None,
                    sent_at=str(r["sent_at"]) if r.get("sent_at") else None,
                    status=r.get("status", "PENDING"),
                    is_read=bool(r.get("is_read", False)),
                    created_at=str(r["created_at"]),
                )
            )
        return results

    def get_unread_summary(self, user_id: str) -> UnreadNotificationsResponse:
        """Fetch unread count and latest unread notifications."""
        notifications = self.get_user_notifications(user_id=user_id, unread_only=True)
        return UnreadNotificationsResponse(
            unread_count=len(notifications),
            notifications=notifications,
        )

    def mark_notification_as_read(self, notification_id: str, user_id: str) -> NotificationActionResponse:
        """
        Mark an individual notification as read.
        Enforces ownership: user can ONLY mark their own notification.
        """
        n_id = self._validate_uuid(notification_id, "notification_id")
        u_id = self._validate_uuid(user_id, "user_id")
        client = self.get_client()

        # 1. Verify existence and ownership
        check = (
            client.table("notifications")
            .select("id, user_id")
            .eq("id", n_id)
            .execute()
        )
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification with ID '{n_id}' not found.",
            )

        row = check.data[0]
        if str(row["user_id"]) != u_id:
            # Cross-user modification forbidden
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to modify this notification.",
            )

        # 2. Update is_read
        client.table("notifications").update({"is_read": True}).eq("id", n_id).execute()

        return NotificationActionResponse(
            success=True,
            message="Notification marked as read.",
            notification_id=n_id,
        )

    def mark_all_as_read(self, user_id: str) -> NotificationActionResponse:
        """Mark all unread notifications as read for the authenticated citizen."""
        u_id = self._validate_uuid(user_id, "user_id")
        client = self.get_client()

        client.table("notifications").update({"is_read": True}).eq("user_id", u_id).eq("is_read", False).execute()

        return NotificationActionResponse(
            success=True,
            message="All notifications successfully marked as read.",
        )

    def check_saved_scheme_deadlines(self) -> DeadlineMonitoringResult:
        """
        Comprehensive deadline monitoring execution:
          1. Find all saved schemes from saved_schemes.
          2. Inspect active deadlines and current eligibility.
          3. Generate deadline alerts if criteria are met.
          4. Prevent duplicate notifications for the same deadline cycle.
        """
        client = self.get_client()

        # 1. Fetch all saved schemes
        saved_res = client.table("saved_schemes").select("user_id, scheme_id").execute()
        saved_rows = saved_res.data or []

        if not saved_rows:
            logger.info("Deadline monitor: zero saved schemes found.")
            return DeadlineMonitoringResult(
                users_checked=0,
                saved_schemes_checked=0,
                eligible_saved_schemes=0,
                notifications_created=0,
                notifications_skipped=0,
            )

        unique_users = set(r["user_id"] for r in saved_rows)
        users_checked = len(unique_users)
        saved_schemes_checked = len(saved_rows)
        eligible_saved_schemes = 0
        notifications_created = 0
        notifications_skipped = 0

        # Cache citizen profiles and users to avoid redundant queries
        profiles_cache: Dict[str, Optional[UserProfileInput]] = {}
        users_cache: Dict[str, Dict[str, Any]] = {}

        for item in saved_rows:
            u_id = item["user_id"]
            s_id = item["scheme_id"]

            # Fetch scheme record
            scheme_res = client.table("schemes").select("*").eq("id", s_id).execute()
            if not scheme_res.data:
                # Scheme deleted or nonexistent
                notifications_skipped += 1
                continue

            scheme = scheme_res.data[0]
            scheme_name = scheme.get("name") or "Government Welfare Scheme"

            # 2. Evaluate scheme activity and deadline
            activity = get_scheme_activity(scheme)

            # Skip if not currently open or not actionable
            if activity.status != ActivityStatus.OPEN:
                notifications_skipped += 1
                continue

            # Skip if no statutory closing deadline
            if (
                activity.days_remaining is None
                or activity.deadline_status == DeadlineClassification.NO_DEADLINE
                or activity.deadline_status == DeadlineClassification.UNKNOWN
            ):
                notifications_skipped += 1
                continue

            # Classify notification window
            notif_type: Optional[NotificationType] = None
            if activity.deadline_status == DeadlineClassification.CLOSING_TODAY:
                notif_type = NotificationType.DEADLINE_TODAY
            elif activity.deadline_status == DeadlineClassification.URGENT:
                notif_type = NotificationType.DEADLINE_URGENT
            elif activity.deadline_status == DeadlineClassification.APPROACHING:
                notif_type = NotificationType.DEADLINE_APPROACHING
            else:
                # e.g. MORE_THAN_15_DAYS or EXPIRED
                notifications_skipped += 1
                continue

            # 3. Retrieve citizen profile and evaluate CURRENT eligibility
            if u_id not in profiles_cache:
                p_res = client.table("user_profiles").select("*").eq("user_id", u_id).limit(1).execute()
                if p_res.data:
                    p_row = p_res.data[0]
                    profiles_cache[u_id] = UserProfileInput(
                        user_id=p_row.get("user_id"),
                        age=p_row.get("age"),
                        gender=p_row.get("gender"),
                        state_id=p_row.get("state_id"),
                        district_id=p_row.get("district_id"),
                        annual_income=float(p_row["annual_income"]) if p_row.get("annual_income") is not None else None,
                        occupation=p_row.get("occupation"),
                        education=p_row.get("education"),
                        category=p_row.get("category"),
                        disability_status=p_row.get("disability_status"),
                    )
                else:
                    profiles_cache[u_id] = None

            citizen_profile = profiles_cache[u_id]
            if not citizen_profile:
                # No profile configured for citizen
                notifications_skipped += 1
                continue

            # Fetch scheme eligibility rules
            elig_res = client.table("scheme_eligibility").select("*").eq("scheme_id", s_id).execute()
            elig_rules = elig_res.data[0] if elig_res.data else {}

            # Execute pure deterministic eligibility evaluation
            eval_res = evaluate_eligibility(
                profile=citizen_profile,
                scheme=scheme,
                eligibility_rules=elig_rules,
            )

            # Strict requirement: ONLY ELIGIBLE generates notifications
            if eval_res.status != EligibilityStatus.ELIGIBLE:
                notifications_skipped += 1
                continue

            eligible_saved_schemes += 1

            # 4. Determine deadline cycle timestamp for idempotency
            deadline_dt = parse_scheme_datetime(scheme.get("last_date"), is_end_of_day=True, tz=IST)
            scheduled_at_iso = deadline_dt.isoformat() if deadline_dt else None

            # 5. Duplicate notification check (Idempotency)
            # Check if identical alert already exists for this citizen, scheme, type, and deadline cycle
            existing_query = (
                client.table("notifications")
                .select("id, scheduled_at")
                .eq("user_id", u_id)
                .eq("scheme_id", s_id)
                .eq("notification_type", notif_type.value)
            )
            if scheduled_at_iso:
                existing_query = existing_query.eq("scheduled_at", scheduled_at_iso)

            existing_notif = existing_query.execute()
            if existing_notif.data:
                # Already generated for this deadline cycle
                notifications_skipped += 1
                continue

            # 6. Construct factual notification message
            if notif_type == NotificationType.DEADLINE_TODAY:
                msg = f"Your saved scheme '{scheme_name}' closes today. Apply through the official government portal."
            elif notif_type == NotificationType.DEADLINE_URGENT:
                msg = f"Your saved scheme '{scheme_name}' has an urgent application deadline. {activity.days_remaining} day(s) remaining."
            else:
                msg = f"Your saved scheme '{scheme_name}' is approaching its application deadline. {activity.days_remaining} days remaining."

            # 7. Insert in-app notification
            new_notif_row = {
                "user_id": u_id,
                "scheme_id": s_id,
                "message": msg,
                "notification_type": notif_type.value,
                "scheduled_at": scheduled_at_iso,
                "status": "PENDING",
                "is_read": False,
            }

            try:
                insert_res = client.table("notifications").insert(new_notif_row).execute()
                notif_id = insert_res.data[0]["id"] if insert_res.data else None
            except Exception as exc:
                logger.error(f"Failed to insert notification: {str(exc)}")
                notifications_skipped += 1
                continue

            # 8. Attempt email delivery
            if u_id not in users_cache:
                u_res = client.table("users").select("email, full_name").eq("id", u_id).limit(1).execute()
                users_cache[u_id] = u_res.data[0] if u_res.data else {}

            user_row = users_cache[u_id]
            user_email = user_row.get("email")
            user_name = user_row.get("full_name") or "Citizen"

            if user_email and not user_email.endswith("@citizen.local"):
                email_sent = self._email_service.send_deadline_notification(
                    to_email=user_email,
                    citizen_name=user_name,
                    scheme_name=scheme_name,
                    notification_type=notif_type.value,
                    days_remaining=activity.days_remaining or 0,
                    official_url=scheme.get("official_url"),
                )
                if email_sent and notif_id:
                    now_utc = datetime.now(timezone.utc).isoformat()
                    try:
                        client.table("notifications").update({
                            "status": "SENT",
                            "sent_at": now_utc,
                        }).eq("id", notif_id).execute()
                    except Exception:
                        pass

            notifications_created += 1

        logger.info(
            f"Deadline monitor finished: {users_checked} users, {saved_schemes_checked} saved schemes, "
            f"{eligible_saved_schemes} eligible, {notifications_created} created, {notifications_skipped} skipped."
        )

        return DeadlineMonitoringResult(
            users_checked=users_checked,
            saved_schemes_checked=saved_schemes_checked,
            eligible_saved_schemes=eligible_saved_schemes,
            notifications_created=notifications_created,
            notifications_skipped=notifications_skipped,
        )
