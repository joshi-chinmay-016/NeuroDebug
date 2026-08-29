"""
Service for analytics and usage statistics.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from repositories.usage_log_repository import UsageLogRepository


class AnalyticsService:
    """Service for analytics and usage statistics."""

    def __init__(self, usage_log_repository: UsageLogRepository):
        """
        Initialize analytics service.

        Args:
            usage_log_repository: Repository for usage log operations.
        """
        self.usage_log_repository = usage_log_repository

    async def get_user_analytics(
        self,
        user_id: uuid.UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get analytics for a specific user.

        Args:
            user_id: UUID of the user.
            days: Number of days to analyze.

        Returns:
            Dictionary with user analytics.
        """
        return await self.usage_log_repository.get_analytics_summary(
            user_id=user_id, days=days
        )

    async def get_usage_trends(
        self,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Get usage trends over time.

        Args:
            user_id: Optional user UUID.
            session_id: Optional session ID.
            days: Number of days to analyze.

        Returns:
            List of daily usage data points.
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        end_date = datetime.now(timezone.utc)

        if user_id:
            logs = await self.usage_log_repository.get_usage_by_user(
                user_id=user_id, start_date=start_date, end_date=end_date
            )
        else:
            logs = await self.usage_log_repository.get_usage_by_session(
                session_id=session_id, start_date=start_date, end_date=end_date
            )

        # Group by day
        daily_data = {}
        for log in logs:
            day = log.request_timestamp.date()
            if day not in daily_data:
                daily_data[day] = {"date": day, "count": 0, "success": 0}
            daily_data[day]["count"] += 1
            if log.patch_success:
                daily_data[day]["success"] += 1

        # Convert to list and sort by date
        return [
            {
                "date": str(data["date"]),
                "count": data["count"],
                "success": data["success"],
            }
            for data in sorted(daily_data.values(), key=lambda x: x["date"])
        ]

    async def get_success_rate(
        self,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get success rate statistics.

        Args:
            user_id: Optional user UUID.
            session_id: Optional session ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with success rate statistics.
        """
        summary = await self.usage_log_repository.get_analytics_summary(
            user_id=user_id, session_id=session_id, days=days
        )

        total_requests = summary["total_requests"]
        successful_patches = summary["successful_patches"]

        success_rate = (
            (successful_patches / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "success_rate": round(success_rate, 2),
            "total_requests": total_requests,
            "successful_patches": successful_patches,
            "failed_patches": total_requests - successful_patches,
        }

    async def get_performance_metrics(
        self,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get performance metrics.

        Args:
            user_id: Optional user UUID.
            session_id: Optional session ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with performance metrics.
        """
        summary = await self.usage_log_repository.get_analytics_summary(
            user_id=user_id, session_id=session_id, days=days
        )

        return {
            "avg_execution_time_ms": summary["avg_execution_time_ms"],
            "total_requests": summary["total_requests"],
            "days_analyzed": summary["days_analyzed"],
        }

    async def get_subscription_analytics(
        self,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Get subscription-related analytics for a user.

        Args:
            user_id: UUID of the user.

        Returns:
            Dictionary with subscription analytics.
        """
        # Get analytics for different time periods
        daily = await self.usage_log_repository.get_analytics_summary(
            user_id=user_id, days=1
        )
        weekly = await self.usage_log_repository.get_analytics_summary(
            user_id=user_id, days=7
        )
        monthly = await self.usage_log_repository.get_analytics_summary(
            user_id=user_id, days=30
        )

        return {
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
        }

    async def get_aggregate_analytics(
        self,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get aggregate analytics across all users.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary with aggregate analytics.
        """
        return await self.usage_log_repository.get_analytics_summary(
            user_id=None, session_id=None, days=days
        )
