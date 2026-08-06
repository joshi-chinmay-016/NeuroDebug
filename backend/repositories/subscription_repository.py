"""
Repository for subscription plan and limit management.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import SubscriptionLimit, SubscriptionPlan
from repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[SubscriptionPlan, Any, Any]):
    """Repository for subscription plan operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize subscription repository.

        Args:
            session: Async database session.
        """
        super().__init__(SubscriptionPlan, session)

    async def get_by_tier(self, tier: str) -> SubscriptionPlan | None:
        """
        Get subscription plan by tier name.

        Args:
            tier: Subscription tier (guest, free, pro, enterprise).

        Returns:
            SubscriptionPlan instance or None.
        """
        result = await self.session.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.tier == tier)
            .where(SubscriptionPlan.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_active_plans(self) -> list[SubscriptionPlan]:
        """
        Get all active subscription plans.

        Returns:
            List of active SubscriptionPlan instances.
        """
        result = await self.session.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active.is_(True))
            .order_by(SubscriptionPlan.daily_request_limit)
        )
        return list(result.scalars().all())

    async def get_limit(
        self, plan_id: uuid.UUID, limit_type: str
    ) -> SubscriptionLimit | None:
        """
        Get specific limit for a plan.

        Args:
            plan_id: UUID of the subscription plan.
            limit_type: Type of limit (e.g., 'daily_requests', 'max_projects').

        Returns:
            SubscriptionLimit instance or None.
        """
        result = await self.session.execute(
            select(SubscriptionLimit)
            .where(SubscriptionLimit.plan_id == plan_id)
            .where(SubscriptionLimit.limit_type == limit_type)
        )
        return result.scalar_one_or_none()

    async def create_limit(
        self,
        plan_id: uuid.UUID,
        limit_type: str,
        limit_value: int,
        description: str | None = None,
    ) -> SubscriptionLimit:
        """
        Create a new limit for a subscription plan.

        Args:
            plan_id: UUID of the subscription plan.
            limit_type: Type of limit.
            limit_value: Limit value.
            description: Optional description.

        Returns:
            Created SubscriptionLimit instance.
        """
        limit = SubscriptionLimit(
            plan_id=plan_id,
            limit_type=limit_type,
            limit_value=limit_value,
            description=description,
        )
        self.session.add(limit)
        await self.session.flush()
        await self.session.refresh(limit)
        return limit
