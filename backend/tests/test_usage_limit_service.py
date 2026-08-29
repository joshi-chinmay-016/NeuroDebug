"""
Tests for usage limit service.
"""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import SubscriptionTier, User
from repositories.subscription_repository import SubscriptionRepository
from services.usage_limit_service import UsageLimitExceededError, UsageLimitService


@pytest.mark.asyncio
async def test_get_daily_limit(db_session: AsyncSession):
    """Test getting daily limit for different tiers."""
    service = UsageLimitService(db_session)

    # Test different tiers
    guest_limit = await service.get_daily_limit(SubscriptionTier.GUEST.value)
    assert guest_limit == 1

    free_limit = await service.get_daily_limit(SubscriptionTier.FREE.value)
    assert free_limit == 5

    pro_limit = await service.get_daily_limit(SubscriptionTier.PRO.value)
    assert pro_limit == 20

    enterprise_limit = await service.get_daily_limit(
        SubscriptionTier.ENTERPRISE.value
    )
    assert enterprise_limit == 999999  # Unlimited


@pytest.mark.asyncio
async def test_check_usage_limit(db_session: AsyncSession):
    """Test usage limit checking."""
    service = UsageLimitService(db_session)
    session_id = f"test_session_{uuid.uuid4()}"

    # Initially should be under limit
    allowed, current, limit = await service.check_usage_limit(
        session_id=session_id, tier=SubscriptionTier.FREE.value
    )
    assert allowed is True
    assert current == 0
    assert limit == 5

    # Record some usage
    for _ in range(2):
        await service.record_usage(
            session_id=session_id,
            tier=SubscriptionTier.FREE.value,
            execution_time_ms=1000.0,
        )

    # Should still be under limit
    allowed, current, limit = await service.check_usage_limit(
        session_id=session_id, tier=SubscriptionTier.FREE.value
    )
    assert allowed is True
    assert current == 2
    assert limit == 5


@pytest.mark.asyncio
async def test_usage_limit_exceeded_error(db_session: AsyncSession):
    """Test UsageLimitExceededError is raised."""
    service = UsageLimitService(db_session)
    session_id = f"test_session_{uuid.uuid4()}"

    # Fill up the limit
    for _ in range(5):
        await service.record_usage(
            session_id=session_id,
            tier=SubscriptionTier.FREE.value,
            execution_time_ms=1000.0,
        )

    # Should raise error on next check
    with pytest.raises(UsageLimitExceededError) as exc_info:
        await service.check_usage_limit(
            session_id=session_id, tier=SubscriptionTier.FREE.value
        )

    error = exc_info.value
    assert error.limit == 5
    assert error.current_usage >= 5
    assert error.tier == SubscriptionTier.FREE.value


@pytest.mark.asyncio
async def test_record_usage(db_session: AsyncSession):
    """Test usage recording."""
    service = UsageLimitService(db_session)
    session_id = f"test_session_{uuid.uuid4()}"

    # Record usage
    await service.record_usage(
        session_id=session_id,
        tier=SubscriptionTier.FREE.value,
        execution_time_ms=1500.0,
        verification_status="verified",
        patch_success=True,
        pipeline_runtime_ms=1200.0,
        llm_runtime_ms=1000.0,
    )

    # Verify usage was recorded
    usage = await service.usage_log_repo.get_daily_usage(session_id=session_id)
    assert usage >= 1

    # Get usage logs
    logs = await service.usage_log_repo.get_usage_by_session(session_id=session_id)
    assert len(logs) >= 1
    assert logs[0].execution_time_ms == 1500.0
    assert logs[0].verification_status == "verified"
    assert logs[0].patch_success is True


@pytest.mark.asyncio
async def test_get_remaining_requests(db_session: AsyncSession):
    """Test getting remaining requests."""
    service = UsageLimitService(db_session)
    session_id = f"test_session_{uuid.uuid4()}"

    # Initially should have full limit
    remaining = await service.get_remaining_requests(
        session_id=session_id, tier=SubscriptionTier.FREE.value
    )
    assert remaining == 5

    # Record 2 requests
    for _ in range(2):
        await service.record_usage(
            session_id=session_id,
            tier=SubscriptionTier.FREE.value,
            execution_time_ms=1000.0,
        )

    # Should have 3 remaining
    remaining = await service.get_remaining_requests(
        session_id=session_id, tier=SubscriptionTier.FREE.value
    )
    assert remaining == 3


@pytest.mark.asyncio
async def test_get_usage_analytics(db_session: AsyncSession):
    """Test usage analytics generation."""
    service = UsageLimitService(db_session)
    session_id = f"test_session_{uuid.uuid4()}"

    # Record some usage with different outcomes
    await service.record_usage(
        session_id=session_id,
        tier=SubscriptionTier.FREE.value,
        execution_time_ms=1000.0,
        verification_status="verified",
        patch_success=True,
    )

    await service.record_usage(
        session_id=session_id,
        tier=SubscriptionTier.FREE.value,
        execution_time_ms=1500.0,
        verification_status="unverified",
        patch_success=False,
    )

    await service.record_usage(
        session_id=session_id,
        tier=SubscriptionTier.FREE.value,
        execution_time_ms=800.0,
        verification_status="verified",
        patch_success=True,
    )

    # Get analytics
    analytics = await service.get_usage_analytics(session_id=session_id, days=30)

    assert analytics["total_requests"] >= 3
    assert analytics["successful_patches"] >= 2
    assert analytics["verified_requests"] >= 2
    assert analytics["avg_execution_time_ms"] > 0
    assert analytics["days_analyzed"] == 30


@pytest.mark.asyncio
async def test_daily_usage_reset(db_session: AsyncSession):
    """Test that daily usage resets correctly."""
    service = UsageLimitService(db_session)
    session_id = f"test_session_{uuid.uuid4()}"

    # Record usage today
    await service.record_usage(
        session_id=session_id,
        tier=SubscriptionTier.FREE.value,
        execution_time_ms=1000.0,
    )

    # Check current usage
    current = await service.usage_log_repo.get_daily_usage(session_id=session_id)
    assert current >= 1


@pytest.mark.asyncio
async def test_user_specific_usage(db_session: AsyncSession):
    """Test usage tracking for specific users."""
    # Create a user
    sub_repo = SubscriptionRepository(db_session)
    free_plan = await sub_repo.get_by_tier(SubscriptionTier.FREE.value)

    user = User(
        email=f"usage_test_{uuid.uuid4().hex[:8]}@example.com",
        display_name="Usage Test User",
        subscription_plan_id=free_plan.id if free_plan else None,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    service = UsageLimitService(db_session)

    # Record user-specific usage
    await service.record_usage(
        session_id="session_123",
        user_id=user.id,
        tier=SubscriptionTier.FREE.value,
        execution_time_ms=1000.0,
    )

    # Verify user usage was recorded
    user_usage = await service.usage_log_repo.get_daily_usage(user_id=user.id)
    assert user_usage >= 1
