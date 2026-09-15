"""
Saved Scheme Data Models
------------------------
Defines request and response schemas for citizen bookmarking / saved welfare schemes.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SavedSchemeResponse(BaseModel):
    """Full detail of a saved scheme bookmark with live activity and deadline status."""
    id: str = Field(..., description="Unique ID of the saved bookmark record")
    user_id: str = Field(..., description="Citizen auth.uid() owner")
    scheme_id: str = Field(..., description="Referenced welfare scheme ID")
    saved_at: str = Field(..., description="Timestamp when scheme was bookmarked")
    scheme_name: str = Field(..., description="Official name of the scheme")
    benefits: Optional[str] = Field(default=None, description="Summary of welfare / financial benefits")
    government_level: Optional[str] = Field(default=None, description="'CENTRAL' or 'STATE'")
    state_id: Optional[int] = Field(default=None, description="State foreign key ID if state-specific")
    official_url: Optional[str] = Field(default=None, description="Official government portal application link")
    source_url: Optional[str] = Field(default=None, description="Source documentation URL")
    start_date: Optional[str] = Field(default=None, description="Registration opening date")
    last_date: Optional[str] = Field(default=None, description="Application closing deadline date")
    activity_status: str = Field(default="OPEN", description="Real-time activity status (OPEN, EXPIRED, NOT_YET_OPEN, INACTIVE)")
    deadline_status: Optional[str] = Field(default=None, description="Real-time deadline classification")
    days_remaining: Optional[int] = Field(default=None, description="Days remaining until deadline, if applicable")
    is_actionable: bool = Field(default=True, description="Whether registration is currently open and actionable")
    eligibility_status: Optional[str] = Field(default=None, description="Citizen eligibility status if previously evaluated")


class SavedSchemeStatusResponse(BaseModel):
    """Check whether a specific scheme is bookmarked by the current citizen."""
    saved: bool = Field(..., description="True if citizen has saved this scheme")
    saved_at: Optional[str] = Field(default=None, description="Timestamp when bookmarked, if saved")
    scheme_id: str = Field(..., description="Scheme UUID")


class SaveSchemeActionResponse(BaseModel):
    """Result of saving or removing a scheme."""
    status: str = Field(..., description="'saved', 'already_saved', or 'removed'")
    message: str = Field(..., description="Human-readable status message")
    saved: bool = Field(..., description="Current bookmark state")
    scheme_id: str = Field(..., description="Scheme UUID")
