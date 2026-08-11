import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import User, Project, DebugSession
from backend.repositories.debug_session_repository import DebugSessionRepository
from backend.services.history_service import HistoryService
import uuid
from datetime import datetime, timedelta


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for history tests."""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        display_name="Test User",
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: User):
    """Create a test project for history tests."""
    project = Project(
        user_id=test_user.id, name="Test Project", description="A test project"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
def session_repository(db_session: AsyncSession):
    """Create a debug session repository instance."""
    return DebugSessionRepository(db_session)


@pytest.fixture
def history_service(session_repository: DebugSessionRepository):
    """Create a history service instance."""
    return HistoryService(session_repository)


class TestDebugSessionRepository:
    """Test debug session repository methods."""

    @pytest.mark.asyncio
    async def test_create_debug_session(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test creating a new debug session."""
        session = await session_repository.create_debug_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="test-session-123",
            code="def example():\n    return 42",
            error_type="NameError",
            error_message="name 'undefined' is not defined",
        )

        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.project_id == test_project.id
        assert session.session_id == "test-session-123"
        assert session.error_type == "NameError"

    @pytest.mark.asyncio
    async def test_get_session_by_id(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test retrieving a session by ID."""
        created_session = await session_repository.create_debug_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="test-session-123",
            code="def example():\n    return 42",
            error_type="NameError",
        )

        retrieved_session = await session_repository.get_session_by_id(
            created_session.id
        )

        assert retrieved_session.id == created_session.id
        assert retrieved_session.session_id == "test-session-123"

    @pytest.mark.asyncio
    async def test_get_sessions_by_user(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test retrieving all sessions for a user."""
        await session_repository.create_debug_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="session-1",
            code="code 1",
            error_type="Error1",
        )
        await session_repository.create_debug_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="session-2",
            code="code 2",
            error_type="Error2",
        )

        sessions = await session_repository.get_sessions_by_user(test_user.id)

        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_get_sessions_by_project(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test retrieving sessions for a specific project."""
        await session_repository.create_debug_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="session-1",
            code="code 1",
            error_type="Error1",
        )

        sessions = await session_repository.get_sessions_by_project(test_project.id)

        assert len(sessions) == 1
        assert sessions[0].project_id == test_project.id

    @pytest.mark.asyncio
    async def test_update_session(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test updating a debug session."""
        session = await session_repository.create_debug_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="test-session",
            code="original code",
            error_type="Error",
        )

        updated_session = await session_repository.update_session(
            session_id=session.id, candidate_patch="fixed code", confidence_score=0.95
        )

        assert updated_session.candidate_patch == "fixed code"
        assert updated_session.confidence_score == 0.95

    @pytest.mark.asyncio
    async def test_delete_session(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test soft deleting a session."""
        session = await session_repository.create_debug_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="test-session",
            code="code",
            error_type="Error",
        )

        await session_repository.delete_session(session.id)

        deleted_session = await session_repository.get_session_by_id(
            session.id, include_deleted=True
        )
        assert deleted_session.deleted_at is not None

    @pytest.mark.asyncio
    async def test_get_recent_sessions(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test retrieving recent sessions with limit."""
        for i in range(5):
            await session_repository.create_debug_session(
                user_id=test_user.id,
                project_id=test_project.id,
                session_id=f"session-{i}",
                code=f"code {i}",
                error_type=f"Error{i}",
            )

        recent_sessions = await session_repository.get_recent_sessions(
            test_user.id, limit=3
        )

        assert len(recent_sessions) <= 3


class TestHistoryService:
    """Test history service methods."""

    @pytest.mark.asyncio
    async def test_list_sessions_service(
        self, history_service: HistoryService, test_user: User, test_project: Project
    ):
        """Test listing sessions through service layer."""
        await history_service.create_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="session-1",
            code="code 1",
            error_type="Error1",
        )
        await history_service.create_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="session-2",
            code="code 2",
            error_type="Error2",
        )

        sessions = await history_service.list_sessions(user_id=test_user.id)

        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_get_session_by_id_service(
        self, history_service: HistoryService, test_user: User, test_project: Project
    ):
        """Test retrieving session by ID through service layer."""
        created_session = await history_service.create_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="test-session",
            code="code",
            error_type="Error",
        )

        session = await history_service.get_session_by_id(created_session.id)

        assert session.session_id == "test-session"

    @pytest.mark.asyncio
    async def test_search_sessions(
        self, history_service: HistoryService, test_user: User, test_project: Project
    ):
        """Test searching sessions by code or error."""
        await history_service.create_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="session-1",
            code="def foo(): return bar",
            error_type="NameError",
        )
        await history_service.create_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="session-2",
            code="def baz(): return qux",
            error_type="TypeError",
        )

        results = await history_service.search_sessions(test_user.id, query="foo")

        assert len(results) == 1
        assert "foo" in results[0].code

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self, history_service: HistoryService, test_user: User, test_project: Project
    ):
        """Test filtering sessions by status."""
        session1 = await history_service.create_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="session-1",
            code="code 1",
            error_type="Error1",
        )
        await history_service.update_session(session1.id, status="success")

        session2 = await history_service.create_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="session-2",
            code="code 2",
            error_type="Error2",
        )
        await history_service.update_session(session2.id, status="failed")

        success_sessions = await history_service.filter_by_status(
            test_user.id, status="success"
        )
        failed_sessions = await history_service.filter_by_status(
            test_user.id, status="failed"
        )

        assert len(success_sessions) == 1
        assert len(failed_sessions) == 1

    @pytest.mark.asyncio
    async def test_export_session(
        self, history_service: HistoryService, test_user: User, test_project: Project
    ):
        """Test exporting session data."""
        session = await history_service.create_session(
            user_id=test_user.id,
            project_id=test_project.id,
            session_id="test-session",
            code="def example(): return 42",
            error_type="None",
            candidate_patch="def example(): return 43",
        )

        exported = await history_service.export_session(session.id)

        assert exported["session_id"] == "test-session"
        assert exported["code"] == "def example(): return 42"
        assert exported["candidate_patch"] == "def example(): return 43"

    @pytest.mark.asyncio
    async def test_get_session_statistics(
        self, history_service: HistoryService, test_user: User, test_project: Project
    ):
        """Test getting session statistics."""
        for i in range(3):
            session = await history_service.create_session(
                user_id=test_user.id,
                project_id=test_project.id,
                session_id=f"session-{i}",
                code=f"code {i}",
                error_type=f"Error{i}",
            )
            status = "success" if i % 2 == 0 else "failed"
            await history_service.update_session(session.id, status=status)

        stats = await history_service.get_session_statistics(test_user.id)

        assert stats["total_sessions"] == 3
        assert stats["success_count"] == 2
        assert stats["failed_count"] == 1
