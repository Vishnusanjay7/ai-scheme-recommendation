"""
Government Scheme Data Processor & Normalizer
----------------------------------------------
Implements robust, deterministic normalization routines for all incoming
scheme attributes across diverse government portals and official formats:
  - Text & whitespace sanitization
  - URL validation & canonicalization
  - Multi-format safe date parsing (to YYYY-MM-DD)
  - Government level resolution ('CENTRAL' vs 'STATE')
  - Strict Central vs State relationship enforcement (no states for Central schemes)
  - Canonical state lookup against 36 official States & UTs
  - Category normalization against official sectors
  - Scheme status mapping
"""

from datetime import date, datetime, timezone
import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from app.models.scheme import (
    NormalizedScheme,
    RawScheme,
    SchemeDocumentData,
    SchemeEligibilityData,
    SchemeSourceData,
)


class DataProcessor:
    """
    Normalizes raw government scheme data into standard internal database representation.
    """

    @staticmethod
    def normalize_whitespace(text: Optional[str]) -> Optional[str]:
        """Strip leading/trailing whitespace and collapse internal irregular spaces."""
        if text is None:
            return None
        cleaned = re.sub(r"[ \t]+", " ", str(text)).strip()
        return cleaned if cleaned else None

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """Sanitize scheme name by stripping whitespace and redundant punctuation."""
        if not name:
            return ""
        cleaned = cls.normalize_whitespace(name) or ""
        # Remove trailing periods or quotes if accidentally scraped
        cleaned = cleaned.strip("\"'.,")
        return cleaned

    @classmethod
    def normalize_url(cls, url: Optional[str]) -> Optional[str]:
        """
        Canonicalize URLs: ensure valid scheme (http/https), strip trailing slashes.
        Returns None if url is malformed or not a web URL.
        """
        if not url:
            return None
        cleaned = str(url).strip()
        if not cleaned:
            return None

        # Add https if missing protocol
        if not cleaned.startswith(("http://", "https://")):
            cleaned = "https://" + cleaned

        try:
            parsed = urlparse(cleaned)
            if not parsed.netloc or ("." not in parsed.netloc and parsed.netloc != "localhost"):
                return None
            # Normalize hostname to lowercase and remove trailing slash
            netloc = parsed.netloc.lower()
            path = parsed.path.rstrip("/")
            canonical = f"{parsed.scheme}://{netloc}{path}"
            if parsed.query:
                canonical += f"?{parsed.query}"
            return canonical
        except Exception:
            return None

    @staticmethod
    def normalize_date(date_val: Any) -> Optional[str]:
        """
        Parse dates safely from multiple standard Indian and international formats
        into database-compatible 'YYYY-MM-DD'.
        Handles:
          - ISO: 2026-05-31, 2026-05-31T00:00:00Z
          - Indian standard: 31-05-2026, 31/05/2026
          - Alternative: 2026/05/31, 31.05.2026
          - Python date/datetime objects
        """
        if not date_val:
            return None

        if isinstance(date_val, (datetime, date)):
            return date_val.strftime("%Y-%m-%d")

        cleaned = str(date_val).strip()
        if not cleaned or cleaned.lower() in ("null", "none", "n/a", "na", "ongoing", "open"):
            return None

        # Handle ISO timestamp strings
        if "T" in cleaned:
            cleaned = cleaned.split("T")[0]

        formats_to_try = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d.%m.%Y",
            "%d %b %Y",
            "%d %B %Y",
            "%b %d, %Y",
            "%B %d, %Y",
        ]

        for fmt in formats_to_try:
            try:
                parsed_dt = datetime.strptime(cleaned, fmt)
                return parsed_dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # If regex matches YYYY-MM-DD directly
        if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned):
            return cleaned

        return None

    @classmethod
    def normalize_government_level(cls, level_input: Optional[str]) -> str:
        """
        Resolve government level strictly to 'CENTRAL' or 'STATE'.
        Defaults to 'CENTRAL' if unspecified.
        """
        if not level_input:
            return "CENTRAL"

        cleaned = cls.normalize_whitespace(level_input) or ""
        upper = cleaned.upper()

        if any(term in upper for term in ["STATE", "UT", "UNION TERRITORY", "PROVINCE"]):
            return "STATE"
        if any(term in upper for term in ["CENTRAL", "UNION", "NATIONAL", "ALL INDIA", "PAN INDIA"]):
            return "CENTRAL"

        return "CENTRAL"

    @classmethod
    def normalize_status(cls, status_input: Optional[str]) -> str:
        """
        Normalize scheme lifecycle status to 'ACTIVE', 'INACTIVE', or 'EXPIRED'.
        """
        if not status_input:
            return "ACTIVE"

        cleaned = (cls.normalize_whitespace(status_input) or "").upper()
        if any(term in cleaned for term in ["ACTIVE", "OPEN", "LIVE", "RUNNING", "ONGOING", "APPLY"]):
            return "ACTIVE"
        if any(term in cleaned for term in ["EXPIRED", "CLOSED", "ENDED", "LAPSED"]):
            return "EXPIRED"
        if any(term in cleaned for term in ["INACTIVE", "DISABLED", "HOLD", "SUSPENDED"]):
            return "INACTIVE"

        return "ACTIVE"

    @classmethod
    def normalize_state(
        cls,
        state_input: Optional[str],
        government_level: str,
        state_lookup: Dict[str, Tuple[int, str]],
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Normalize and resolve state reference against master database registry.

        STRICT RULE:
        For CENTRAL schemes, state_id MUST be NULL.
        Do not silently assign a state to a Central scheme.
        For STATE schemes, state_id must correspond to the selected state.

        state_lookup: dict mapping normalized keys (lowercase name, code) -> (id, canonical_name)
        """
        if government_level == "CENTRAL":
            return None, None

        if not state_input:
            return None, None

        cleaned = (cls.normalize_whitespace(state_input) or "").lower()

        # Direct match on name or code in lookup
        if cleaned in state_lookup:
            return state_lookup[cleaned]

        # Fuzzy / prefix matching for common variations (e.g. "Govt of Tamil Nadu", "TamilNadu")
        stripped = re.sub(r"[^a-z0-9]", "", cleaned)
        for key, val in state_lookup.items():
            key_stripped = re.sub(r"[^a-z0-9]", "", key)
            if stripped == key_stripped or key_stripped in stripped:
                return val

        return None, state_input

    @classmethod
    def normalize_category(
        cls,
        cat_input: Optional[str],
        category_lookup: Dict[str, Tuple[int, str]],
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Normalize category input against official government categories.
        category_lookup: dict mapping normalized lowercase name -> (id, canonical_name)
        """
        if not cat_input:
            return None, None

        cleaned = (cls.normalize_whitespace(cat_input) or "").lower()

        if cleaned in category_lookup:
            return category_lookup[cleaned]

        # Check keyword overlaps with official categories
        for key, val in category_lookup.items():
            if key in cleaned or cleaned in key:
                return val

        return None, cat_input

    @classmethod
    def process_raw_scheme(
        cls,
        raw: RawScheme,
        state_lookup: Dict[str, Tuple[int, str]],
        category_lookup: Dict[str, Tuple[int, str]],
    ) -> NormalizedScheme:
        """
        Transforms a RawScheme into a cleanly normalized NormalizedScheme.
        """
        clean_name = cls.normalize_name(raw.scheme_name)
        clean_desc = cls.normalize_whitespace(raw.description)
        gov_level = cls.normalize_government_level(raw.government_level)

        # Enforce State vs Central constraints
        state_id, state_name = cls.normalize_state(raw.state, gov_level, state_lookup)
        cat_id, cat_name = cls.normalize_category(raw.category, category_lookup)

        clean_start_date = cls.normalize_date(raw.start_date)
        clean_last_date = cls.normalize_date(raw.last_date)
        clean_status = cls.normalize_status(raw.status)

        clean_official_url = cls.normalize_url(raw.official_url)
        clean_source_url = cls.normalize_url(raw.source_url) or raw.source_url

        # Normalize sources provenance
        sources = [
            SchemeSourceData(
                source_url=clean_source_url,
                source_type="OFFICIAL_PORTAL",
                last_checked=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
            )
        ]

        # Normalize required documents
        norm_docs = []
        if raw.required_documents:
            for doc in raw.required_documents:
                doc_name = cls.normalize_name(doc.document_name)
                if doc_name:
                    norm_docs.append(
                        SchemeDocumentData(
                            document_name=doc_name,
                            mandatory=doc.mandatory,
                            description=cls.normalize_whitespace(doc.description),
                        )
                    )

        return NormalizedScheme(
            external_id=cls.normalize_whitespace(raw.external_id),
            scheme_name=clean_name,
            description=clean_desc,
            government_level=gov_level,
            state_id=state_id,
            state_name=state_name,
            category_id=cat_id,
            category_name=cat_name,
            benefits=cls.normalize_whitespace(raw.benefits),
            application_process=cls.normalize_whitespace(raw.application_process),
            start_date=clean_start_date,
            last_date=clean_last_date,
            status=clean_status,
            official_url=clean_official_url,
            source_url=clean_source_url,
            source_identifier=raw.source_identifier,
            last_updated=datetime.now(timezone.utc),
            eligibility=raw.eligibility,
            required_documents=norm_docs,
            sources=sources,
        )
