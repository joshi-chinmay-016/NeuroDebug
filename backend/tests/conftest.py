"""Shared pytest fixtures for backend tests."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

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


@pytest.fixture(autouse=True)
def mock_database_init(request):
    """Mock database initialization to avoid connection errors in tests.
    Skip mocking for tests marked with requires_db."""
    if "requires_db" not in request.keywords:
        with patch("database.init_db", new_callable=AsyncMock), patch(
            "database.close_db", new_callable=AsyncMock
        ):
            yield
    else:
        yield


@pytest.fixture(scope="session")
def database_available():
    """Check if database is available for integration tests."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return False

    try:
        engine = create_async_engine(database_url)
        import asyncio

        async def check():
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")

        asyncio.run(check())
        asyncio.run(engine.dispose())
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Skip tests marked with requires_db if database is not available."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        for item in items:
            if "requires_db" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="DATABASE_URL not set"))
