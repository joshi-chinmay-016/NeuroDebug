"""
Performance Metrics Service

Tracks timing metrics for AST, rule, LLM, verification, and database operations.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict

from utils.logging import get_logger

logger = get_logger("neurodebug.performance_service")


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single request."""

    request_id: str
    ast_duration_ms: float = 0.0
    rule_duration_ms: float = 0.0
    llm_duration_ms: float = 0.0
    patch_generation_duration_ms: float = 0.0
    verification_duration_ms: float = 0.0
    database_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "request_id": self.request_id,
            "ast_duration_ms": self.ast_duration_ms,
            "rule_duration_ms": self.rule_duration_ms,
            "llm_duration_ms": self.llm_duration_ms,
            "patch_generation_duration_ms": self.patch_generation_duration_ms,
            "verification_duration_ms": self.verification_duration_ms,
            "database_duration_ms": self.database_duration_ms,
            "total_duration_ms": self.total_duration_ms,
            "metadata": self.metadata,
        }


class PerformanceService:
    """Service for tracking and aggregating performance metrics."""

    def __init__(self):
        """Initialize performance service."""
        self._current_metrics: PerformanceMetrics | None = None
        self._start_time: float = 0.0
        self._stage_start_time: float = 0.0
        self._aggregated_metrics: defaultdict[str, list[float]] = defaultdict(list)

    def start_request(self, request_id: str) -> None:
        """
        Start tracking a new request.

        Args:
            request_id: Unique identifier for the request.
        """
        self._current_metrics = PerformanceMetrics(request_id=request_id)
        self._start_time = time.time()
        logger.debug("Performance tracking started for request: %s", request_id)

    def end_request(self) -> PerformanceMetrics | None:
        """
        End tracking the current request.

        Returns:
            PerformanceMetrics for the completed request.
        """
        if self._current_metrics is None:
            return None

        self._current_metrics.total_duration_ms = (
            time.time() - self._start_time
        ) * 1000
        metrics = self._current_metrics

        # Aggregate metrics
        self._aggregated_metrics["ast"].append(metrics.ast_duration_ms)
        self._aggregated_metrics["rule"].append(metrics.rule_duration_ms)
        self._aggregated_metrics["llm"].append(metrics.llm_duration_ms)
        self._aggregated_metrics["patch"].append(metrics.patch_generation_duration_ms)
        self._aggregated_metrics["verification"].append(
            metrics.verification_duration_ms
        )
        self._aggregated_metrics["database"].append(metrics.database_duration_ms)
        self._aggregated_metrics["total"].append(metrics.total_duration_ms)

        logger.debug(
            "Performance tracking ended for request: %s (total: %.2fms)",
            metrics.request_id,
            metrics.total_duration_ms,
        )

        self._current_metrics = None
        return metrics

    @contextmanager
    def track_stage(self, stage_name: str):
        """
        Context manager to track a specific stage duration.

        Args:
            stage_name: Name of the stage (ast, rule, llm, patch, verification, database).

        Yields:
            None
        """
        self._stage_start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - self._stage_start_time) * 1000
            if self._current_metrics:
                if stage_name == "ast":
                    self._current_metrics.ast_duration_ms = duration_ms
                elif stage_name == "rule":
                    self._current_metrics.rule_duration_ms = duration_ms
                elif stage_name == "llm":
                    self._current_metrics.llm_duration_ms = duration_ms
                elif stage_name == "patch":
                    self._current_metrics.patch_generation_duration_ms = duration_ms
                elif stage_name == "verification":
                    self._current_metrics.verification_duration_ms = duration_ms
                elif stage_name == "database":
                    self._current_metrics.database_duration_ms = duration_ms

            logger.debug("Stage %s completed in %.2fms", stage_name, duration_ms)

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to current metrics.

        Args:
            key: Metadata key.
            value: Metadata value.
        """
        if self._current_metrics:
            self._current_metrics.metadata[key] = value

    def get_aggregated_stats(self) -> dict[str, dict[str, float]]:
        """
        Get aggregated statistics for all tracked requests.

        Returns:
            Dictionary with statistics for each stage.
        """
        stats = {}
        for stage, durations in self._aggregated_metrics.items():
            if not durations:
                continue
            stats[stage] = {
                "count": len(durations),
                "avg_ms": sum(durations) / len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "total_ms": sum(durations),
            }
        return stats

    def reset_aggregated(self) -> None:
        """Reset aggregated metrics."""
        self._aggregated_metrics.clear()
        logger.debug("Aggregated metrics reset")


# Global performance service instance
performance_service = PerformanceService()
