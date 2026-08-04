"""Shared pytest fixtures for backend tests."""

import pytest

from services.debug_pipeline import DebugPipeline
from services.debug_service import DebugService


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
