"""
Structured Safe Logging & Observability Engine for NeuroDebug.

Features:
- Request-scoped correlation ID context propagation
- Automatic regex redaction of sensitive credentials (API keys, Bearer tokens, DB credentials)
- Fine-grained stage duration metrics and pipeline telemetry
"""

from __future__ import annotations

import logging
import re
import uuid
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from typing import Any

# Context variable for request-scoped correlation ID
_request_id: ContextVar[str] = ContextVar("request_id", default="")

# Common credential patterns for safe redaction
REDACTION_PATTERNS = [
    (re.compile(r"(gsk_[a-zA-Z0-9_\-]{20,})", re.IGNORECASE), "gsk_***REDACTED***"),
    (re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE), r"\1***REDACTED_TOKEN***"),
    (re.compile(r'(api_key["\']?\s*[:=]\s*["\'])([^"\']{8,})(["\'])', re.IGNORECASE), r'\1***REDACTED***\3'),
    (re.compile(r'(password["\']?\s*[:=]\s*["\'])([^"\']{4,})(["\'])', re.IGNORECASE), r'\1***REDACTED***\3'),
    (re.compile(r'(postgres(?:ql)?:\/\/[^:]+:)([^@]+)(@)', re.IGNORECASE), r"\1***REDACTED***\3"),
]


def sanitize_log_message(msg: str) -> str:
    """Mask any embedded API keys or credentials in log output."""
    if not isinstance(msg, str):
        msg = str(msg)
    for pattern, replacement in REDACTION_PATTERNS:
        msg = pattern.sub(replacement, msg)
    return msg


class SafeLogFilter(logging.Filter):
    """Logging filter that injects request_id and redacts sensitive data."""

    def filter(self, record: logging.LogRecord) -> bool:
        req_id = _request_id.get() or "system"
        record.request_id = req_id  # type: ignore[attr-defined]
        if isinstance(record.msg, str):
            record.msg = sanitize_log_message(record.msg)
        if record.args and isinstance(record.args, tuple):
            record.args = tuple(
                sanitize_log_message(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure structured logging with safe redaction and request correlation."""
    log_format = "%(asctime)s [%(levelname)s] [req:%(request_id)s] %(name)s — %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(log_format, date_format))
    handler.addFilter(SafeLogFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    logger = logging.getLogger(name)
    if not any(isinstance(f, SafeLogFilter) for f in logger.filters):
        logger.addFilter(SafeLogFilter())
    return logger


def set_request_id(request_id: str | None = None) -> str:
    """Set the request ID for the current context (generates one if None)."""
    req_id = request_id or str(uuid.uuid4())
    _request_id.set(req_id)
    return req_id


def get_request_id() -> str:
    """Get the current request ID."""
    return _request_id.get() or "system"


@dataclass
class PipelineTelemetry:
    """Comprehensive end-to-end execution timing and observability telemetry."""

    request_id: str = field(default_factory=get_request_id)
    ast_duration_ms: float = 0.0
    rule_duration_ms: float = 0.0
    llm_analysis_duration_ms: float = 0.0
    patch_generation_duration_ms: float = 0.0
    patch_validation_duration_ms: float = 0.0
    verification_duration_ms: float = 0.0
    ranking_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    cache_hit: bool = False
    llm_calls: int = 0
    stages_completed: list[str] = field(default_factory=list)


def log_pipeline_stage(
    logger: logging.Logger,
    stage: str,
    duration_ms: float,
    status: str = "success",
    **metadata: Any,
) -> None:
    """Log a pipeline stage with timing and sanitized metadata."""
    safe_meta = {k: sanitize_log_message(str(v)) for k, v in metadata.items()}
    logger.info(
        "Pipeline stage: stage=%s status=%s duration_ms=%.2f metadata=%s",
        stage,
        status,
        duration_ms,
        safe_meta,
    )


def log_verification_stage(
    logger: logging.Logger,
    stage: str,
    duration_ms: float,
    status: str = "success",
    **metadata: Any,
) -> None:
    """Log a verification stage with timing and sanitized metadata."""
    safe_meta = {k: sanitize_log_message(str(v)) for k, v in metadata.items()}
    logger.info(
        "Verification stage: stage=%s status=%s duration_ms=%.2f metadata=%s",
        stage,
        status,
        duration_ms,
        safe_meta,
    )


def log_execution_result(
    logger: logging.Logger,
    execution_type: str,
    success: bool,
    exit_code: int | None,
    execution_time: float,
    timeout_occurred: bool,
) -> None:
    """Log execution result details."""
    logger.info(
        "Execution result: type=%s success=%s exit_code=%s execution_time=%.3fs timeout=%s",
        execution_type,
        success,
        exit_code,
        execution_time,
        timeout_occurred,
    )
