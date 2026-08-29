"""Shared pytest fixtures for backend tests."""

import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from services.debug_pipeline import DebugPipeline
from services.debug_service import DebugService


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "requires_db: marks tests that require a database connection"
    )


@pytest.fixture
def pipeline():
    """Create a DebugPipeline instance for unit tests."""
    return DebugPipeline()


@pytest.fixture
def debug_service(pipeline):
    """Create a DebugService instance wired to the shared pipeline fixture."""
    service = DebugService()
    service.pipeline = pipeline
    return service


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Initialize database tables for integration tests."""
    from database import init_db

    try:
        await init_db()
    except Exception:
        pass
    yield


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create an isolated SQLite database session for unit/repository tests."""
    import tempfile
    import os

    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    database_url = f"sqlite+aiosqlite:///{temp_db.name}"

    engine = create_async_engine(
        database_url,
        echo=False,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},
    )
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables
    from database.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

    await engine.dispose()
    try:
        os.unlink(temp_db.name)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def mock_database_init(request):
    """Mock database initialization to avoid connection errors in non-db unit tests."""
    if "requires_db" not in request.keywords:
        with patch("database.init_db", new_callable=AsyncMock), patch(
            "database.close_db", new_callable=AsyncMock
        ):
            yield
    else:
        yield
