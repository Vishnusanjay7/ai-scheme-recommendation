"""Data Pipeline Package Initialization."""

from app.data_pipeline.data_processor import DataProcessor
from app.data_pipeline.data_validator import DataValidator
from app.data_pipeline.deduplication import Deduplicator
from app.data_pipeline.district_adapter import DistrictAdapter
from app.data_pipeline.importers.official_importer import OfficialImporter
from app.data_pipeline.scheme_collector import SchemeCollector, collect_and_update_schemes
from app.data_pipeline.source_manager import SourceManager

__all__ = [
    "DataProcessor",
    "DataValidator",
    "Deduplicator",
    "DistrictAdapter",
    "OfficialImporter",
    "SchemeCollector",
    "SourceManager",
    "collect_and_update_schemes",
]
