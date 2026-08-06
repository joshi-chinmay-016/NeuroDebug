"""
Tests for session service.
"""

import pytest

from database import get_db_session
from database.models import SubscriptionTier, User
from repositories.subscription_repository import SubscriptionRepository
from services.session_service import SessionService


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_generate_session_id():
    """Test session ID generation."""
    async with get_db_session() as session:
        service = SessionService(session)

        session_id = service.generate_session_id()

        assert session_id is not None
        assert len(session_id) > 16
        assert isinstance(session_id, str)


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_get_or_create_session_new():
    """Test creating a new session."""
    async with get_db_session() as session:
        service = SessionService(session)

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


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_get_or_create_session_existing():
    """Test getting an existing session."""
    async with get_db_session() as session:
        service = SessionService(session)

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


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_set_session_cookie():
    """Test setting session cookie."""
    async with get_db_session() as session:
        service = SessionService(session)

        class MockResponse:
            def __init__(self):
                self.cookies = {}

            def set_cookie(self, key, value, **kwargs):
                self.cookies[key] = value
                self.cookie_args = kwargs

        response = MockResponse()
        session_id = "test_session_456"

        service.set_session_cookie(response, session_id)

        assert response.cookies["neurodebug_session"] == session_id
        assert response.cookie_args["httponly"] is True
        assert response.cookie_args["secure"] is False


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_clear_session_cookie():
    """Test clearing session cookie."""
    async with get_db_session() as session:
        service = SessionService(session)

        class MockResponse:
            def __init__(self):
                self.cookies = {}

            def delete_cookie(self, key, **kwargs):
                self.cookies[key] = None
                self.delete_args = kwargs

        response = MockResponse()

        service.clear_session_cookie(response)

        assert response.cookies["neurodebug_session"] is None


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_validate_session():
    """Test session validation."""
    async with get_db_session() as session:
        service = SessionService(session)

        # Valid session
        is_valid, tier = await service.validate_session("valid_session_123")
        assert is_valid is True
        assert tier == SubscriptionTier.GUEST.value

        # Invalid session (too short)
        is_valid, tier = await service.validate_session("short")
        assert is_valid is False
        assert tier == SubscriptionTier.GUEST.value


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_check_rate_limit():
    """Test rate limit checking."""
    async with get_db_session() as session:
        service = SessionService(session)
        session_id = "rate_limit_session"

        # Initially should be under limit
        allowed, current, limit = await service.check_rate_limit(
            session_id=session_id, tier=SubscriptionTier.GUEST.value
        )
        assert allowed is True
        assert current == 0
        assert limit == 3


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_get_usage_info():
    """Test getting usage information."""
    async with get_db_session() as session:
        service = SessionService(session)
        session_id = "usage_info_session"

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

        assert usage_info["remaining_requests"] == 3
        assert usage_info["daily_limit"] == 5
        assert usage_info["tier"] == SubscriptionTier.FREE.value
        assert usage_info["session_id"] == session_id


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_upgrade_session():
    """Test upgrading from guest to authenticated session."""
    async with get_db_session() as session:
        service = SessionService(session)

        # Create a user
        sub_repo = SubscriptionRepository(session)
        free_plan = await sub_repo.get_by_tier(SubscriptionTier.FREE.value)

        user = User(
            email="upgrade@example.com",
            display_name="Upgrade User",
            subscription_plan_id=free_plan.id if free_plan else None,
            email_verified=True,
        )
        session.add(user)
        await session.flush()

        class MockResponse:
            def __init__(self):
                self.cookies = {}

            def set_cookie(self, key, value, **kwargs):
                self.cookies[key] = value

        response = MockResponse()
        old_session_id = "guest_session_123"

        # Upgrade session
        new_session_id, tier = await service.upgrade_session(
            old_session_id=old_session_id, user_id=user.id, response=response
        )

        assert new_session_id != old_session_id
        assert tier == SubscriptionTier.FREE.value
        assert "neurodebug_session" in response.cookies
