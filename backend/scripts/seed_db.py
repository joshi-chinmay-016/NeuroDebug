"""
Idempotent Database Migration and Seeding Script.

Creates all tables in PostgreSQL and seeds initial subscription plans.
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from database import Base, engine, get_db_session, init_db
from database.models import (
    SubscriptionLimit,
    SubscriptionPlan,
    SubscriptionTier,
)
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.scripts.seed_db")


async def seed_database() -> None:
    """Initialize tables and seed subscription plans idempotently."""
    logger.info("Initializing database schema...")
    await init_db()

    logger.info("Seeding subscription plans...")
    async with get_db_session() as session:
        # Check if plans already exist
        query = select(SubscriptionPlan)
        result = await session.execute(query)
        existing_plans = {plan.tier: plan for plan in result.scalars().all()}

        plans_to_seed = [
            {
                "name": "Guest",
                "tier": SubscriptionTier.GUEST.value,
                "price": 0.0,
                "daily_request_limit": Config.DEFAULT_GUEST_LIMIT,  # 1 request / day
                "features": {
                    "ast_parsing": True,
                    "rules": 13,
                    "candidate_patch": True,
                    "diff_view": True,
                },
            },
            {
                "name": "Free",
                "tier": SubscriptionTier.FREE.value,
                "price": 0.0,
                "daily_request_limit": Config.DEFAULT_FREE_LIMIT,  # 5 requests / day
                "features": {
                    "ast_parsing": True,
                    "rules": 13,
                    "candidate_patch": True,
                    "diff_view": True,
                    "execution_verification": True,
                    "test_runner": True,
                    "workspaces": True,
                    "history": True,
                },
            },
            {
                "name": "Pro",
                "tier": SubscriptionTier.PRO.value,
                "price": 19.0,
                "daily_request_limit": Config.DEFAULT_PRO_LIMIT,  # 20 requests / day
                "features": {
                    "ast_parsing": True,
                    "rules": 13,
                    "candidate_patch": True,
                    "diff_view": True,
                    "execution_verification": True,
                    "test_runner": True,
                    "workspaces": True,
                    "history": True,
                    "priority_queue": True,
                    "custom_api_key": True,
                },
            },
        ]

        for plan_data in plans_to_seed:
            tier = plan_data["tier"]
            if tier in existing_plans:
                # Update existing plan limit
                plan = existing_plans[tier]
                plan.daily_request_limit = plan_data["daily_request_limit"]
                logger.info(
                    "Updated existing plan '%s' limit to %d requests/day",
                    plan.name,
                    plan.daily_request_limit,
                )
            else:
                new_plan = SubscriptionPlan(
                    id=uuid.uuid4(),
                    name=plan_data["name"],
                    tier=plan_data["tier"],
                    price=plan_data["price"],
                    billing_period="monthly" if plan_data["price"] > 0 else "lifetime",
                    daily_request_limit=plan_data["daily_request_limit"],
                    features=plan_data["features"],
                    is_active=True,
                )
                session.add(new_plan)
                logger.info(
                    "Created new plan '%s' with %d requests/day",
                    new_plan.name,
                    new_plan.daily_request_limit,
                )

        await session.commit()
        logger.info("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
