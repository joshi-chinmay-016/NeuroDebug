"""
Tests for session service.
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import SubscriptionTier, User
from repositories.subscription_repository import SubscriptionRepository
from services.session_service import SessionService


@pytest.mark.asyncio
async def test_generate_session_id(db_session: AsyncSession):
    """Test session ID generation."""
    service = SessionService(db_session)

    session_id = service.generate_session_id()

    assert session_id is not None
    assert len(session_id) > 16
    assert isinstance(session_id, str)


@pytest.mark.asyncio
async def test_get_or_create_session_new(db_session: AsyncSession):
    """Test creating a new session."""
    service = SessionService(db_session)

    # Mock request and response
    class MockRequest:
        def __init__(self):
            self.cookies = {}
            self.headers = {}

    class MockResponse:
        def __init__(self):
            self.cookies = {}

        def set_cookie(self, key, value, **kwargs):
            self.cookies[key] = value

    request = MockRequest()
    response = MockResponse()

    # Get or create session (should create new)
    session_id, tier = await service.get_or_create_session(request, response)

    assert session_id is not None
    assert tier == SubscriptionTier.GUEST.value
    assert "neurodebug_session" in response.cookies


@pytest.mark.asyncio
async def test_get_or_create_session_existing(db_session: AsyncSession):
    """Test getting an existing session."""
    service = SessionService(db_session)

    class MockRequest:
        def __init__(self, session_id):
            self.cookies = {"neurodebug_session": session_id}
            self.headers = {}

    class MockResponse:
        def __init__(self):
            self.cookies = {}

        def set_cookie(self, key, value, **kwargs):
            self.cookies[key] = value

    existing_session_id = "existing_session_123"
    request = MockRequest(existing_session_id)
    response = MockResponse()

    # Get or create session (should use existing)
    session_id, tier = await service.get_or_create_session(request, response)

    assert session_id == existing_session_id
    assert tier == SubscriptionTier.GUEST.value


@pytest.mark.asyncio
async def test_set_session_cookie(db_session: AsyncSession):
    """Test setting session cookie."""
    service = SessionService(db_session)

    class MockResponse:
        def __init__(self):
            self.cookies = {}

        def set_cookie(self, key, value, **kwargs):
            self.cookies[key] = value

    response = MockResponse()
    service.set_session_cookie(response, "test_session_id")

    assert "neurodebug_session" in response.cookies
    assert response.cookies["neurodebug_session"] == "test_session_id"


@pytest.mark.asyncio
async def test_clear_session_cookie(db_session: AsyncSession):
    """Test clearing session cookie."""
    service = SessionService(db_session)

    class MockResponse:
        def __init__(self):
            self.deleted_cookies = []

        def delete_cookie(self, key, **kwargs):
            self.deleted_cookies.append(key)

    response = MockResponse()
    service.clear_session_cookie(response)

    assert "neurodebug_session" in response.deleted_cookies


@pytest.mark.asyncio
async def test_validate_session(db_session: AsyncSession):
    """Test session validation."""
    service = SessionService(db_session)

    # Valid session ID (long enough)
    is_valid, tier = await service.validate_session("valid_session_id_12345")
    assert is_valid is True
    assert tier == SubscriptionTier.GUEST.value

    # Invalid session ID (too short)
    is_valid, tier = await service.validate_session("short")
    assert is_valid is False
    assert tier == SubscriptionTier.GUEST.value

    # Empty session ID
    is_valid, tier = await service.validate_session("")
    assert is_valid is False
    assert tier == SubscriptionTier.GUEST.value


@pytest.mark.asyncio
async def test_check_rate_limit(db_session: AsyncSession):
    """Test rate limit checking."""
    service = SessionService(db_session)
    session_id = f"test_session_{uuid.uuid4()}"

    # Initially should be under limit
    allowed, current_usage, limit = await service.check_rate_limit(
        session_id=session_id, tier=SubscriptionTier.GUEST.value
    )
    assert allowed is True
    assert current_usage == 0
    assert limit == 1


@pytest.mark.asyncio
async def test_get_usage_info(db_session: AsyncSession):
    """Test getting usage info."""
    service = SessionService(db_session)
    session_id = f"test_session_{uuid.uuid4()}"

    # Record some usage
    for _ in range(2):
        await service.usage_limit_service.record_usage(
            session_id=session_id,
            tier=SubscriptionTier.FREE.value,
            execution_time_ms=1000.0,
        )

    # Get usage info
    usage_info = await service.get_usage_info(
        session_id=session_id, tier=SubscriptionTier.FREE.value
    )

    assert usage_info["remaining_requests"] >= 0
    assert usage_info["daily_limit"] == 5
    assert usage_info["tier"] == SubscriptionTier.FREE.value
    assert usage_info["session_id"] == session_id


@pytest.mark.asyncio
async def test_upgrade_session(db_session: AsyncSession):
    """Test upgrading from guest to authenticated session."""
    service = SessionService(db_session)

    # Create a user
    sub_repo = SubscriptionRepository(db_session)
    free_plan = await sub_repo.get_by_tier(SubscriptionTier.FREE.value)

    user = User(
        email=f"upgrade_{uuid.uuid4().hex[:8]}@example.com",
        display_name="Upgrade User",
        subscription_plan_id=free_plan.id if free_plan else None,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    class MockResponse:
        def __init__(self):
            self.cookies = {}

        def set_cookie(self, key, value, **kwargs):
            self.cookies[key] = value

    response = MockResponse()
    old_session_id = "guest_session_123"

    # Upgrade session
    new_session_id, tier = await service.upgrade_session(
        session_id=old_session_id, user_id=user.id, response=response
    )

    assert new_session_id != old_session_id
    assert tier == SubscriptionTier.FREE.value
    assert "neurodebug_session" in response.cookies
