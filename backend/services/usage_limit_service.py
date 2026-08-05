"""
Usage limit service for enforcing subscription tier limits.

Provides configurable usage limiting for Guest, Free, Pro, and Enterprise tiers.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import SubscriptionTier
from repositories.subscription_repository import SubscriptionRepository
from repositories.usage_log_repository import UsageLogRepository
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.usage_limit_service")


class UsageLimitExceededError(Exception):
    """Raised when usage limit is exceeded."""

    def __init__(self, limit: int, current_usage: int, tier: str):
        self.limit = limit
        self.current_usage = current_usage
        self.tier = tier
        message = (
            f"Usage limit exceeded for {tier} tier: {current_usage}/{limit} requests"
        )
        super().__init__(message)


class UsageLimitService:
    """
    Service for managing and enforcing usage limits.

    Supports configurable limits for different subscription tiers.
    """

    def __init__(
        self,
        session: AsyncSession,
        subscription_repo: SubscriptionRepository | None = None,
        usage_log_repo: UsageLogRepository | None = None,
    ):
        """
        Initialize usage limit service.

        Args:
            session: Async database session.
            subscription_repo: Optional subscription repository.
            usage_log_repo: Optional usage log repository.
        """
        self.session = session
        self.subscription_repo = subscription_repo or SubscriptionRepository(session)
        self.usage_log_repo = usage_log_repo or UsageLogRepository(session)

    async def get_daily_limit(self, tier: str) -> int:
        """
        Get daily request limit for a subscription tier.

        Args:
            tier: Subscription tier (guest, free, pro, enterprise).

        Returns:
            Daily request limit.
        """
        plan = await self.subscription_repo.get_by_tier(tier)
        if plan:
            return plan.daily_request_limit

        # Fallback to config defaults if no plan found
        fallback_limits = {
            SubscriptionTier.GUEST.value: Config.DEFAULT_GUEST_LIMIT,
            SubscriptionTier.FREE.value: Config.DEFAULT_FREE_LIMIT,
            SubscriptionTier.PRO.value: Config.DEFAULT_PRO_LIMIT,
            SubscriptionTier.ENTERPRISE.value: 999999,  # Unlimited
        }
        return fallback_limits.get(tier, Config.DEFAULT_GUEST_LIMIT)

    async def check_usage_limit(
        self,
        session_id: str,
        tier: str,
        user_id: uuid.UUID | None = None,
    ) -> tuple[bool, int, int]:
        """
        Check if usage limit is exceeded.

        Args:
            session_id: Session ID string.
            tier: Subscription tier.
            user_id: Optional user UUID.

        Returns:
            Tuple of (allowed, current_usage, limit).

        Raises:
            UsageLimitExceededError: If limit is exceeded.
        """
        limit = await self.get_daily_limit(tier)
        current_usage = await self.usage_log_repo.get_daily_usage(
            session_id=session_id, user_id=user_id
        )

        allowed = current_usage < limit

        if not allowed:
            logger.warning(
                "Usage limit exceeded: session_id=%s tier=%s usage=%d limit=%d",
                session_id,
                tier,
                current_usage,
                limit,
            )
            raise UsageLimitExceededError(limit, current_usage, tier)

        return allowed, current_usage, limit

    async def record_usage(
        self,
        session_id: str,
        tier: str,
        execution_time_ms: float,
        user_id: uuid.UUID | None = None,
        verification_status: str | None = None,
        patch_success: bool = False,
        pipeline_runtime_ms: float | None = None,
        llm_runtime_ms: float | None = None,
    ) -> None:
        """
        Record a usage event.

        Args:
            session_id: Session ID string.
            tier: Subscription tier.
            execution_time_ms: Execution time in milliseconds.
            user_id: Optional user UUID.
            verification_status: Optional verification status.
            patch_success: Whether patch was successful.
            pipeline_runtime_ms: Optional pipeline runtime.
            llm_runtime_ms: Optional LLM runtime.
        """
        current_usage = await self.usage_log_repo.get_daily_usage(
            session_id=session_id, user_id=user_id
        )

        await self.usage_log_repo.create_usage_log(
            session_id=session_id,
            user_id=user_id,
            execution_time_ms=execution_time_ms,
            subscription_tier=tier,
            verification_status=verification_status,
            patch_success=patch_success,
            pipeline_runtime_ms=pipeline_runtime_ms,
            llm_runtime_ms=llm_runtime_ms,
            daily_usage_count=current_usage + 1,
        )

        logger.info(
            "Usage recorded: session_id=%s tier=%s daily_count=%d",
            session_id,
            tier,
            current_usage + 1,
        )

    async def get_remaining_requests(
        self,
        session_id: str,
        tier: str,
        user_id: uuid.UUID | None = None,
    ) -> int:
        """
        Get remaining requests for the day.

        Args:
            session_id: Session ID string.
            tier: Subscription tier.
            user_id: Optional user UUID.

        Returns:
            Number of remaining requests.
        """
        limit = await self.get_daily_limit(tier)
        current_usage = await self.usage_log_repo.get_daily_usage(
            session_id=session_id, user_id=user_id
        )
        return max(0, limit - current_usage)

    async def get_usage_analytics(
        self,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get usage analytics for a user or session.

        Args:
            user_id: Optional user UUID.
            session_id: Optional session ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with analytics data.
        """
        return await self.usage_log_repo.get_analytics_summary(
            user_id=user_id, session_id=session_id, days=days
        )
