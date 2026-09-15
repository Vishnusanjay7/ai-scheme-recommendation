"""
Government Scheme Source Manager
---------------------------------
Coordinates and manages multiple official government data source adapters.
Provides a unified registry for discovering, querying, and checking availability
across national, central, state, and dataset-level sources.
"""

from pathlib import Path
from typing import Dict, List, Optional
from app.integrations.government_source import (
    CentralGovernmentAdapter,
    GovernmentSourceAdapter,
    MySchemeAdapter,
    OfficialFileDatasetAdapter,
)
from app.utils.logger import pipeline_logger


class SourceManager:
    """
    Registry and lifecycle coordinator for government source adapters.
    """

    def __init__(self):
        self._adapters: Dict[str, GovernmentSourceAdapter] = {}
        # Register standard default adapters
        self.register_adapter(MySchemeAdapter())
        self.register_adapter(CentralGovernmentAdapter())

    def register_adapter(self, adapter: GovernmentSourceAdapter):
        """Register a new government source adapter."""
        self._adapters[adapter.source_name] = adapter
        pipeline_logger._log_event(
            20,
            "adapter_registered",
            f"Registered source adapter: {adapter.source_name} ({adapter.source_type})",
            {"source_name": adapter.source_name, "source_type": adapter.source_type},
        )

    def register_dataset_file(self, file_path: Path) -> OfficialFileDatasetAdapter:
        """Helper to register an official dataset file adapter."""
        adapter = OfficialFileDatasetAdapter(file_path)
        self.register_adapter(adapter)
        return adapter

    def get_adapter(self, source_name: str) -> Optional[GovernmentSourceAdapter]:
        """Retrieve a specific registered adapter by name."""
        return self._adapters.get(source_name)

    def list_adapters(self) -> List[Dict[str, str]]:
        """Return operational summary of all registered adapters."""
        return [
            {
                "name": name,
                "type": adapter.source_type,
                "base_url": adapter.base_url,
                "available": adapter.is_available(),
            }
            for name, adapter in self._adapters.items()
        ]

    def get_available_adapters(self) -> List[GovernmentSourceAdapter]:
        """Return only adapters that currently have verified live access or valid files."""
        return [a for a in self._adapters.values() if a.is_available()]
