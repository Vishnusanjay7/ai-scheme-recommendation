"""
Notification API Endpoints
--------------------------
Provides authenticated citizen access to in-app notifications and deadline alerts:
  - GET   /api/notifications                  (List notifications for authenticated citizen)
  - GET   /api/notifications/unread           (Get unread count and list of unread alerts)
  - PATCH /api/notifications/{id}/read        (Mark a single notification as read)
  - PATCH /api/notifications/read-all         (Mark all citizen notifications as read)
  - POST  /api/notifications/check-deadlines  (Trigger deadline monitoring evaluation)

SECURITY INVARIANTS:
1. Citizen identity is derived strictly from verified JWT claims (auth.uid()).
2. Client-provided user_id is never accepted.
3. Cross-user notification access or modification is rejected.
4. Unauthenticated requests are rejected with 401 Unauthorized.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.notification import (
    DeadlineMonitoringResult,
    NotificationActionResponse,
    NotificationResponse,
    UnreadNotificationsResponse,
)
from app.services.notification_service import NotificationService
from app.utils.auth import get_authenticated_user_id

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])
notification_service = NotificationService()


def _require_auth_user(auth_user_id: Optional[str] = Depends(get_authenticated_user_id)) -> str:
    """Validate authenticated session and extract citizen UUID."""
    if not auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access notifications.",
        )
    return auth_user_id


@router.get(
    "",
    response_model=List[NotificationResponse],
    summary="List citizen notifications",
    description="Retrieve chronological list of in-app notifications for the calling citizen.",
)
def get_notifications(
    limit: int = Query(default=50, ge=1, le=100, description="Max notifications to retrieve"),
    user_id: str = Depends(_require_auth_user),
):
    return notification_service.get_user_notifications(user_id=user_id, unread_only=False, limit=limit)


@router.get(
    "/unread",
    response_model=UnreadNotificationsResponse,
    summary="Get unread notifications summary",
    description="Retrieve count of unread alerts and list of unread notifications for navbar badges and dashboard widgets.",
)
def get_unread_notifications(
    user_id: str = Depends(_require_auth_user),
):
    return notification_service.get_unread_summary(user_id=user_id)


@router.patch(
    "/read-all",
    response_model=NotificationActionResponse,
    summary="Mark all notifications as read",
    description="Mark all unread notifications for the calling citizen as read.",
)
def mark_all_notifications_read(
    user_id: str = Depends(_require_auth_user),
):
    return notification_service.mark_all_as_read(user_id=user_id)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationActionResponse,
    summary="Mark notification as read",
    description="Mark a single notification as read. Fails with 403/404 if notification does not belong to calling citizen.",
)
def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(_require_auth_user),
):
    return notification_service.mark_notification_as_read(notification_id=notification_id, user_id=user_id)


@router.post(
    "/check-deadlines",
    response_model=DeadlineMonitoringResult,
    summary="Trigger deadline monitoring check",
    description="Execute the periodic deadline evaluation job. Re-evaluates eligibility and deadlines for all saved schemes.",
)
def trigger_deadline_monitoring(
    user_id: str = Depends(_require_auth_user),
):
    """
    Authenticated trigger for deadline monitoring.
    Re-evaluates saved schemes against active deadline windows.
    """
    return notification_service.check_saved_scheme_deadlines()
