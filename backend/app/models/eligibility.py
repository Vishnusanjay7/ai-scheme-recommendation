"""
Deterministic Eligibility Engine Models
---------------------------------------
Defines schemas for citizen profiles, eligibility evaluation requests,
criterion results, and detailed explanations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class CriterionResult(str, Enum):
    """Three-state evaluation outcome for an individual criterion."""
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class EligibilityStatus(str, Enum):
    """Overall deterministic scheme eligibility status."""
    ELIGIBLE = "ELIGIBLE"
    POSSIBLY_ELIGIBLE = "POSSIBLY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


DISPLAY_STATUS_MAP = {
    EligibilityStatus.ELIGIBLE: "🟢 Eligible",
    EligibilityStatus.POSSIBLY_ELIGIBLE: "🟡 Possibly Eligible",
    EligibilityStatus.NOT_ELIGIBLE: "🔴 Not Eligible",
}


class UserProfileInput(BaseModel):
    """
    Standardized citizen demographic and socio-economic attributes.
    Mirrors the `user_profiles` schema. Unprovided attributes remain None.
    """
    user_id: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=0, le=150)
    gender: Optional[str] = None  # MALE, FEMALE, TRANSGENDER, OTHER
    state_id: Optional[int] = None
    state_name: Optional[str] = None
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    annual_income: Optional[float] = Field(default=None, ge=0)
    occupation: Optional[str] = None
    education: Optional[str] = None
    category: Optional[str] = None  # General, OBC, SC, ST, EWS
    disability_status: Optional[bool] = None
    family_details: Optional[Dict[str, Any]] = None


class CriterionEvaluation(BaseModel):
    """Detailed evaluation of a single eligibility criterion."""
    criterion: str
    result: CriterionResult
    user_value: Optional[Any] = None
    required: Optional[str] = None
    reason: str


class EligibilityExplanation(BaseModel):
    """
    Detailed, explainable evaluation output returned by the engine.
    Never uses match percentage to determine eligibility.
    """
    status: EligibilityStatus
    display_status: str
    summary: str
    criteria: List[CriterionEvaluation]
    passed_criteria_count: int
    failed_criteria_count: int
    unknown_criteria_count: int


class EligibilityEvaluationRequest(BaseModel):
    """
    API payload for evaluating scheme eligibility.
    Can reference an authenticated user_id or provide an in-memory profile.
    """
    scheme_id: str
    user_id: Optional[str] = None
    profile: Optional[UserProfileInput] = None


class EligibilityEvaluationResponse(BaseModel):
    """API response containing scheme info and detailed evaluation."""
    scheme_id: str
    scheme_name: Optional[str] = None
    government_level: Optional[str] = None
    evaluation: EligibilityExplanation


class BulkEligibilityResponse(BaseModel):
    """API response for bulk scheme evaluation."""
    total_evaluated: int
    eligible_count: int
    possibly_eligible_count: int
    not_eligible_count: int
    results: List[EligibilityEvaluationResponse]
