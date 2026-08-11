"""
API routes for analytics and usage statistics.

Handles total requests, success rates, usage metrics, and performance metrics.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from database import get_db_session
from database.models import DebugSession
from middleware.auth import get_current_user_required
from repositories.debug_session_repository import DebugSessionRepository
from services.performance_service import performance_service
from sqlalchemy import select, func
from utils.logging import get_logger

logger = get_logger("neurodebug.routes.analytics")

router = APIRouter()


# ──────────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────────


class UsageMetrics(BaseModel):
    """Usage metrics for a time period."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_duration_ms: float
    total_duration_ms: float


class ErrorDistribution(BaseModel):
    """Error type distribution."""

    error_type: str
    count: int
    percentage: float


class PerformanceMetrics(BaseModel):
    """Performance metrics for pipeline stages."""

    ast_avg_ms: float
    rule_avg_ms: float
    llm_avg_ms: float
    patch_avg_ms: float
    verification_avg_ms: float
    database_avg_ms: float
    total_avg_ms: float


class AnalyticsResponse(BaseModel):
    """Complete analytics response."""

    usage_metrics: UsageMetrics
    error_distribution: list[ErrorDistribution]
    daily_stats: list[dict]
    performance_metrics: PerformanceMetrics


# ──────────────────────────────────────────────────────────────────
# Route Handlers
# ──────────────────────────────────────────────────────────────────


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user_required),
):
    """
    Get analytics data for the authenticated user.

    Args:
        days: Number of days to include in analysis.
        current_user: Current authenticated user.

    Returns:
        AnalyticsResponse with usage metrics and statistics.
    """
    async with get_db_session() as session:
        try:
            user_id = current_user["user_id"]
            start_date = datetime.now(timezone.utc) - timedelta(days=days)

            # Get total requests
            total_result = await session.execute(
                select(func.count())
                .select_from(DebugSession)
                .where(DebugSession.user_id == user_id)
                .where(DebugSession.created_at >= start_date)
            )
            total_requests = total_result.scalar() or 0

            # Get successful requests (those with patches and verification passed)
            # For now, we'll count sessions with candidate patches as successful
            successful_result = await session.execute(
                select(func.count())
                .select_from(DebugSession)
                .where(DebugSession.user_id == user_id)
                .where(DebugSession.created_at >= start_date)
                .where(DebugSession.candidate_patches.any())  # type: ignore
            )
            successful_requests = successful_result.scalar() or 0

            failed_requests = total_requests - successful_requests
            success_rate = (
                (successful_requests / total_requests * 100)
                if total_requests > 0
                else 0.0
            )

            # Get average duration
            duration_result = await session.execute(
                select(func.avg(DebugSession.pipeline_duration_ms))
                .select_from(DebugSession)
                .where(DebugSession.user_id == user_id)
                .where(DebugSession.created_at >= start_date)
                .where(DebugSession.pipeline_duration_ms.isnot(None))
            )
            avg_duration = duration_result.scalar() or 0.0

            # Get total duration
            total_duration_result = await session.execute(
                select(func.sum(DebugSession.pipeline_duration_ms))
                .select_from(DebugSession)
                .where(DebugSession.user_id == user_id)
                .where(DebugSession.created_at >= start_date)
                .where(DebugSession.pipeline_duration_ms.isnot(None))
            )
            total_duration = total_duration_result.scalar() or 0.0

            usage_metrics = UsageMetrics(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                success_rate=round(success_rate, 2),
                avg_duration_ms=round(avg_duration, 2),
                total_duration_ms=round(total_duration, 2),
            )

            # Get error distribution
            error_result = await session.execute(
                select(DebugSession.error_type, func.count())
                .select_from(DebugSession)
                .where(DebugSession.user_id == user_id)
                .where(DebugSession.created_at >= start_date)
                .where(DebugSession.error_type.isnot(None))
                .group_by(DebugSession.error_type)
                .order_by(func.count().desc())
            )
            error_rows = error_result.all()

            error_distribution = []
            for error_type, count in error_rows:
                percentage = (
                    (count / total_requests * 100) if total_requests > 0 else 0.0
                )
                error_distribution.append(
                    ErrorDistribution(
                        error_type=error_type or "Unknown",
                        count=count,
                        percentage=round(percentage, 2),
                    )
                )

            # Get daily stats
            daily_result = await session.execute(
                select(
                    func.date(DebugSession.created_at).label("date"),
                    func.count().label("count"),
                )
                .select_from(DebugSession)
                .where(DebugSession.user_id == user_id)
                .where(DebugSession.created_at >= start_date)
                .group_by(func.date(DebugSession.created_at))
                .order_by(func.date(DebugSession.created_at))
            )
            daily_rows = daily_result.all()

            daily_stats = [
                {"date": str(date), "requests": count} for date, count in daily_rows
            ]

            # Get aggregated performance metrics
            perf_stats = performance_service.get_aggregated_stats()

            performance_metrics = PerformanceMetrics(
                ast_avg_ms=perf_stats.get("ast", {}).get("avg_ms", 0.0),
                rule_avg_ms=perf_stats.get("rule", {}).get("avg_ms", 0.0),
                llm_avg_ms=perf_stats.get("llm", {}).get("avg_ms", 0.0),
                patch_avg_ms=perf_stats.get("patch", {}).get("avg_ms", 0.0),
                verification_avg_ms=perf_stats.get("verification", {}).get(
                    "avg_ms", 0.0
                ),
                database_avg_ms=perf_stats.get("database", {}).get("avg_ms", 0.0),
                total_avg_ms=perf_stats.get("total", {}).get("avg_ms", 0.0),
            )

            return AnalyticsResponse(
                usage_metrics=usage_metrics,
                error_distribution=error_distribution,
                daily_stats=daily_stats,
                performance_metrics=performance_metrics,
            )

        except Exception as exc:
            logger.exception("Failed to get analytics")
            raise Exception("Failed to retrieve analytics data") from exc
