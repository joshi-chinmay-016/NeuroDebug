"""
Database package initialization.

Provides database session management, PostgreSQL auto-provisioning, table creation,
and subscription plan seeding.
"""

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Import base class for models (must be at top level)
from database.base import Base
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.database")

import os
from sqlalchemy.pool import NullPool

# Create async engine with NullPool for tests to prevent closed event loop issues on Windows
engine_kwargs = {
    "echo": Config.DATABASE_ECHO,
}

if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING") == "true":
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_pre_ping"] = True
    # Only add pool parameters for non-SQLite databases
    if not Config.DATABASE_URL.startswith("sqlite"):
        engine_kwargs.update({
            "pool_size": Config.DATABASE_POOL_SIZE,
            "max_overflow": Config.DATABASE_MAX_OVERFLOW,
        })

engine = create_async_engine(Config.DATABASE_URL, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with proper error handling.

    Yields:
        AsyncSession: Database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Database session rollback due to error")
            raise
        finally:
            await session.close()


async def _ensure_database_exists() -> None:
    """Ensure PostgreSQL database exists, creating it if needed."""
    if not Config.DATABASE_URL.startswith("postgresql"):
        return

    try:
        import asyncpg

        parsed = urlparse(Config.DATABASE_URL.replace("postgresql+asyncpg://", "http://"))
        db_name = parsed.path.lstrip("/")
        user = parsed.username
        password = parsed.password
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432

        # Connect to default postgres DB
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres",
            timeout=3.0,
        )
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            logger.info("Database '%s' does not exist. Creating automatically...", db_name)
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            logger.info("Database '%s' created successfully.", db_name)
        await conn.close()
    except Exception as exc:
        logger.warning("Could not auto-create database via postgres catalog: %s", exc)


async def _seed_subscription_plans() -> None:
    """Idempotently seed default subscription plans into PostgreSQL."""
    try:
        from database.models import SubscriptionPlan, SubscriptionTier

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

        async with get_db_session() as session:
            query = select(SubscriptionPlan)
            result = await session.execute(query)
            existing_plans = {plan.tier: plan for plan in result.scalars().all()}

            for plan_data in plans_to_seed:
                tier = plan_data["tier"]
                if tier in existing_plans:
                    plan = existing_plans[tier]
                    plan.daily_request_limit = plan_data["daily_request_limit"]
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

            await session.commit()
            logger.info("Subscription plans seeded/updated successfully in PostgreSQL.")
    except Exception as exc:
        logger.warning("Could not seed subscription plans: %s", exc)


async def init_db() -> None:
    """Initialize database connection, create all tables, and seed initial plans."""
    await _ensure_database_exists()
    try:
        async with engine.begin() as conn:
            # Import models module to ensure all models are registered with Base
            from database import models  # noqa: F401

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized and all tables verified successfully.")

        # Seed default plans
        await _seed_subscription_plans()
    except Exception as exc:
        logger.warning(
            "Database initialization encountered an issue on startup: %s. "
            "Server will continue running so stateless endpoints remain available.",
            exc,
        )


async def close_db() -> None:
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as exc:  # noqa: BLE001 - Broad exception handling for cleanup
        logger.error("Error closing database connections: %s", exc)
