"""
Tests for usage limit service.
"""

from datetime import datetime, timedelta, timezone

import pytest

from database import get_db_session
from database.models import SubscriptionTier, User
from repositories.subscription_repository import SubscriptionRepository
from services.usage_limit_service import UsageLimitExceededError, UsageLimitService


@pytest.mark.asyncio
async def test_get_daily_limit():
    """Test getting daily limit for different tiers."""
    async with get_db_session() as session:
        service = UsageLimitService(session)

        # Test different tiers
        guest_limit = await service.get_daily_limit(SubscriptionTier.GUEST.value)
        assert guest_limit == 3

        free_limit = await service.get_daily_limit(SubscriptionTier.FREE.value)
        assert free_limit == 5

        pro_limit = await service.get_daily_limit(SubscriptionTier.PRO.value)
        assert pro_limit == 20

        enterprise_limit = await service.get_daily_limit(
            SubscriptionTier.ENTERPRISE.value
        )
        assert enterprise_limit == 999999  # Unlimited


@pytest.mark.asyncio
async def test_check_usage_limit():
    """Test usage limit checking."""
    async with get_db_session() as session:
        service = UsageLimitService(session)
        session_id = "test_session_123"

        # Initially should be under limit
        allowed, current, limit = await service.check_usage_limit(
            session_id=session_id, tier=SubscriptionTier.GUEST.value
        )
        assert allowed is True
        assert current == 0
        assert limit == 3

        # Record some usage
        for _ in range(3):
            await service.record_usage(
                session_id=session_id,
                tier=SubscriptionTier.GUEST.value,
                execution_time_ms=1000.0,
            )

        # Should now be at limit
        allowed, current, limit = await service.check_usage_limit(
            session_id=session_id, tier=SubscriptionTier.GUEST.value
        )
        assert allowed is False
        assert current == 3
        assert limit == 3


@pytest.mark.asyncio
async def test_usage_limit_exceeded_error():
    """Test UsageLimitExceededError is raised."""
    async with get_db_session() as session:
        service = UsageLimitService(session)
        session_id = "test_session_456"

        # Fill up the limit
        for _ in range(5):
            await service.record_usage(
                session_id=session_id,
                tier=SubscriptionTier.FREE.value,
                execution_time_ms=1000.0,
            )

        # Should raise error
        with pytest.raises(UsageLimitExceededError) as exc_info:
            await service.check_usage_limit(
                session_id=session_id, tier=SubscriptionTier.FREE.value
            )

        error = exc_info.value
        assert error.limit == 5
        assert error.current_usage == 5
        assert error.tier == SubscriptionTier.FREE.value


@pytest.mark.asyncio
async def test_record_usage():
    """Test usage recording."""
    async with get_db_session() as session:
        service = UsageLimitService(session)
        session_id = "test_session_789"

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
        assert usage == 1

        # Get usage logs
        logs = await service.usage_log_repo.get_usage_by_session(session_id=session_id)
        assert len(logs) == 1
        assert logs[0].execution_time_ms == 1500.0
        assert logs[0].verification_status == "verified"
        assert logs[0].patch_success is True


@pytest.mark.asyncio
async def test_get_remaining_requests():
    """Test getting remaining requests."""
    async with get_db_session() as session:
        service = UsageLimitService(session)
        session_id = "test_session_remaining"

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
async def test_get_usage_analytics():
    """Test usage analytics generation."""
    async with get_db_session() as session:
        service = UsageLimitService(session)
        session_id = "test_session_analytics"

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

        assert analytics["total_requests"] == 3
        assert analytics["successful_patches"] == 2
        assert analytics["verified_requests"] == 2
        assert analytics["avg_execution_time_ms"] > 0
        assert analytics["days_analyzed"] == 30


@pytest.mark.asyncio
async def test_daily_usage_reset():
    """Test that daily usage resets correctly."""
    async with get_db_session() as session:
        service = UsageLimitService(session)
        session_id = "test_session_reset"

        # Record usage today
        await service.record_usage(
            session_id=session_id,
            tier=SubscriptionTier.FREE.value,
            execution_time_ms=1000.0,
        )

        # Check current usage
        current = await service.usage_log_repo.get_daily_usage(session_id=session_id)
        assert current == 1

        # Check usage for yesterday (should be 0)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        yesterday_usage = await service.usage_log_repo.get_daily_usage(
            session_id=session_id, date=yesterday
        )
        assert yesterday_usage == 0


@pytest.mark.asyncio
async def test_user_specific_usage():
    """Test usage tracking for specific users."""
    async with get_db_session() as session:
        # Create a user
        sub_repo = SubscriptionRepository(session)
        free_plan = await sub_repo.get_by_tier(SubscriptionTier.FREE.value)

        user_repo = type(
            "UserRepo",
            (),
            {
                "create_user": lambda email, display_name, subscription_plan_id: User(
                    email=email,
                    display_name=display_name,
                    subscription_plan_id=subscription_plan_id,
                )
            },
        )()

        user = user_repo.create_user(
            email="user@example.com",
            display_name="Test User",
            subscription_plan_id=free_plan.id if free_plan else None,
        )
        session.add(user)
        await session.flush()

        service = UsageLimitService(session)
        session_id = "user_session_123"

        # Record usage for user
        await service.record_usage(
            session_id=session_id,
            tier=SubscriptionTier.FREE.value,
            user_id=user.id,
            execution_time_ms=1000.0,
        )

        # Check user-specific usage
        user_usage = await service.usage_log_repo.get_daily_usage(
            session_id=session_id, user_id=user.id
        )
        assert user_usage == 1

        # Get user analytics
        analytics = await service.get_usage_analytics(user_id=user.id, days=30)
        assert analytics["total_requests"] == 1
