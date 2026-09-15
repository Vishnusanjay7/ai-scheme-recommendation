"""
AI Recommendation Engine Models
-------------------------------
Defines response models, request payloads, and structured AI output schemas
for multi-factor relevance ranking.

ARCHITECTURAL PRINCIPLE:
Relevance score (0–100) is strictly distinct from legal eligibility status.
Eligibility is determined exclusively by the Phase 3 Deterministic Engine.
Relevance indicates how well an already-eligible and active scheme matches
a citizen's profile, stated intent, and urgency.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.deadline import ActivityStatus, DeadlineClassification
from app.models.eligibility import EligibilityStatus, UserProfileInput


class AIRankedItem(BaseModel):
    """Structured AI output item produced by LLM."""
    scheme_id: str = Field(..., description="UUID of the candidate scheme")
    relevance_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Relevance match score (0-100). NOT an eligibility percentage.",
    )
    reason: str = Field(
        ...,
        description="Concise explanation of why this scheme matches the citizen's profile and needs",
    )


class AIRankingOutput(BaseModel):
    """Top-level structured output expected from OpenAI."""
    ranked_schemes: List[AIRankedItem] = Field(
        default_factory=list,
        description="Ordered list of candidate schemes ranked by relevance",
    )


class RecommendationItem(BaseModel):
    """
    A single recommended government welfare scheme.
    Guaranteed to be deterministically ELIGIBLE and currently OPEN.
    """
    scheme_id: str
    scheme_name: str
    eligibility_status: EligibilityStatus = Field(
        default=EligibilityStatus.ELIGIBLE,
        description="Deterministic eligibility result (strictly ELIGIBLE for main recommendations)",
    )
    relevance_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Relevance match score (0–100). Indicates priority/fit, not legal eligibility.",
    )
    relevance_reason: str = Field(
        ...,
        description="Transparent justification for the relevance match score",
    )
    activity_status: ActivityStatus = Field(
        default=ActivityStatus.OPEN,
        description="Current application activity status (strictly OPEN)",
    )
    deadline_status: DeadlineClassification = Field(
        ...,
        description="Application deadline urgency classification",
    )
    days_remaining: Optional[int] = Field(
        default=None,
        description="Calendar days remaining until application deadline in Asia/Kolkata timezone",
    )
    benefits: Optional[str] = None
    official_url: Optional[str] = None
    government_level: Optional[str] = None
    state_id: Optional[int] = None
    category_name: Optional[str] = None


class VerificationRequiredItem(BaseModel):
    """
    Scheme where the citizen is POSSIBLY_ELIGIBLE (missing/unverified criteria).
    Excluded from main recommendations to prevent false qualification guarantees.
    """
    scheme_id: str
    scheme_name: str
    eligibility_status: EligibilityStatus = Field(
        default=EligibilityStatus.POSSIBLY_ELIGIBLE,
        description="Deterministic eligibility status (POSSIBLY_ELIGIBLE)",
    )
    status_label: str = Field(
        default="Eligibility needs verification",
        description="Explicit notice that user must verify missing criteria before applying",
    )
    relevance_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Relevance match score (0–100)",
    )
    relevance_reason: str
    activity_status: ActivityStatus
    deadline_status: DeadlineClassification
    days_remaining: Optional[int] = None
    benefits: Optional[str] = None
    official_url: Optional[str] = None
    government_level: Optional[str] = None
    state_id: Optional[int] = None
    missing_criteria: List[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    """
    Request payload for AI scheme recommendations.
    Accepts optional natural-language query to guide ranking relevance.
    """
    query: Optional[str] = Field(
        default=None,
        description="Optional natural-language description of needs (e.g. 'farmer looking for loan assistance')",
    )
    limit: int = Field(default=50, ge=1, le=100, description="Max recommendations to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    user_id: Optional[str] = Field(
        default=None,
        description="Optional user ID for client identity tracking. Validated server-side against auth.uid()",
    )
    profile: Optional[UserProfileInput] = Field(
        default=None,
        description="Guest/in-memory demographic profile. Prohibited for authenticated sessions",
    )


class RecommendationResponse(BaseModel):
    """Complete recommendation API response payload."""
    recommendations: List[RecommendationItem] = Field(
        ...,
        description="Ranked list of verified ELIGIBLE and OPEN schemes",
    )
    verification_required: List[VerificationRequiredItem] = Field(
        default_factory=list,
        description="Schemes that are active but require user profile verification (POSSIBLY_ELIGIBLE)",
    )
    total_candidates: int = Field(
        ...,
        description="Total number of eligible and open candidates evaluated",
    )
    ranking_method: str = Field(
        ...,
        description="'OPENAI' if ranked by LLM, 'DETERMINISTIC_FALLBACK' if ranked by deterministic rules",
    )
    query_used: Optional[str] = Field(
        default=None,
        description="Natural-language query used for relevance contextualization",
    )
