"""Minimal tests for the DebugService delegation boundary."""

from unittest.mock import AsyncMock

import pytest

from models.responses import DebugResponse


@pytest.mark.asyncio
async def test_debug_service_delegates_to_pipeline(debug_service):
    """DebugService should forward requests to the pipeline unchanged."""
    expected_response = DebugResponse(
        detected_issues=[],
        candidate_patch=None,
        error_type="Clean",
        explanation="No issues detected in the code.",
        confidence_score=1.0,
        patch_status="not_generated",
        validation_result="not_attempted",
        verification_report=None,
        metadata={"total_duration_ms": 0.0},
    )

    debug_service.pipeline.execute = AsyncMock(return_value=expected_response)

    result = await debug_service.debug_code(code="x = 1", api_key="test-key")

    debug_service.pipeline.execute.assert_awaited_once_with(
        code="x = 1", api_key="test-key", test_code=None
    )
    assert result is expected_response
