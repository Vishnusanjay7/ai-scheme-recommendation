"""
Deterministic Scheme Deduplication Engine
------------------------------------------
Prevents duplicate scheme records using strict, high-confidence identity signals in priority order:
  1. Source Scheme ID / External ID (highest confidence)
  2. Source Slug (e.g., myScheme canonical slug)
  3. Normalized Name + Government Level + Beneficiary State tuple

Rules:
  - Source URL / Official URL / Reference PDF is NEVER used alone as a scheme identity key.
    Distinct schemes frequently cite the same departmental portal or gazette/policy PDF.
  - Source URL may only serve as supporting evidence (e.g., corroborating a name+level+state match).
  - Two distinct schemes sharing an identical document or portal URL are preserved independently.
  - Repeated ingestion of the same source scheme ID or slug resolves to 'UPDATE'.
  - Unprecedented schemes resolve to 'INSERT'.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.models.scheme import NormalizedScheme
from app.utils.logger import pipeline_logger


def canonicalize_url_key(url: Optional[str]) -> Optional[str]:
    """Helper to generate a uniform key for URL comparison."""
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


def extract_slug_from_source(source_type: Optional[str], source_url: Optional[str]) -> Optional[str]:
    """Extract scheme slug from source_type metadata or canonical source URL."""
    if source_type:
        m = re.search(r"slug:\s*([a-zA-Z0-9_-]+)", str(source_type), re.IGNORECASE)
        if m:
            return m.group(1).strip().lower()

    if source_url:
        m = re.search(r"myscheme\.gov\.in/schemes/([a-zA-Z0-9_-]+)", str(source_url), re.IGNORECASE)
        if m:
            return m.group(1).strip().lower()

    return None


class Deduplicator:
    """
    In-memory and database-backed deduplication manager.
    Maintains fast multi-key indexes over known scheme records.
    """

    def __init__(self):
        self.by_external_id: Dict[str, Dict[str, Any]] = {}
        self.by_slug: Dict[str, Dict[str, Any]] = {}
        self.by_name_level_state: Dict[Tuple[str, str, Optional[int]], Dict[str, Any]] = {}
        self.by_canonical_url: Dict[str, List[Dict[str, Any]]] = {}

    def index_scheme(self, scheme_record: Dict[str, Any]):
        """Index an existing or freshly processed scheme record."""
        # 1. External / Source Scheme ID
        ext_id = scheme_record.get("external_id") or scheme_record.get("source_id")
        if ext_id:
            ext_key = str(ext_id).strip().lower()
            self.by_external_id[ext_key] = scheme_record

        # 2. Source Slug
        slug = scheme_record.get("slug")
        if not slug and ext_id:
            slug = ext_id
        if slug:
            slug_key = str(slug).strip().lower()
            self.by_slug[slug_key] = scheme_record

        # 3. Name + Level + State
        raw_name = scheme_record.get("scheme_name", "")
        norm_name = re.sub(r"[ \t]+", " ", str(raw_name)).strip().lower()
        level = (scheme_record.get("government_level") or "CENTRAL").upper()
        state_id = scheme_record.get("state_id")
        if norm_name:
            self.by_name_level_state[(norm_name, level, state_id)] = scheme_record

        # 4. URLs (indexed as a list for supporting evidence, NEVER as sole scheme identity)
        for url_field in ["official_url", "source_url"]:
            url = scheme_record.get(url_field)
            if url:
                c_url = canonicalize_url_key(url)
                if c_url:
                    if c_url not in self.by_canonical_url:
                        self.by_canonical_url[c_url] = []
                    if scheme_record not in self.by_canonical_url[c_url]:
                        self.by_canonical_url[c_url].append(scheme_record)

    def build_index(
        self,
        existing_schemes: List[Dict[str, Any]],
        existing_sources: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Build lookup indices from current database records.
        """
        self.by_external_id.clear()
        self.by_slug.clear()
        self.by_name_level_state.clear()
        self.by_canonical_url.clear()

        # Build scheme_id to scheme map
        scheme_map: Dict[str, Dict[str, Any]] = {}
        for scheme in existing_schemes:
            sid = str(scheme.get("id"))
            scheme_map[sid] = scheme

        # Extract slugs from sources if available
        if existing_sources:
            for src in existing_sources:
                sid = str(src.get("scheme_id"))
                if sid in scheme_map:
                    extracted_slug = extract_slug_from_source(
                        src.get("source_type"), src.get("source_url")
                    )
                    if extracted_slug:
                        scheme_map[sid]["slug"] = extracted_slug
                        if not scheme_map[sid].get("external_id"):
                            scheme_map[sid]["external_id"] = extracted_slug

        for scheme in existing_schemes:
            self.index_scheme(scheme)

    def find_duplicate(
        self, candidate: NormalizedScheme
    ) -> Tuple[str, Optional[Dict[str, Any]], str]:
        """
        Evaluate candidate scheme against deduplication indices using strong scheme identity signals:
          1. Source Scheme ID when available
          2. Source Slug when available
          3. Normalized scheme name + government level + beneficiary state

        Source URL is only used as supporting evidence / corroboration, NEVER as the sole duplicate key.
        Two distinct schemes sharing the same official PDF or document URL are preserved independently.
        """
        candidate_name = re.sub(r"[ \t]+", " ", str(candidate.scheme_name)).strip().lower()

        # Priority 1: Source Scheme ID
        candidate_ext_id = candidate.external_id
        if candidate_ext_id:
            ext_key = str(candidate_ext_id).strip().lower()
            if ext_key in self.by_external_id:
                existing = self.by_external_id[ext_key]
                pipeline_logger.duplicate_detected(candidate.scheme_name, "EXTERNAL_ID", existing.get("id"))
                return "UPDATE", existing, "EXTERNAL_ID"

        # Priority 2: Source Slug
        candidate_slug = getattr(candidate, "slug", None) or candidate_ext_id
        if candidate_slug:
            slug_key = str(candidate_slug).strip().lower()
            if slug_key in self.by_slug:
                existing = self.by_slug[slug_key]
                pipeline_logger.duplicate_detected(candidate.scheme_name, "SLUG", existing.get("id"))
                return "UPDATE", existing, "SLUG"

        # Priority 3: Normalized Scheme Name + Government Level + Beneficiary State
        level = (candidate.government_level or "CENTRAL").upper()
        state_id = candidate.state_id
        name_tuple = (candidate_name, level, state_id)

        if name_tuple in self.by_name_level_state:
            existing = self.by_name_level_state[name_tuple]
            # Check if source/official URL corroborates the match as supporting evidence
            c_off = canonicalize_url_key(candidate.official_url)
            c_src = canonicalize_url_key(candidate.source_url)
            e_off = canonicalize_url_key(existing.get("official_url"))
            e_src = canonicalize_url_key(existing.get("source_url"))

            url_corroborated = bool(
                (c_off and c_off in (e_off, e_src)) or (c_src and c_src in (e_off, e_src))
            )
            reason = "NAME_LEVEL_STATE_CORROBORATED" if url_corroborated else "NAME_LEVEL_STATE"
            pipeline_logger.duplicate_detected(candidate.scheme_name, reason, existing.get("id"))
            return "UPDATE", existing, "NAME_LEVEL_STATE"

        # If IDs, slugs, and names differ: distinctly new scheme (even if sharing a PDF/source URL)
        return "INSERT", None, "GENUINELY_NEW"
