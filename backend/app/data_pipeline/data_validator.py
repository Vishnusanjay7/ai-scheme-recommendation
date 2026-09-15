"""
Government Scheme Data Validator
--------------------------------
Implements strict validation rules for normalized scheme entities before
allowing persistence to the Supabase database:
  - Non-empty scheme title
  - Valid government level ('CENTRAL' | 'STATE')
  - Strict Central vs State relationship (state_id null for Central, present for State)
  - URL format and accessibility syntax validation
  - Date consistency checks (last_date >= start_date)
  - Status compliance ('ACTIVE', 'INACTIVE', 'EXPIRED')
  - Structured error reporting preventing corrupt or fabricated data insertion
"""

from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from app.models.scheme import NormalizedScheme, ValidationResult


class DataValidator:
    """
    Validates NormalizedScheme instances against government data integrity requirements.
    """

    ALLOWED_GOVERNMENT_LEVELS = {"CENTRAL", "STATE"}
    ALLOWED_STATUSES = {"ACTIVE", "INACTIVE", "EXPIRED"}

    @classmethod
    def is_valid_url(cls, url: Optional[str]) -> bool:
        """Verify URL has valid structure, scheme, and domain."""
        if not url:
            return False
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme in ("http", "https") and parsed.netloc and "." in parsed.netloc)
        except Exception:
            return False

    @classmethod
    def validate_scheme(cls, scheme: NormalizedScheme) -> ValidationResult:
        """
        Execute comprehensive validation on a normalized scheme candidate.
        Returns a ValidationResult with structured error messages.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Scheme Name Validation
        if not scheme.scheme_name or len(scheme.scheme_name.strip()) < 3:
            errors.append("Scheme name is missing or shorter than 3 characters.")

        # 2. Government Level Validation
        if scheme.government_level not in cls.ALLOWED_GOVERNMENT_LEVELS:
            errors.append(
                f"Invalid government level '{scheme.government_level}'. Must be 'CENTRAL' or 'STATE'."
            )

        # 3. Central vs State Relationship
        if scheme.government_level == "STATE":
            if scheme.state_id is None:
                errors.append("State scheme requires a valid state_id matching an Indian State or UT.")
        elif scheme.government_level == "CENTRAL":
            if scheme.state_id is not None:
                errors.append(
                    f"Central scheme must not be assigned a state_id (got {scheme.state_id}). Must be NULL."
                )

        # 4. URL Validation
        if not scheme.source_url:
            errors.append("Source URL is mandatory to maintain data provenance.")
        elif not cls.is_valid_url(scheme.source_url):
            errors.append(f"Invalid source URL format: '{scheme.source_url}'.")

        if scheme.official_url and not cls.is_valid_url(scheme.official_url):
            errors.append(f"Invalid official application URL format: '{scheme.official_url}'.")

        # 5. Date Validation
        if scheme.start_date and scheme.last_date:
            try:
                start_dt = datetime.strptime(scheme.start_date, "%Y-%m-%d")
                last_dt = datetime.strptime(scheme.last_date, "%Y-%m-%d")
                if last_dt < start_dt:
                    errors.append(
                        f"last_date ({scheme.last_date}) cannot be earlier than start_date ({scheme.start_date})."
                    )
            except ValueError as ve:
                errors.append(f"Invalid date format: {ve}")

        # 6. Status Validation
        if scheme.status not in cls.ALLOWED_STATUSES:
            errors.append(
                f"Invalid scheme status '{scheme.status}'. Must be one of {cls.ALLOWED_STATUSES}."
            )

        # 7. Warnings for incomplete but non-blocking metadata
        if not scheme.description:
            warnings.append("Scheme description is empty.")
        if not scheme.category_id:
            warnings.append("Scheme category could not be resolved to an official category.")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
