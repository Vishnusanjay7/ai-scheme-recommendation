"""
Scheme Registration Activity and Deadline Models
------------------------------------------------
Defines enums and structured representations for scheme registration status,
deadline classifications, remaining days, and actionability metadata.
Decouples application activity from deterministic citizen eligibility.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ActivityStatus(str, Enum):
    """
    Deterministic registration activity status for a welfare scheme.
    Indicates whether a citizen can currently apply.
    """
    OPEN = "OPEN"
    NOT_YET_OPEN = "NOT_YET_OPEN"
    EXPIRED = "EXPIRED"
    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"


class DeadlineClassification(str, Enum):
    """
    Standardized classification of time remaining before application deadline.
    Computed deterministically using Indian Standard Time (Asia/Kolkata).
    """
    MORE_THAN_15_DAYS = "MORE_THAN_15_DAYS"  # >15 calendar days
    APPROACHING = "APPROACHING"              # 8–15 calendar days
    URGENT = "URGENT"                        # 1–7 calendar days
    CLOSING_TODAY = "CLOSING_TODAY"          # 0 days (valid through end of calendar day)
    EXPIRED = "EXPIRED"                      # Deadline has passed
    NO_DEADLINE = "NO_DEADLINE"              # Scheme has no statutory closing date (last_date is NULL)
    UNKNOWN = "UNKNOWN"                      # Cannot be determined or date format is invalid


class SchemeActivityInfo(BaseModel):
    """
    Comprehensive activity and deadline metadata for a scheme.
    Can be nested in scheme lists, search results, and scheme detail views.
    """
    status: ActivityStatus = Field(
        ...,
        description="Effective activity status (OPEN, NOT_YET_OPEN, EXPIRED, INACTIVE, UNKNOWN)",
    )
    deadline_status: DeadlineClassification = Field(
        ...,
        description="Deadline classification based on days remaining in IST",
    )
    days_remaining: Optional[int] = Field(
        default=None,
        description="Calendar days remaining until application deadline in Asia/Kolkata timezone",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Registration opening date (YYYY-MM-DD)",
    )
    last_date: Optional[str] = Field(
        default=None,
        description="Registration closing date (YYYY-MM-DD)",
    )
    is_actionable: bool = Field(
        default=False,
        description="True if scheme is currently OPEN and deadline has not expired",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Deterministic explanation of the activity and deadline evaluation",
    )
