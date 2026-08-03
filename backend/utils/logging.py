"""Structured logging configuration for NeuroDebug."""

import logging
from contextvars import ContextVar
from typing import Any

# Context variable for request-scoped logging
_request_id: ContextVar[str] = ContextVar("request_id", default="")


def configure_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s — [%(request_id)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt=date_format,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    _request_id.set(request_id)


def get_request_id() -> str:
    """Get the current request ID."""
    return _request_id.get()


class RequestLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds request ID to log records."""

    def process(self, msg: Any, kwargs: Any) -> tuple[Any, Any]:
        """Add request_id to the log record."""
        kwargs.setdefault("extra", {})["request_id"] = get_request_id()
        return msg, kwargs


def log_pipeline_stage(
    logger: logging.Logger,
    stage: str,
    duration_ms: float,
    status: str = "success",
    **metadata: Any,
) -> None:
    """Log a pipeline stage with timing and metadata."""
    logger.info(
        "Pipeline stage: stage=%s status=%s duration_ms=%.2f metadata=%s",
        stage,
        status,
        duration_ms,
        metadata,
    )
