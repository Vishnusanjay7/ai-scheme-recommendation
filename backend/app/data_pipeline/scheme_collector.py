"""
Government Scheme Collector & Orchestrator
-------------------------------------------
Coordinates end-to-end data acquisition across all registered official
government adapters and datasets.

Workflow:
  1. Discover and load active official sources
  2. Fetch raw scheme records
  3. Normalize attributes (whitespace, dates, URLs, government level, states)
  4. Validate against integrity constraints
  5. Deduplicate against existing schemes
  6. Insert new schemes or update existing records
  7. Maintain provenance in scheme_sources
  8. Emit structured logs and return execution summary
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.data_pipeline.importers.official_importer import OfficialImporter
from app.data_pipeline.source_manager import SourceManager
from app.utils.logger import pipeline_logger


class SchemeCollector:
    """
    Central orchestrator for the Phase 2 scheme acquisition pipeline.
    """

    def __init__(self, source_manager: Optional[SourceManager] = None, dry_run: bool = True):
        self.source_manager = source_manager or SourceManager()
        self.dry_run = dry_run
        self.importer = OfficialImporter(dry_run=dry_run)

    def collect_and_update_schemes(
        self,
        sources: Optional[List[str]] = None,
        dataset_file: Optional[Union[str, Path]] = None,
        limit_per_source: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute collection across specified sources or dataset files.
        """
        summary = {
            "sources_processed": 0,
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "new_schemes": 0,
            "updated_schemes": 0,
            "duplicates": 0,
            "errors": [],
        }

        # 1. Process dataset file if supplied
        if dataset_file:
            path = Path(dataset_file)
            pipeline_logger._log_event(
                20, "collector_file_start", f"Processing official dataset file: {path.name}"
            )
            try:
                file_summary = self.importer.import_from_file(path)
                summary["sources_processed"] += 1
                summary["records_received"] += file_summary["records_received"]
                summary["records_valid"] += file_summary["records_valid"]
                summary["records_rejected"] += file_summary["records_rejected"]
                summary["new_schemes"] += file_summary["new_schemes"]
                summary["updated_schemes"] += file_summary["updated_schemes"]
                summary["duplicates"] += file_summary["duplicates"]
                summary["errors"].extend(file_summary.get("errors", []))
            except Exception as exc:
                err = f"Failed importing file {path.name}: {exc}"
                summary["errors"].append(err)
                pipeline_logger._log_event(40, "file_import_error", err)

        # 2. Process adapters
        adapters_to_run = []
        if sources:
            for s_name in sources:
                ad = self.source_manager.get_adapter(s_name)
                if ad:
                    adapters_to_run.append(ad)
                else:
                    msg = f"Source adapter '{s_name}' not found in registry."
                    summary["errors"].append(msg)
                    pipeline_logger._log_event(30, "adapter_not_found", msg)
        else:
            adapters_to_run = self.source_manager.get_available_adapters()

        for adapter in adapters_to_run:
            summary["sources_processed"] += 1
            pipeline_logger.source_started(adapter.source_name, {"dry_run": self.dry_run})
            try:
                raw_schemes = adapter.fetch_schemes(limit=limit_per_source)
                raw_dicts = [s.model_dump() for s in raw_schemes]
                adapter_summary = self.importer.import_records(
                    raw_dicts, source_identifier=adapter.source_name
                )
                summary["records_received"] += adapter_summary["records_received"]
                summary["records_valid"] += adapter_summary["records_valid"]
                summary["records_rejected"] += adapter_summary["records_rejected"]
                summary["new_schemes"] += adapter_summary["new_schemes"]
                summary["updated_schemes"] += adapter_summary["updated_schemes"]
                summary["duplicates"] += adapter_summary["duplicates"]
                summary["errors"].extend(adapter_summary.get("errors", []))
            except Exception as exc:
                err = f"Error during collection from '{adapter.source_name}': {exc}"
                summary["errors"].append(err)
                pipeline_logger.source_failure(adapter.source_name, str(exc))

        pipeline_logger._log_event(
            20,
            "collector_completed",
            f"Scheme collection run completed. Processed: {summary['records_received']} records, Valid: {summary['records_valid']}, Rejected: {summary['records_rejected']}, New: {summary['new_schemes']}, Updated: {summary['updated_schemes']}",
            {"summary": summary},
        )
        return summary


def collect_and_update_schemes(
    sources: Optional[List[str]] = None,
    dataset_file: Optional[Union[str, Path]] = None,
    dry_run: bool = True,
    limit_per_source: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Convenience function to execute scheme acquisition and update pipeline.
    """
    collector = SchemeCollector(dry_run=dry_run)
    return collector.collect_and_update_schemes(
        sources=sources, dataset_file=dataset_file, limit_per_source=limit_per_source
    )
