import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, UsageLog
from repositories.usage_log_repository import UsageLogRepository
from services.analytics_service import AnalyticsService
from datetime import datetime, timedelta
import uuid


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for analytics tests."""
    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_password",
        display_name="Test User",
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def usage_log_repository(db_session: AsyncSession):
    """Create a usage log repository instance."""
    return UsageLogRepository(db_session)


@pytest.fixture
def analytics_service(usage_log_repository: UsageLogRepository):
    """Create an analytics service instance."""
    return AnalyticsService(usage_log_repository)


class TestUsageLogRepository:
    """Test usage log repository methods."""

    @pytest.mark.asyncio
    async def test_create_usage_log(
        self, usage_log_repository: UsageLogRepository, test_user: User
    ):
        """Test creating a usage log entry."""
        log = await usage_log_repository.create_usage_log(
            user_id=test_user.id,
            session_id="test-session-123",
            execution_time_ms=100.0,
            subscription_tier="free",
        )

        assert log.id is not None
        assert log.user_id == test_user.id
        assert log.session_id == "test-session-123"
        assert log.subscription_tier == "free"

    @pytest.mark.asyncio
    async def test_get_usage_logs_by_user(
        self, usage_log_repository: UsageLogRepository, test_user: User
    ):
        """Test retrieving usage logs for a user."""
        await usage_log_repository.create_usage_log(
            user_id=test_user.id, session_id="session-1", execution_time_ms=100.0, subscription_tier="free"
        )
        await usage_log_repository.create_usage_log(
            user_id=test_user.id, session_id="session-2", execution_time_ms=100.0, subscription_tier="free"
        )

        logs = await usage_log_repository.get_usage_by_user(test_user.id)

        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_get_usage_count_by_date_range(
        self, usage_log_repository: UsageLogRepository, test_user: User
    ):
        """Test getting usage logs within a date range."""
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        await usage_log_repository.create_usage_log(
            user_id=test_user.id,
            session_id="session-1",
            execution_time_ms=100.0,
            subscription_tier="free",
        )
        await usage_log_repository.create_usage_log(
            user_id=test_user.id,
            session_id="session-2",
            execution_time_ms=100.0,
            subscription_tier="free",
        )

        logs = await usage_log_repository.get_usage_by_user(
            test_user.id, start_date=yesterday, end_date=today + timedelta(days=1)
        )

        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_get_daily_usage(
        self, usage_log_repository: UsageLogRepository, test_user: User
    ):
        """Test getting daily usage statistics for a session."""
        today = datetime.now()
        session_id = "test-session-123"

        for i in range(5):
            await usage_log_repository.create_usage_log(
                user_id=test_user.id,
                session_id=session_id,
                execution_time_ms=100.0,
                subscription_tier="free",
            )

        daily_usage = await usage_log_repository.get_daily_usage(session_id, test_user.id, today)

        assert daily_usage == 5


@pytest.mark.skip(reason="AnalyticsService not implemented yet")
class TestAnalyticsService:
    """Test analytics service methods."""

    @pytest.mark.asyncio
    async def test_get_user_analytics(
        self, analytics_service: AnalyticsService, test_user: User
    ):
        """Test getting user analytics."""
        today = datetime.utcnow()

        # Create some usage logs
        for i in range(10):
            await analytics_service.log_usage(
                user_id=test_user.id,
                session_id=f"session-{i}",
                subscription_tier="free",
                request_timestamp=today,
            )

        analytics = await analytics_service.get_user_analytics(test_user.id)

        assert analytics["total_requests"] == 10
        assert "subscription_tier" in analytics

    @pytest.mark.asyncio
    async def test_get_usage_trends(
        self, analytics_service: AnalyticsService, test_user: User
    ):
        """Test getting usage trends over time."""
        today = datetime.utcnow()

        # Create usage logs for past 7 days
        for day in range(7):
            date = today - timedelta(days=day)
            for i in range(3):
                await analytics_service.log_usage(
                    user_id=test_user.id,
                    session_id=f"session-{day}-{i}",
                    subscription_tier="free",
                    request_timestamp=date,
                )

        trends = await analytics_service.get_usage_trends(test_user.id, days=7)

        assert len(trends) == 7
        assert all("date" in trend for trend in trends)
        assert all("count" in trend for trend in trends)

    @pytest.mark.asyncio
    async def test_get_success_rate(
        self, analytics_service: AnalyticsService, test_user: User
    ):
        """Test calculating success rate."""
        # This would require debug session data with success/failure status
        # For now, test the method exists and returns a valid structure
        success_rate = await analytics_service.get_success_rate(test_user.id)

        assert isinstance(success_rate, float)
        assert 0 <= success_rate <= 1

    @pytest.mark.asyncio
    async def test_get_performance_metrics(
        self, analytics_service: AnalyticsService, test_user: User
    ):
        """Test getting performance metrics."""
        metrics = await analytics_service.get_performance_metrics(test_user.id)

        assert "avg_response_time" in metrics
        assert "avg_ast_duration" in metrics
        assert "avg_llm_duration" in metrics

    @pytest.mark.asyncio
    async def test_get_subscription_analytics(
        self, analytics_service: AnalyticsService
    ):
        """Test getting subscription-level analytics."""
        analytics = await analytics_service.get_subscription_analytics()

        assert "total_users" in analytics
        assert "active_users" in analytics
        assert "tier_distribution" in analytics

    @pytest.mark.asyncio
    async def test_log_usage(
        self, analytics_service: AnalyticsService, test_user: User
    ):
        """Test logging usage."""
        await analytics_service.log_usage(
            user_id=test_user.id, session_id="test-session", subscription_tier="free"
        )

        # Verify the log was created
        logs = await analytics_service.repository.get_usage_logs_by_user(test_user.id)
        assert len(logs) == 1
        assert logs[0].session_id == "test-session"

    @pytest.mark.asyncio
    async def test_get_aggregate_analytics(self, analytics_service: AnalyticsService):
        """Test getting aggregate analytics across all users."""
        analytics = await analytics_service.get_aggregate_analytics()

        assert "total_requests" in analytics
        assert "success_rate" in analytics
        assert "avg_response_time" in analytics
