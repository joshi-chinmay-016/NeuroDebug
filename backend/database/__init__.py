"""
Database package initialization.

Provides database session management and configuration.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.database")

# Create async engine
engine = create_async_engine(
    Config.DATABASE_URL,
    echo=Config.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=Config.DATABASE_POOL_SIZE,
    max_overflow=Config.DATABASE_MAX_OVERFLOW,
)

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

    Example:
        async with get_db_session() as session:
            result = await session.execute(query)
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


async def init_db() -> None:
    """Initialize database connection and create tables if needed."""
    try:
        async with engine.begin() as conn:
            # Import models module to ensure all models are registered with Base
            # This import is needed for SQLAlchemy model registration
            from database import models  # noqa: F401

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
    except Exception as exc:
        logger.error("Failed to initialize database: %s", exc)
        raise


async def close_db() -> None:
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as exc:  # noqa: BLE001 - Broad exception handling for cleanup
        logger.error("Error closing database connections: %s", exc)


# Import base class for models
from database.base import Base
