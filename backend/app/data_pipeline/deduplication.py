"""
Deterministic Scheme Deduplication Engine
------------------------------------------
Prevents duplicate scheme records using a strict, multi-stage priority strategy:
  1. Official External Scheme ID (highest confidence)
  2. Canonical Official Application / Source URL
  3. Normalized Name + Government Level + State ID tuple

Distinguishes between:
  - 'INSERT' (Genuinely new welfare scheme)
  - 'UPDATE' (Updated details for existing scheme)
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.models.scheme import NormalizedScheme
from app.utils.logger import pipeline_logger


def canonicalize_url_key(url: Optional[str]) -> Optional[str]:
    """Helper to generate a uniform key for URL deduplication."""
    if not url:
        return None
    cleaned = url.strip().lower()
    try:
        parsed = urlparse(cleaned)
        if not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    except Exception:
        return cleaned.rstrip("/")


class Deduplicator:
    """
    In-memory and database-backed deduplication manager.
    Maintains fast multi-key indexes over known scheme records.
    """

    def __init__(self):
        self.by_external_id: Dict[str, Dict[str, Any]] = {}
        self.by_canonical_url: Dict[str, Dict[str, Any]] = {}
        self.by_name_level_state: Dict[Tuple[str, str, Optional[int]], Dict[str, Any]] = {}

    def index_scheme(self, scheme_record: Dict[str, Any]):
        """Index an existing or freshly processed scheme record."""
        scheme_id = scheme_record.get("id")
        ext_id = scheme_record.get("external_id")
        if ext_id:
            self.by_external_id[str(ext_id).strip()] = scheme_record

        # URL indexing
        for url_field in ["official_url", "source_url"]:
            url = scheme_record.get(url_field)
            if url:
                c_url = canonicalize_url_key(url)
                if c_url:
                    self.by_canonical_url[c_url] = scheme_record

        # Name + Level + State indexing
        raw_name = scheme_record.get("scheme_name", "")
        norm_name = re.sub(r"[ \t]+", " ", str(raw_name)).strip().lower()
        level = (scheme_record.get("government_level") or "CENTRAL").upper()
        state_id = scheme_record.get("state_id")
        if norm_name:
            self.by_name_level_state[(norm_name, level, state_id)] = scheme_record

    def build_index(
        self,
        existing_schemes: List[Dict[str, Any]],
        existing_sources: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Build fast lookup indices from current database records.
        """
        self.by_external_id.clear()
        self.by_canonical_url.clear()
        self.by_name_level_state.clear()

        # Map scheme_sources back to schemes if provided
        source_url_to_scheme_id: Dict[str, str] = {}
        if existing_sources:
            for src in existing_sources:
                sid = src.get("scheme_id")
                surl = canonicalize_url_key(src.get("source_url"))
                if sid and surl:
                    source_url_to_scheme_id[surl] = sid

        for scheme in existing_schemes:
            self.index_scheme(scheme)

    def find_duplicate(
        self, candidate: NormalizedScheme
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]], str]:
        """
        Evaluate candidate scheme against deduplication indices.
        Returns:
          (action, existing_record, match_reason)
          where action is 'UPDATE' or 'INSERT'
        """
        # Priority 1: External Scheme ID
        if candidate.external_id:
            ext_key = candidate.external_id.strip()
            if ext_key in self.by_external_id:
                existing = self.by_external_id[ext_key]
                pipeline_logger.duplicate_detected(candidate.scheme_name, "EXTERNAL_ID", existing.get("id"))
                return "UPDATE", existing, "EXTERNAL_ID"

        # Priority 2: Canonical Official URL
        if candidate.official_url:
            c_off = canonicalize_url_key(candidate.official_url)
            if c_off and c_off in self.by_canonical_url:
                existing = self.by_canonical_url[c_off]
                pipeline_logger.duplicate_detected(candidate.scheme_name, "CANONICAL_OFFICIAL_URL", existing.get("id"))
                return "UPDATE", existing, "CANONICAL_OFFICIAL_URL"

        if candidate.source_url:
            c_src = canonicalize_url_key(candidate.source_url)
            if c_src and c_src in self.by_canonical_url:
                existing = self.by_canonical_url[c_src]
                pipeline_logger.duplicate_detected(candidate.scheme_name, "SOURCE_URL", existing.get("id"))
                return "UPDATE", existing, "SOURCE_URL"

        # Priority 3: Normalized Scheme Name + Government Level + State ID
        norm_name = re.sub(r"[ \t]+", " ", candidate.scheme_name).strip().lower()
        key = (norm_name, candidate.government_level, candidate.state_id)
        if key in self.by_name_level_state:
            existing = self.by_name_level_state[key]
            pipeline_logger.duplicate_detected(candidate.scheme_name, "NAME_LEVEL_STATE", existing.get("id"))
            return "UPDATE", existing, "NAME_LEVEL_STATE"

        return "INSERT", None, "GENUINELY_NEW"
