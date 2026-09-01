import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Project, DebugSession
from repositories.debug_session_repository import DebugSessionRepository
from services.history_service import HistoryService
import uuid
from datetime import datetime, timedelta


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for history tests."""
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


@pytest_asyncio.fixture
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
            session_id="test-session-123",
            code="def example():\n    return 42",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="NameError",
        )

        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.project_id == test_project.id
        assert session.session_id == "test-session-123"
        assert session.error_type == "NameError"

    @pytest.mark.asyncio
    async def test_create_debug_session_with_patch_and_verification(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test creating a debug session with candidate patch and verification report."""
        session = await session_repository.create_debug_session(
            session_id="test-session-with-patch",
            code="def add(a, b):\n    return a - b",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="LogicError",
            candidate_patch={
                "original_code": "def add(a, b):\n    return a - b",
                "patched_code": "def add(a, b):\n    return a + b",
                "diff": "+ return a + b\n- return a - b",
                "validation_passed": True,
                "explanation": "Fixed operator sign",
            },
            verification_report={
                "verification_status": "VERIFIED",
                "execution_summary": "Tests passed 1/1",
                "runtime_seconds": 1,
            },
        )

        assert session.id is not None
        assert session.error_type == "LogicError"

    @pytest.mark.asyncio
    async def test_get_session_by_id(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test retrieving a session by ID."""
        created_session = await session_repository.create_debug_session(
            session_id="test-session-123",
            code="def example():\n    return 42",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="NameError",
        )

        retrieved_session = await session_repository.get_by_id(
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
            session_id="session-1",
            code="code 1",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error1",
        )
        await session_repository.create_debug_session(
            session_id="session-2",
            code="code 2",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error2",
        )

        sessions = await session_repository.get_by_user(test_user.id)

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
            session_id="session-1",
            code="code 1",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error1",
        )

        sessions = await session_repository.get_by_project(test_project.id)

        assert len(sessions) == 1
        assert sessions[0].project_id == test_project.id

    @pytest.mark.asyncio
    async def test_update_session(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test updating a debug session."""
        session = await session_repository.create_debug_session(
            session_id="test-session",
            code="original code",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error",
        )

        session.error_type = "TypeError"
        await db_session.flush()
        await db_session.refresh(session)

        assert session.error_type == "TypeError"

    @pytest.mark.asyncio
    async def test_delete_session(
        self,
        session_repository: DebugSessionRepository,
        test_user: User,
        test_project: Project,
    ):
        """Test soft deleting a session."""
        session = await session_repository.create_debug_session(
            session_id="test-session",
            code="code",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error",
        )

        result = await session_repository.delete(session.id)
        assert result is True

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
                session_id=f"session-{i}",
                code=f"code {i}",
                user_id=test_user.id,
                project_id=test_project.id,
                error_type=f"Error{i}",
            )

        recent_sessions = await session_repository.get_user_debug_sessions(
            test_user.id, limit=3
        )

        assert len(recent_sessions) <= 3


class TestHistoryService:
    """Test history service methods."""

    @pytest.mark.asyncio
    async def test_list_sessions_service(
        self, history_service: HistoryService, test_user: User, test_project: Project, session_repository: DebugSessionRepository
    ):
        """Test listing sessions through service layer."""
        await session_repository.create_debug_session(
            session_id="session-1",
            code="code 1",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error1",
        )
        await session_repository.create_debug_session(
            session_id="session-2",
            code="code 2",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error2",
        )

        sessions = await history_service.list_sessions(user_id=test_user.id)

        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_get_session_by_id_service(
        self, history_service: HistoryService, test_user: User, test_project: Project, session_repository: DebugSessionRepository
    ):
        """Test retrieving session by ID through service layer."""
        created_session = await session_repository.create_debug_session(
            session_id="test-session",
            code="code",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error",
        )

        session = await history_service.get_session_by_id(created_session.id)

        assert session.session_id == "test-session"

    @pytest.mark.asyncio
    async def test_search_sessions(
        self, history_service: HistoryService, test_user: User, test_project: Project, session_repository: DebugSessionRepository
    ):
        """Test searching sessions by code or error."""
        await session_repository.create_debug_session(
            session_id="session-1",
            code="def foo(): return 42",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="NameError",
        )
        await session_repository.create_debug_session(
            session_id="session-2",
            code="def bar(): return 43",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="TypeError",
        )

        results = await history_service.search_sessions(test_user.id, "foo")

        assert len(results) == 1
        assert "foo" in results[0].code

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self, history_service: HistoryService, test_user: User, test_project: Project, session_repository: DebugSessionRepository
    ):
        """Test filtering sessions by patch status."""
        await session_repository.create_debug_session(
            session_id="session-1",
            code="code 1",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error1",
        )
        await session_repository.create_debug_session(
            session_id="session-2",
            code="code 2",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error2",
        )

        with_patch = await history_service.filter_by_status(test_user.id, has_patch=True)
        without_patch = await history_service.filter_by_status(test_user.id, has_patch=False)

        # Neither session has patches since we didn't create candidate patches
        assert len(with_patch) == 0
        assert len(without_patch) == 2

    @pytest.mark.asyncio
    async def test_export_session(
        self, history_service: HistoryService, test_user: User, test_project: Project, session_repository: DebugSessionRepository
    ):
        """Test exporting session data."""
        session = await session_repository.create_debug_session(
            session_id="test-session",
            code="code",
            user_id=test_user.id,
            project_id=test_project.id,
            error_type="Error",
        )

        exported = await history_service.export_session(session.id)

        assert exported["session_id"] == "test-session"
        assert exported["code"] == "code"

    @pytest.mark.asyncio
    async def test_get_session_statistics(
        self, history_service: HistoryService, test_user: User, test_project: Project, session_repository: DebugSessionRepository
    ):
        """Test getting session statistics."""
        for i in range(3):
            await session_repository.create_debug_session(
                session_id=f"session-{i}",
                code=f"code {i}",
                user_id=test_user.id,
                project_id=test_project.id,
                error_type=f"Error{i}",
            )

        stats = await history_service.get_session_statistics(test_user.id)

        assert stats["total_sessions"] >= 3
