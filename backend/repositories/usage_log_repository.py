"""
Repository for usage log and analytics operations.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UsageLog
from repositories.base import BaseRepository


class UsageLogRepository(BaseRepository[UsageLog, Any, Any]):
    """Repository for usage log operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize usage log repository.

        Args:
            session: Async database session.
        """
        super().__init__(UsageLog, session)

    async def get_daily_usage(
        self,
        session_id: str | None = None,
        user_id: uuid.UUID | None = None,
        date: datetime | None = None,
    ) -> int:
        """
        Get daily usage count for a session or user.

        Args:
            session_id: Optional session ID string.
            user_id: Optional user UUID.
            date: Optional date to check (defaults to today).

        Returns:
            Daily usage count.
        """
        if date is None:
            date = datetime.now(timezone.utc)

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        conditions = [
            UsageLog.request_timestamp >= start_of_day,
            UsageLog.request_timestamp < end_of_day,
        ]
        if session_id:
            conditions.append(UsageLog.session_id == session_id)
        if user_id:
            conditions.append(UsageLog.user_id == user_id)

        query = select(func.count(UsageLog.id)).where(*conditions)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_usage_by_user(
        self,
        user_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[UsageLog]:
        """
        Get usage logs for a user within a date range.

        Args:
            user_id: UUID of the user.
            start_date: Optional start date.
            end_date: Optional end date.

        Returns:
            List of UsageLog instances.
        """
        query = select(UsageLog).where(UsageLog.user_id == user_id)

        if start_date:
            query = query.where(UsageLog.request_timestamp >= start_date)
        if end_date:
            query = query.where(UsageLog.request_timestamp <= end_date)

        query = query.order_by(UsageLog.request_timestamp.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_usage_by_session(
        self,
        session_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[UsageLog]:
        """
        Get usage logs for a session within a date range.

        Args:
            session_id: Session ID string.
            start_date: Optional start date.
            end_date: Optional end date.

        Returns:
            List of UsageLog instances.
        """
        query = select(UsageLog).where(UsageLog.session_id == session_id)

        if start_date:
            query = query.where(UsageLog.request_timestamp >= start_date)
        if end_date:
            query = query.where(UsageLog.request_timestamp <= end_date)

        query = query.order_by(UsageLog.request_timestamp.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_usage_log(
        self,
        session_id: str,
        execution_time_ms: float,
        subscription_tier: str,
        user_id: uuid.UUID | None = None,
        verification_status: str | None = None,
        patch_success: bool = False,
        pipeline_runtime_ms: float | None = None,
        llm_runtime_ms: float | None = None,
        daily_usage_count: int = 0,
    ) -> UsageLog:
        """
        Create a new usage log entry.

        Args:
            session_id: Session ID string.
            execution_time_ms: Execution time in milliseconds.
            subscription_tier: Subscription tier.
            user_id: Optional user UUID.
            verification_status: Optional verification status.
            patch_success: Whether patch was successful.
            pipeline_runtime_ms: Optional pipeline runtime.
            llm_runtime_ms: Optional LLM runtime.
            daily_usage_count: Daily usage count at time of request.

        Returns:
            Created UsageLog instance.
        """
        usage_log = UsageLog(
            session_id=session_id,
            user_id=user_id,
            request_timestamp=datetime.now(timezone.utc),
            execution_time_ms=execution_time_ms,
            verification_status=verification_status,
            patch_success=patch_success,
            pipeline_runtime_ms=pipeline_runtime_ms,
            llm_runtime_ms=llm_runtime_ms,
            subscription_tier=subscription_tier,
            daily_usage_count=daily_usage_count,
        )
        self.session.add(usage_log)
        await self.session.flush()
        await self.session.refresh(usage_log)
        return usage_log

    async def get_analytics_summary(
        self,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get analytics summary for a user or session.

        Args:
            user_id: Optional user UUID.
            session_id: Optional session ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with analytics summary.
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(UsageLog).where(UsageLog.request_timestamp >= start_date)

        if user_id:
            query = query.where(UsageLog.user_id == user_id)
        if session_id:
            query = query.where(UsageLog.session_id == session_id)

        result = await self.session.execute(query)
        logs = list(result.scalars().all())

        total_requests = len(logs)
        successful_patches = sum(1 for log in logs if log.patch_success)
        verified_requests = sum(
            1 for log in logs if log.verification_status == "verified"
        )
        avg_execution_time = (
            sum(log.execution_time_ms for log in logs) / total_requests
            if total_requests > 0
            else 0
        )

        return {
            "total_requests": total_requests,
            "successful_patches": successful_patches,
            "verified_requests": verified_requests,
            "avg_execution_time_ms": round(avg_execution_time, 2),
            "days_analyzed": days,
        }
