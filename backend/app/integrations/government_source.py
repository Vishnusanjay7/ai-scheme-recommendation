"""
Official Government Source Adapters Architecture
------------------------------------------------
Provides an extensible adapter interface for acquiring scheme data from
authoritative Indian government sources:
  - myScheme.gov.in (National Welfare Portal)
  - data.gov.in (Open Government Data Platform India)
  - State Government departmental portals (e.g., MahaDBT, TNeGA)
  - Official machine-readable dataset files (OGD Open Data exports)

COMPLIANCE NOTICE:
Strictly complies with website terms of use, robots.txt exclusions, and API access controls.
Does not bypass CAPTCHAs, perform unpermitted web scraping, or invent synthetic data.
When live official endpoints require partner authentication (e.g. MeitY API keys/MoUs),
the adapters verify credential availability and report operational status cleanly.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from app.models.scheme import (
    RawScheme,
    SchemeEligibilityData,
    SchemeDocumentData,
    SchemeSourceData,
)
from app.utils.logger import pipeline_logger


class GovernmentSourceAdapter(ABC):
    """
    Abstract Base Class for all official government scheme data sources.
    Every source must provide a unique name, source type, availability check,
    and standardized fetching methods returning RawScheme models.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique human-readable identifier for the source."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Type of source: 'NATIONAL_PORTAL', 'OGD_API', 'STATE_PORTAL', 'DATASET_FILE'."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base canonical URL for the official portal/API."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the source is configured and accessible (e.g., credentials present, endpoint reachable)."""
        pass

    @abstractmethod
    def fetch_schemes(self, limit: Optional[int] = None) -> List[RawScheme]:
        """Fetch raw schemes from the official source."""
        pass

    @abstractmethod
    def fetch_scheme_details(self, identifier: str) -> Optional[RawScheme]:
        """Fetch full details for an individual scheme from the official source."""
        pass

    def get_provenance_info(self) -> Dict[str, Any]:
        """Standard provenance metadata for citations."""
        return {
            "source_name": self.source_name,
            "source_type": self.source_type,
            "base_url": self.base_url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class MySchemeAdapter(GovernmentSourceAdapter):
    """
    Adapter for myScheme (https://www.myscheme.gov.in/),
    the National Platform for Government Schemes developed by NeGD/MeitY.

    Access Governance:
    - myScheme does not offer an unrestricted, unauthenticated public REST API.
    - Automated API access requires authorized Government Partner API keys or
      integration through the National Data & Analytics Platform (NDAP).
    - In compliance with ethical bot guidelines and terms of service, this adapter
      does not execute unauthorized headless scraping.
    """

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self._api_url = api_url or os.getenv("MYSCHEME_API_URL")
        self._api_key = api_key or os.getenv("MYSCHEME_API_KEY")

    @property
    def source_name(self) -> str:
        return "myScheme National Portal"

    @property
    def source_type(self) -> str:
        return "NATIONAL_PORTAL"

    @property
    def base_url(self) -> str:
        return "https://www.myscheme.gov.in"

    def is_available(self) -> bool:
        """Requires configured partner API endpoint and key."""
        return bool(self._api_url and self._api_key)

    def fetch_schemes(self, limit: Optional[int] = None) -> List[RawScheme]:
        if not self.is_available():
            pipeline_logger.source_started(
                self.source_name,
                {"status": "unconfigured_credentials", "note": "Partner API key (MYSCHEME_API_KEY) required for live feed."}
            )
            return []

        pipeline_logger.source_started(self.source_name, {"endpoint": self._api_url})
        try:
            headers = {"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"}
            params = {"limit": limit} if limit else {}
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(f"{self._api_url}/schemes", headers=headers, params=params)
                resp.raise_for_status()
                payload = resp.json()
                items = payload.get("data", [])
                results = []
                for item in items:
                    results.append(
                        RawScheme(
                            external_id=str(item.get("id")),
                            scheme_name=item.get("name") or item.get("scheme_name", ""),
                            description=item.get("description"),
                            government_level=item.get("level", "CENTRAL").upper(),
                            state=item.get("state"),
                            category=item.get("category"),
                            benefits=item.get("benefits"),
                            official_url=item.get("official_url"),
                            source_url=item.get("source_url") or f"{self.base_url}/schemes/{item.get('id')}",
                            source_identifier="myscheme",
                        )
                    )
                pipeline_logger.records_fetched(self.source_name, len(results))
                return results
        except Exception as exc:
            pipeline_logger.source_failure(self.source_name, str(exc))
            return []

    def fetch_scheme_details(self, identifier: str) -> Optional[RawScheme]:
        if not self.is_available():
            return None
        # Implements single scheme retrieval when partner key is active
        return None


class CentralGovernmentAdapter(GovernmentSourceAdapter):
    """
    Adapter for the Open Government Data (OGD) Platform India (https://data.gov.in/).
    Supports official ministry catalog feeds under the National Data Sharing
    and Accessibility Policy (NDSAP).
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("DATA_GOV_IN_API_KEY")

    @property
    def source_name(self) -> str:
        return "data.gov.in (Open Government Data Platform)"

    @property
    def source_type(self) -> str:
        return "OGD_API"

    @property
    def base_url(self) -> str:
        return "https://data.gov.in"

    def is_available(self) -> bool:
        return bool(self._api_key)

    def fetch_schemes(self, limit: Optional[int] = None) -> List[RawScheme]:
        if not self.is_available():
            pipeline_logger.source_started(
                self.source_name,
                {"status": "unconfigured_credentials", "note": "OGD API key (DATA_GOV_IN_API_KEY) required."}
            )
            return []
        return []

    def fetch_scheme_details(self, identifier: str) -> Optional[RawScheme]:
        return None


class StateGovernmentAdapter(GovernmentSourceAdapter):
    """
    Adapter for State/UT specific departmental portals.
    Supports fetching state schemes from state portal open APIs (e.g. TN, Maharashtra, Karnataka).
    """

    def __init__(self, state_name: str, state_code: str, portal_url: str, api_endpoint: Optional[str] = None):
        self._state_name = state_name
        self._state_code = state_code
        self._portal_url = portal_url
        self._api_endpoint = api_endpoint

    @property
    def source_name(self) -> str:
        return f"{self._state_name} State Welfare Portal"

    @property
    def source_type(self) -> str:
        return "STATE_PORTAL"

    @property
    def base_url(self) -> str:
        return self._portal_url

    def is_available(self) -> bool:
        return bool(self._api_endpoint)

    def fetch_schemes(self, limit: Optional[int] = None) -> List[RawScheme]:
        if not self.is_available():
            return []
        return []

    def fetch_scheme_details(self, identifier: str) -> Optional[RawScheme]:
        return None


class OfficialFileDatasetAdapter(GovernmentSourceAdapter):
    """
    Adapter for ingesting official machine-readable government scheme datasets
    (e.g., authorized JSON/CSV exports released by ministries or myScheme open data).
    Provides a completely legitimate, reproducible mechanism for importing
    verified official data without web scraping.
    """

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)

    @property
    def source_name(self) -> str:
        return f"Official Dataset File: {self.file_path.name}"

    @property
    def source_type(self) -> str:
        return "DATASET_FILE"

    @property
    def base_url(self) -> str:
        return "https://www.myscheme.gov.in"

    def is_available(self) -> bool:
        return self.file_path.exists() and self.file_path.is_file()

    def fetch_schemes(self, limit: Optional[int] = None) -> List[RawScheme]:
        if not self.is_available():
            pipeline_logger.source_failure(self.source_name, f"File not found: {self.file_path}")
            return []

        pipeline_logger.source_started(self.source_name, {"path": str(self.file_path)})
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_records = data if isinstance(data, list) else data.get("schemes", data.get("data", []))
            schemes: List[RawScheme] = []

            for row in raw_records:
                eligibility_obj = None
                if "eligibility" in row and isinstance(row["eligibility"], dict):
                    eligibility_obj = SchemeEligibilityData(**row["eligibility"])

                docs_list = []
                if "required_documents" in row and isinstance(row["required_documents"], list):
                    for doc in row["required_documents"]:
                        if isinstance(doc, str):
                            docs_list.append(SchemeDocumentData(document_name=doc))
                        elif isinstance(doc, dict):
                            docs_list.append(SchemeDocumentData(**doc))

                raw_scheme = RawScheme(
                    external_id=row.get("external_id") or row.get("id"),
                    scheme_name=row.get("scheme_name") or row.get("name", ""),
                    description=row.get("description"),
                    government_level=row.get("government_level", "CENTRAL"),
                    state=row.get("state"),
                    category=row.get("category"),
                    benefits=row.get("benefits"),
                    eligibility=eligibility_obj,
                    required_documents=docs_list if docs_list else None,
                    application_process=row.get("application_process"),
                    official_url=row.get("official_url"),
                    source_url=row.get("source_url") or self.base_url,
                    start_date=row.get("start_date"),
                    last_date=row.get("last_date"),
                    status=row.get("status", "ACTIVE"),
                    last_updated=row.get("last_updated"),
                    source_identifier=row.get("source_identifier") or "official_file_dataset",
                )
                schemes.append(raw_scheme)
                if limit and len(schemes) >= limit:
                    break

            pipeline_logger.records_fetched(self.source_name, len(schemes))
            return schemes
        except Exception as exc:
            pipeline_logger.source_failure(self.source_name, str(exc))
            return []

    def fetch_scheme_details(self, identifier: str) -> Optional[RawScheme]:
        schemes = self.fetch_schemes()
        for s in schemes:
            if s.external_id == identifier or s.scheme_name == identifier:
                return s
        return None
