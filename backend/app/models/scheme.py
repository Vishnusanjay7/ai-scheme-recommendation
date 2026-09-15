"""
Scheme Models and Data Representations
---------------------------------------
Defines Pydantic models for raw incoming government scheme data,
normalized internal schemes, validation results, and API serialization.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl

from app.models.deadline import SchemeActivityInfo


class SchemeEligibilityData(BaseModel):
    """Structured deterministic eligibility criteria for a scheme."""
    min_age: Optional[int] = Field(default=None, ge=0, le=150)
    max_age: Optional[int] = Field(default=None, ge=0, le=150)
    max_income: Optional[float] = Field(default=None, ge=0)
    gender: Optional[str] = Field(default=None, description="'ALL', 'MALE', 'FEMALE', 'TRANSGENDER', 'OTHER'")
    occupation: Optional[str] = None
    education: Optional[str] = None
    category: Optional[str] = None
    disability_required: bool = False
    state_restriction: Optional[int] = None
    district_restriction: Optional[int] = None
    other_conditions: Dict[str, Any] = Field(default_factory=dict)


class SchemeDocumentData(BaseModel):
    """Required document specification for scheme application."""
    document_name: str
    mandatory: bool = True
    description: Optional[str] = None


class SchemeSourceData(BaseModel):
    """Provenance audit trail and source citation."""
    source_url: str
    source_type: Optional[str] = "OFFICIAL_PORTAL"
    last_checked: Optional[datetime] = None
    last_updated: Optional[datetime] = None


class RawScheme(BaseModel):
    """
    Normalized internal input representation of an official government scheme.
    Used by source adapters to hand off collected scheme data to the pipeline.
    Unknown/unprovided values remain None.
    """
    external_id: Optional[str] = None
    scheme_name: str
    description: Optional[str] = None
    government_level: str = "CENTRAL"  # Expected 'CENTRAL' or 'STATE'
    state: Optional[str] = None  # State name, code, or identifier
    category: Optional[str] = None  # Category name or identifier
    benefits: Optional[str] = None
    eligibility: Optional[SchemeEligibilityData] = None
    required_documents: Optional[List[SchemeDocumentData]] = None
    application_process: Optional[str] = None
    official_url: Optional[str] = None
    source_url: str
    start_date: Optional[str] = None
    last_date: Optional[str] = None
    status: str = "ACTIVE"
    last_updated: Optional[str] = None
    source_identifier: Optional[str] = None  # e.g., 'myscheme', 'data.gov.in'


class NormalizedScheme(BaseModel):
    """
    Validated, normalized internal representation ready for database persistence.
    """
    id: Optional[str] = None  # Database UUID if existing
    external_id: Optional[str] = None
    scheme_name: str
    description: Optional[str] = None
    government_level: str  # Strictly 'CENTRAL' or 'STATE'
    state_id: Optional[int] = None  # NULL for CENTRAL, valid foreign key for STATE
    state_name: Optional[str] = None
    category_id: Optional[int] = None  # Foreign key to scheme_categories
    category_name: Optional[str] = None
    benefits: Optional[str] = None
    application_process: Optional[str] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    last_date: Optional[str] = None  # YYYY-MM-DD
    status: str = "ACTIVE"  # 'ACTIVE', 'INACTIVE', 'EXPIRED'
    official_url: Optional[str] = None
    source_url: str
    source_identifier: Optional[str] = None
    last_updated: Optional[datetime] = None
    eligibility: Optional[SchemeEligibilityData] = None
    required_documents: List[SchemeDocumentData] = Field(default_factory=list)
    sources: List[SchemeSourceData] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Validation outcome for a scheme candidate."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# --- API Response Models ---

class SchemeItemResponse(BaseModel):
    """Summary representation of a scheme for API listing and search."""
    id: str
    scheme_name: str
    description: Optional[str] = None
    government_level: str
    state_id: Optional[int] = None
    category_id: Optional[int] = None
    benefits: Optional[str] = None
    application_process: Optional[str] = None
    start_date: Optional[str] = None
    last_date: Optional[str] = None
    status: str
    official_url: Optional[str] = None
    source_url: Optional[str] = None
    last_updated: Optional[str] = None
    created_at: Optional[str] = None
    activity: Optional[SchemeActivityInfo] = Field(
        default=None,
        description="Effective registration activity and deadline classification",
    )


class SchemeDetailResponse(SchemeItemResponse):
    """Comprehensive representation of a single scheme including nested relations."""
    eligibility: Optional[Dict[str, Any]] = None
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class SchemeListResponse(BaseModel):
    """Paginated collection of schemes."""
    total: int
    count: int
    offset: int
    limit: int
    data: List[SchemeItemResponse]
