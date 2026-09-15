"""
Official Government Scheme Dataset Importer
--------------------------------------------
Implements an ingestion processor for authoritative government datasets
(e.g., official JSON/CSV published by ministries or open data platforms).

Fulfills the complete pipeline:
  Structured Official Data -> Normalization -> Validation -> Deduplication -> Persistence
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from app.data_pipeline.data_processor import DataProcessor
from app.data_pipeline.data_validator import DataValidator
from app.data_pipeline.deduplication import Deduplicator
from app.integrations.supabase_client import (
    get_supabase_admin_client,
    get_supabase_client,
    is_supabase_configured,
)
from app.models.scheme import (
    NormalizedScheme,
    RawScheme,
    SchemeDocumentData,
    SchemeEligibilityData,
)
from app.utils.logger import pipeline_logger


class OfficialImporter:
    """
    Importer for processing and ingesting official structured government scheme datasets.
    Supports dry-run validation mode and live database persistence.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.processor = DataProcessor()
        self.validator = DataValidator()
        self.deduplicator = Deduplicator()
        self.state_lookup: Dict[str, Tuple[int, str]] = {}
        self.category_lookup: Dict[str, Tuple[int, str]] = {}
        self._initialized = False

    def load_reference_lookups(self):
        """Preload States and Categories lookups from Supabase for normalizer matching."""
        if not is_supabase_configured():
            return

        client = get_supabase_client()
        try:
            # Load States & UTs
            states_res = client.table("states").select("id, name, code").execute()
            for s in states_res.data or []:
                s_id = s["id"]
                name = s["name"]
                code = s["code"]
                self.state_lookup[name.strip().lower()] = (s_id, name)
                self.state_lookup[code.strip().lower()] = (s_id, name)

            # Load Scheme Categories
            cats_res = client.table("scheme_categories").select("id, name").execute()
            for c in cats_res.data or []:
                c_id = c["id"]
                c_name = c["name"]
                self.category_lookup[c_name.strip().lower()] = (c_id, c_name)

            # Pre-populate deduplicator with existing schemes from DB
            schemes_res = client.table("schemes").select(
                "id, scheme_name, government_level, state_id, official_url, source_url"
            ).execute()
            sources_res = client.table("scheme_sources").select("scheme_id, source_url").execute()
            self.deduplicator.build_index(schemes_res.data or [], sources_res.data or [])

            self._initialized = True
        except Exception as exc:
            pipeline_logger._log_event(
                30, "lookup_load_error", f"Could not load reference lookups from Supabase: {exc}"
            )

    def process_and_persist_scheme(
        self, norm: NormalizedScheme, action: str, existing_id: Optional[str]
    ) -> Optional[str]:
        """
        Persist a validated normalized scheme into Supabase tables:
        schemes, scheme_eligibility, scheme_documents, scheme_sources.
        Returns scheme_id if persisted.
        """
        if self.dry_run:
            scheme_id = existing_id or "dry-run-generated-id"
            self.deduplicator.index_scheme({
                "id": scheme_id,
                "external_id": norm.external_id,
                "scheme_name": norm.scheme_name,
                "government_level": norm.government_level,
                "state_id": norm.state_id,
                "official_url": norm.official_url,
                "source_url": norm.source_url,
            })
            return scheme_id

        # Elevated admin access is required for persistent writes under RLS
        admin_client = get_supabase_admin_client()

        scheme_payload = {
            "scheme_name": norm.scheme_name,
            "description": norm.description,
            "government_level": norm.government_level,
            "state_id": norm.state_id,
            "category_id": norm.category_id,
            "benefits": norm.benefits,
            "application_process": norm.application_process,
            "start_date": norm.start_date,
            "last_date": norm.last_date,
            "status": norm.status,
            "official_url": norm.official_url,
            "source_url": norm.source_url,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        scheme_id = None
        if action == "UPDATE" and existing_id:
            scheme_id = existing_id
            admin_client.table("schemes").update(scheme_payload).eq("id", existing_id).execute()
            pipeline_logger.scheme_updated(scheme_id, norm.scheme_name)
        else:
            insert_res = admin_client.table("schemes").insert(scheme_payload).execute()
            if insert_res.data:
                scheme_id = insert_res.data[0]["id"]
                pipeline_logger.scheme_inserted(scheme_id, norm.scheme_name)

        if not scheme_id:
            return None

        # 1. Eligibility criteria persistence
        if norm.eligibility:
            elig_payload = {
                "scheme_id": scheme_id,
                "min_age": norm.eligibility.min_age,
                "max_age": norm.eligibility.max_age,
                "max_income": norm.eligibility.max_income,
                "gender": norm.eligibility.gender,
                "occupation": norm.eligibility.occupation,
                "education": norm.eligibility.education,
                "category": norm.eligibility.category,
                "disability_required": norm.eligibility.disability_required,
                "state_restriction": norm.eligibility.state_restriction or norm.state_id,
                "district_restriction": norm.eligibility.district_restriction,
                "other_conditions": norm.eligibility.other_conditions or {},
            }
            # Delete old eligibility for this scheme if updating, then insert
            admin_client.table("scheme_eligibility").delete().eq("scheme_id", scheme_id).execute()
            admin_client.table("scheme_eligibility").insert(elig_payload).execute()

        # 2. Documents persistence
        if norm.required_documents:
            admin_client.table("scheme_documents").delete().eq("scheme_id", scheme_id).execute()
            doc_rows = [
                {
                    "scheme_id": scheme_id,
                    "document_name": doc.document_name,
                    "mandatory": doc.mandatory,
                    "description": doc.description,
                }
                for doc in norm.required_documents
            ]
            if doc_rows:
                admin_client.table("scheme_documents").insert(doc_rows).execute()

        # 3. Provenance sources persistence
        if norm.sources:
            for src in norm.sources:
                src_payload = {
                    "scheme_id": scheme_id,
                    "source_url": src.source_url,
                    "source_type": src.source_type or "OFFICIAL_PORTAL",
                    "last_checked": src.last_checked.isoformat() if src.last_checked else datetime.now(timezone.utc).isoformat(),
                    "last_updated": src.last_updated.isoformat() if src.last_updated else datetime.now(timezone.utc).isoformat(),
                }
                admin_client.table("scheme_sources").insert(src_payload).execute()

        # Register into local deduplicator index so same run sees it
        self.deduplicator.index_scheme({
            "id": scheme_id,
            "external_id": norm.external_id,
            "scheme_name": norm.scheme_name,
            "government_level": norm.government_level,
            "state_id": norm.state_id,
            "official_url": norm.official_url,
            "source_url": norm.source_url,
        })
        return scheme_id

    def import_records(
        self, raw_records: List[Dict[str, Any]], source_identifier: str = "official_import"
    ) -> Dict[str, Any]:
        """
        Processes a batch of raw records through normalization, validation,
        deduplication, and optional persistence.
        """
        if not self._initialized:
            self.load_reference_lookups()

        pipeline_logger.source_started(source_identifier, {"records_count": len(raw_records), "dry_run": self.dry_run})

        summary = {
            "sources_processed": 1,
            "records_received": len(raw_records),
            "records_valid": 0,
            "records_rejected": 0,
            "new_schemes": 0,
            "updated_schemes": 0,
            "duplicates": 0,
            "errors": [],
        }

        for row in raw_records:
            scheme_title = row.get("scheme_name") or row.get("name", "Unknown Scheme")

            # Convert row to RawScheme
            try:
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
                    scheme_name=scheme_title,
                    description=row.get("description"),
                    government_level=row.get("government_level", "CENTRAL"),
                    state=row.get("state"),
                    category=row.get("category"),
                    benefits=row.get("benefits"),
                    eligibility=eligibility_obj,
                    required_documents=docs_list if docs_list else None,
                    application_process=row.get("application_process"),
                    official_url=row.get("official_url"),
                    source_url=row.get("source_url") or "https://www.myscheme.gov.in",
                    start_date=row.get("start_date"),
                    last_date=row.get("last_date"),
                    status=row.get("status", "ACTIVE"),
                    source_identifier=source_identifier,
                )
            except Exception as e:
                summary["records_rejected"] += 1
                err_msg = f"Failed parsing schema for '{scheme_title}': {str(e)}"
                summary["errors"].append(err_msg)
                pipeline_logger.records_rejected(scheme_title, [err_msg])
                continue

            # Normalize
            normalized = self.processor.process_raw_scheme(
                raw_scheme, self.state_lookup, self.category_lookup
            )

            # Validate
            val_result = self.validator.validate_scheme(normalized)
            if not val_result.is_valid:
                summary["records_rejected"] += 1
                err_msg = f"Validation failed for '{scheme_title}': {'; '.join(val_result.errors)}"
                summary["errors"].append(err_msg)
                pipeline_logger.validation_errors(scheme_title, val_result.errors)
                continue

            summary["records_valid"] += 1

            # Deduplicate
            action, existing_rec, match_reason = self.deduplicator.find_duplicate(normalized)
            existing_id = existing_rec.get("id") if existing_rec else None

            if action == "UPDATE":
                summary["duplicates"] += 1
                summary["updated_schemes"] += 1
            else:
                summary["new_schemes"] += 1

            try:
                self.process_and_persist_scheme(normalized, action, existing_id)
            except Exception as exc:
                err_msg = f"Database persistence error for '{scheme_title}': {str(exc)}"
                summary["errors"].append(err_msg)
                pipeline_logger._log_event(40, "persistence_error", err_msg)

        pipeline_logger.source_completed(source_identifier, summary["records_valid"])
        return summary

    def import_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load and import from a local JSON dataset file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Official dataset file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data if isinstance(data, list) else data.get("schemes", data.get("data", []))
        return self.import_records(records, source_identifier=path.name)
