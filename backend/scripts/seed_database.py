"""
Database seeding script.

Creates initial subscription plans and limits.
"""

import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from database.models import SubscriptionPlan, SubscriptionLimit
from repositories.subscription_repository import SubscriptionRepository
from utils.logging import get_logger

logger = get_logger("neurodebug.seed_database")


async def seed_subscription_plans(session: AsyncSession) -> None:
    """Seed subscription plans with default configurations."""
    repo = SubscriptionRepository(session)

    # Check if plans already exist
    existing = await repo.get_active_plans()
    if existing:
        logger.info("Subscription plans already exist, skipping seed")
        return

    # Create Guest plan
    guest_plan = await repo.create(
        SubscriptionPlan(
            name="Guest",
            tier="guest",
            daily_request_limit=3,
            max_projects=0,
            features={
                "basic_debugging": True,
                "ast_analysis": True,
                "rule_engine": True,
                "llm_analysis": False,
                "patch_generation": False,
                "verification": False,
                "history": False,
                "projects": False,
                "api_access": False,
            },
            price_monthly=0,
            is_active=True,
        )
    )
    logger.info("Created Guest plan: %s", guest_plan.id)

    # Create Free plan
    free_plan = await repo.create(
        SubscriptionPlan(
            name="Free",
            tier="free",
            daily_request_limit=5,
            max_projects=3,
            features={
                "basic_debugging": True,
                "ast_analysis": True,
                "rule_engine": True,
                "llm_analysis": True,
                "patch_generation": True,
                "verification": True,
                "history": True,
                "projects": True,
                "api_access": False,
            },
            price_monthly=0,
            is_active=True,
        )
    )
    logger.info("Created Free plan: %s", free_plan.id)

    # Create Pro plan
    pro_plan = await repo.create(
        SubscriptionPlan(
            name="Pro",
            tier="pro",
            daily_request_limit=20,
            max_projects=999999,
            features={
                "basic_debugging": True,
                "ast_analysis": True,
                "rule_engine": True,
                "llm_analysis": True,
                "patch_generation": True,
                "verification": True,
                "history": True,
                "projects": True,
                "api_access": True,
                "priority_processing": True,
                "advanced_reports": True,
            },
            price_monthly=2900,  # $29.00
            is_active=True,
        )
    )
    logger.info("Created Pro plan: %s", pro_plan.id)

    # Create Enterprise plan
    enterprise_plan = await repo.create(
        SubscriptionPlan(
            name="Enterprise",
            tier="enterprise",
            daily_request_limit=999999,
            max_projects=999999,
            features={
                "basic_debugging": True,
                "ast_analysis": True,
                "rule_engine": True,
                "llm_analysis": True,
                "patch_generation": True,
                "verification": True,
                "history": True,
                "projects": True,
                "api_access": True,
                "priority_processing": True,
                "advanced_reports": True,
                "team_features": True,
                "custom_integrations": True,
                "dedicated_support": True,
            },
            price_monthly=9900,  # $99.00
            is_active=True,
        )
    )
    logger.info("Created Enterprise plan: %s", enterprise_plan.id)

    # Create additional limits for Pro plan
    await repo.create_limit(
        pro_plan.id,
        "max_code_length",
        50000,
        "Maximum code length in characters",
    )
    await repo.create_limit(
        pro_plan.id,
        "max_execution_time",
        60,
        "Maximum execution time in seconds",
    )

    logger.info("Database seeding completed successfully")


async def main():
    """Main seeding function."""
    async with AsyncSessionLocal() as session:
        try:
            await seed_subscription_plans(session)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("Failed to seed database: %s", exc)
            raise


if __name__ == "__main__":
    asyncio.run(main())
