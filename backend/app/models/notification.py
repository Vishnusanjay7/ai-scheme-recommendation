"""
Notification Data Models
------------------------
Defines schemas, types, and responses for citizen deadline alerts and in-app notifications.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Supported citizen notification types for welfare scheme deadlines."""
    DEADLINE_APPROACHING = "DEADLINE_APPROACHING"
    DEADLINE_URGENT = "DEADLINE_URGENT"
    DEADLINE_TODAY = "DEADLINE_TODAY"


class NotificationStatus(str, Enum):
    """Delivery and lifecycle status of a notification."""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class NotificationResponse(BaseModel):
    """Representation of an in-app citizen notification."""
    id: str = Field(..., description="Unique notification UUID")
    user_id: str = Field(..., description="Recipient citizen auth.uid()")
    scheme_id: Optional[str] = Field(default=None, description="Referenced scheme ID")
    scheme_name: Optional[str] = Field(default=None, description="Name of referenced scheme")
    message: str = Field(..., description="Factual notification message")
    notification_type: str = Field(..., description="Type of alert (DEADLINE_APPROACHING, DEADLINE_URGENT, DEADLINE_TODAY)")
    scheduled_at: Optional[str] = Field(default=None, description="Associated deadline cycle ISO timestamp")
    sent_at: Optional[str] = Field(default=None, description="Timestamp when email delivery occurred")
    status: str = Field(default="PENDING", description="Delivery status (PENDING, SENT, FAILED, CANCELLED)")
    is_read: bool = Field(default=False, description="Whether notification has been marked read by citizen")
    created_at: str = Field(..., description="Creation timestamp")


class UnreadNotificationsResponse(BaseModel):
    """Summary of unread notifications for citizen dashboard / navbar badges."""
    unread_count: int = Field(..., description="Number of unread notifications")
    notifications: List[NotificationResponse] = Field(default_factory=list, description="List of unread notifications")


class NotificationActionResponse(BaseModel):
    """Result of marking a notification as read."""
    success: bool = Field(..., description="Whether the action succeeded")
    message: str = Field(..., description="Status description")
    notification_id: Optional[str] = Field(default=None, description="Target notification UUID")


class DeadlineMonitoringResult(BaseModel):
    """Summary statistics returned by deadline monitoring runner."""
    users_checked: int = Field(default=0, description="Total unique citizens evaluated")
    saved_schemes_checked: int = Field(default=0, description="Total saved schemes inspected")
    eligible_saved_schemes: int = Field(default=0, description="Saved schemes meeting strict current eligibility")
    notifications_created: int = Field(default=0, description="New in-app/email notifications generated")
    notifications_skipped: int = Field(default=0, description="Duplicate notifications or non-qualifying windows skipped")
