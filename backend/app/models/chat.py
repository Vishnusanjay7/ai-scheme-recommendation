"""
Chat & NLP Assistant Data Models
--------------------------------
Defines request and response schemas for natural language interaction,
entity extraction, conversational scheme recommendations, and chat history.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.models.recommendation import (
    RecommendationItem,
    VerificationRequiredItem,
)


class ChatIntent(BaseModel):
    """Structured intent and demographic entities extracted from user natural language query."""
    intent: str = Field(default="find_schemes", description="Classified intent (find_schemes, eligibility_query, greeting, general_inquiry)")
    query: Optional[str] = Field(default=None, description="Cleaned search query text")
    language: str = Field(default="en", description="Detected language code ('en', 'ta')")
    age: Optional[int] = Field(default=None, ge=0, le=150, description="Explicitly stated age in years")
    gender: Optional[str] = Field(default=None, description="Explicitly stated gender (MALE, FEMALE, TRANSGENDER, OTHER)")
    state_id: Optional[int] = Field(default=None, description="Referenced state ID")
    state_name: Optional[str] = Field(default=None, description="Explicitly mentioned state name")
    district_id: Optional[int] = Field(default=None, description="Referenced district ID")
    district_name: Optional[str] = Field(default=None, description="Explicitly mentioned district name")
    annual_income: Optional[float] = Field(default=None, ge=0, description="Explicitly stated annual household income")
    occupation: Optional[str] = Field(default=None, description="Explicitly stated occupation (e.g., FARMER, STUDENT, ARTISAN)")
    education: Optional[str] = Field(default=None, description="Explicitly stated educational qualification")
    category: Optional[str] = Field(default=None, description="Explicitly stated social category (SC, ST, OBC, GENERAL)")
    disability_status: Optional[bool] = Field(default=None, description="Explicitly mentioned disability status")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords describing needs or scheme domains")


class ChatMessageRequest(BaseModel):
    """Incoming user chat query."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language question or request from the citizen in English or Tamil",
    )
    language: Optional[str] = Field(
        default=None,
        description="Optional preferred response language override ('en' or 'ta')",
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty or whitespace only.")
        return cleaned


class ChatMessageResponse(BaseModel):
    """Structured assistant response grounded in deterministic eligibility."""
    message: str = Field(..., description="Conversational natural-language response for the citizen")
    language: str = Field(default="en", description="Language of response ('en' or 'ta')")
    intent: Optional[ChatIntent] = Field(default=None, description="Extracted structured intent and entities")
    recommendations: List[RecommendationItem] = Field(
        default_factory=list,
        description="Deterministically ELIGIBLE and OPEN scheme recommendations",
    )
    verification_required: List[VerificationRequiredItem] = Field(
        default_factory=list,
        description="Schemes requiring demographic verification",
    )
    total_eligible_found: int = Field(default=0, description="Count of eligible schemes discovered")


class ChatHistoryItem(BaseModel):
    """A single stored conversational turn."""
    id: str = Field(..., description="UUID of chat interaction record")
    user_id: str = Field(..., description="Authenticated citizen owner UUID")
    user_message: str = Field(..., description="User message text")
    bot_response: str = Field(..., description="Assistant response text")
    language: str = Field(default="en", description="Language code")
    created_at: str = Field(..., description="Interaction timestamp")


class ChatHistoryResponse(BaseModel):
    """List of recent chat history items for authenticated citizen."""
    user_id: Optional[str] = Field(default=None, description="Authenticated citizen UUID")
    total_messages: int = Field(default=0, description="Total history turns retrieved")
    history: List[ChatHistoryItem] = Field(default_factory=list, description="Chronological chat history records")

