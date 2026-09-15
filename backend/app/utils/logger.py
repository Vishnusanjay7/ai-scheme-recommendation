"""
Structured Logging Utility for AI Government Scheme Recommender
---------------------------------------------------------------
Provides standard, structured log formatting for data pipeline operations
and background collectors.

Security compliance:
Strictly redacts/omits sensitive keys (passwords, tokens, API keys, private citizen data).
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "jwt",
    "secret",
    "api_key",
    "apikey",
    "service_role_key",
    "openai_api_key",
    "email_api_key",
    "phone",
    "aadhaar",
    "pan",
    "annual_income",
    "user_id",
}


def sanitize_data(data: Any) -> Any:
    """Recursively redact sensitive keys from dictionaries/lists."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if str(k).lower() in SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_data(v)
        return sanitized
    elif isinstance(data, (list, tuple, set)):
        return [sanitize_data(item) for item in data]
    return data


class PipelineLogger:
    """
    Structured logger for the government scheme acquisition pipeline.
    Emits clean, structured log events.
    """

    def __init__(self, name: str = "data_pipeline"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _log_event(self, level: int, event: str, message: str, context: Optional[dict] = None):
        log_line = f"[{event}] {message}"
        if context:
            log_line += f" | {json.dumps(sanitize_data(context), default=str)}"
        self.logger.log(level, log_line)

    def source_started(self, source_name: str, details: Optional[dict] = None):
        self._log_event(logging.INFO, "source_started", f"Started data collection from {source_name}", {"source": source_name, **(details or {})})

    def source_completed(self, source_name: str, records_count: int):
        self._log_event(logging.INFO, "source_completed", f"Completed data collection from {source_name}", {"source": source_name, "records_count": records_count})

    def records_fetched(self, source_name: str, count: int):
        self._log_event(logging.INFO, "records_fetched", f"Fetched {count} records from {source_name}", {"source": source_name, "count": count})

    def records_rejected(self, scheme_name: str, errors: list):
        self._log_event(logging.WARNING, "records_rejected", f"Record rejected: {scheme_name}", {"scheme_name": scheme_name, "errors": errors})

    def validation_errors(self, scheme_name: str, errors: list):
        self._log_event(logging.WARNING, "validation_errors", f"Validation failed for: {scheme_name}", {"scheme_name": scheme_name, "errors": errors})

    def duplicate_detected(self, scheme_name: str, match_type: str, existing_id: Optional[str] = None):
        self._log_event(logging.INFO, "duplicate_detected", f"Duplicate detected for '{scheme_name}' by {match_type}", {"scheme_name": scheme_name, "match_type": match_type, "existing_id": existing_id})

    def scheme_inserted(self, scheme_id: str, scheme_name: str):
        self._log_event(logging.INFO, "scheme_inserted", f"New scheme persisted: {scheme_name}", {"scheme_id": scheme_id, "scheme_name": scheme_name})

    def scheme_updated(self, scheme_id: str, scheme_name: str):
        self._log_event(logging.INFO, "scheme_updated", f"Existing scheme updated: {scheme_name}", {"scheme_id": scheme_id, "scheme_name": scheme_name})

    def source_failure(self, source_name: str, error: str):
        self._log_event(logging.ERROR, "source_failure", f"Failed collection for source: {source_name} - {error}", {"source": source_name, "error": error})


# Singleton default logger
pipeline_logger = PipelineLogger()
