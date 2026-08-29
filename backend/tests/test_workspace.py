import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Project
from repositories.project_repository import ProjectRepository
from services.workspace_service import WorkspaceService
import uuid


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for workspace tests."""
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
def project_repository(db_session: AsyncSession):
    """Create a project repository instance."""
    return ProjectRepository(db_session)


@pytest.fixture
def workspace_service(project_repository: ProjectRepository):
    """Create a workspace service instance."""
    return WorkspaceService(project_repository)


class TestProjectRepository:
    """Test project repository methods."""

    @pytest.mark.asyncio
    async def test_create_project(
        self, project_repository: ProjectRepository, test_user: User
    ):
        """Test creating a new project."""
        project = await project_repository.create_project(
            name="Test Project", user_id=test_user.id, description="A test project"
        )

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.user_id == test_user.id
        assert project.deleted_at is None

    @pytest.mark.asyncio
    async def test_get_project_by_id(
        self, project_repository: ProjectRepository, test_user: User
    ):
        """Test retrieving a project by ID."""
        created_project = await project_repository.create_project(
            user_id=test_user.id, name="Test Project"
        )

        retrieved_project = await project_repository.get_by_id(
            created_project.id
        )

        assert retrieved_project.id == created_project.id
        assert retrieved_project.name == "Test Project"

    @pytest.mark.asyncio
    async def test_get_projects_by_user(
        self, project_repository: ProjectRepository, test_user: User
    ):
        """Test retrieving all projects for a user."""
        await project_repository.create_project(name="Project 1", user_id=test_user.id)
        await project_repository.create_project(name="Project 2", user_id=test_user.id)
        await project_repository.create_project(name="Project 3", user_id=test_user.id)

        projects = await project_repository.get_by_user(test_user.id)

        assert len(projects) == 3
        project_names = [p.name for p in projects]
        assert "Project 1" in project_names
        assert "Project 2" in project_names
        assert "Project 3" in project_names

    @pytest.mark.asyncio
    async def test_update_project(
        self, project_repository: ProjectRepository, test_user: User
    ):
        """Test updating a project."""
        project = await project_repository.create_project(name="Original Name", user_id=test_user.id)

        updated_project = await project_repository.update_project(
            project_id=project.id,
            name="Updated Name",
            description="Updated description",
        )

        assert updated_project.name == "Updated Name"
        assert updated_project.description == "Updated description"

    @pytest.mark.asyncio
    async def test_archive_project(
        self, project_repository: ProjectRepository, test_user: User
    ):
        """Test archiving a project."""
        project = await project_repository.create_project(name="Test Project", user_id=test_user.id)

        archived_project = await project_repository.archive_project(project.id)

        assert archived_project.deleted_at is not None

    @pytest.mark.asyncio
    async def test_restore_project(
        self, project_repository: ProjectRepository, test_user: User
    ):
        """Test restoring an archived project."""
        project = await project_repository.create_project(name="Test Project", user_id=test_user.id)
        await project_repository.archive_project(project.id)

        restored_project = await project_repository.restore_project(project.id)

        assert restored_project.deleted_at is None

    @pytest.mark.asyncio
    async def test_delete_project(
        self, project_repository: ProjectRepository, test_user: User
    ):
        """Test soft deleting a project."""
        project = await project_repository.create_project(name="Test Project", user_id=test_user.id)

        result = await project_repository.delete(project.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_projects_excludes_archived(
        self, project_repository: ProjectRepository, test_user: User
    ):
        """Test that archived projects are excluded by default."""
        await project_repository.create_project(name="Active Project", user_id=test_user.id)
        archived = await project_repository.create_project(name="Archived Project", user_id=test_user.id)
        await project_repository.archive_project(archived.id)

        projects = await project_repository.get_user_projects(test_user.id, include_archived=False)

        assert len(projects) == 1
        assert projects[0].name == "Active Project"


class TestWorkspaceService:
    """Test workspace service methods."""

    @pytest.mark.asyncio
    async def test_create_project_service(
        self, workspace_service: WorkspaceService, test_user: User
    ):
        """Test creating a project through service layer."""
        project = await workspace_service.create_project(
            user_id=test_user.id,
            name="Service Test Project",
            description="Created via service",
        )

        assert project.name == "Service Test Project"
        assert project.description == "Created via service"

    @pytest.mark.asyncio
    async def test_list_projects_service(
        self, workspace_service: WorkspaceService, test_user: User
    ):
        """Test listing projects through service layer."""
        await workspace_service.create_project(user_id=test_user.id, name="Project 1")
        await workspace_service.create_project(user_id=test_user.id, name="Project 2")

        projects = await workspace_service.list_projects(user_id=test_user.id)

        assert len(projects) == 2

    @pytest.mark.asyncio
    async def test_update_project_service(
        self, workspace_service: WorkspaceService, test_user: User
    ):
        """Test updating project through service layer."""
        project = await workspace_service.create_project(
            user_id=test_user.id, name="Original"
        )

        updated = await workspace_service.update_project(
            project_id=project.id, name="Updated", description="New description"
        )

        assert updated.name == "Updated"

    @pytest.mark.asyncio
    async def test_archive_project_service(
        self, workspace_service: WorkspaceService, test_user: User
    ):
        """Test archiving project through service layer."""
        project = await workspace_service.create_project(
            user_id=test_user.id, name="To Archive"
        )

        await workspace_service.archive_project(project.id)

        projects = await workspace_service.list_projects(user_id=test_user.id)
        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_delete_project_service(
        self, workspace_service: WorkspaceService, test_user: User
    ):
        """Test deleting project through service layer."""
        project = await workspace_service.create_project(
            user_id=test_user.id, name="To Delete"
        )

        await workspace_service.delete_project(project.id)

        projects = await workspace_service.list_projects(
            user_id=test_user.id, include_archived=True
        )
        assert len(projects) == 1
        assert projects[0].deleted_at is not None
