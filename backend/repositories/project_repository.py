"""
Repository for project management operations.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project
from repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project, Any, Any]):
    """Repository for project operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize project repository.

        Args:
            session: Async database session.
        """
        super().__init__(Project, session)

    async def get_by_user(self, user_id: uuid.UUID) -> list[Project]:
        """
        Get all projects for a specific user.

        Args:
            user_id: UUID of the user.

        Returns:
            List of Project instances.
        """
        result = await self.session.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_session(self, session_id: str) -> list[Project]:
        """
        Get all projects for a specific session (guest users).

        Args:
            session_id: Session ID string.

        Returns:
            List of Project instances.
        """
        result = await self.session.execute(
            select(Project)
            .where(Project.session_id == session_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_project(
        self,
        name: str,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        description: str | None = None,
    ) -> Project:
        """
        Create a new project.

        Args:
            name: Project name.
            user_id: Optional user UUID (for authenticated users).
            session_id: Optional session ID (for guest users).
            description: Optional project description.

        Returns:
            Created Project instance.
        """
        project = Project(
            name=name,
            user_id=user_id,
            session_id=session_id,
            description=description,
        )
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def get_user_projects(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        include_archived: bool = False,
    ) -> list[Project]:
        """
        Get projects for a user with pagination.

        Args:
            user_id: UUID of the user.
            skip: Number of projects to skip.
            limit: Maximum number of projects to return.
            include_archived: Whether to include archived projects.

        Returns:
            List of Project instances.
        """
        query = select(Project).where(Project.user_id == user_id)

        if not include_archived:
            query = query.where(Project.deleted_at.is_(None))

        query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_user_projects(
        self,
        user_id: uuid.UUID,
        include_archived: bool = False,
    ) -> int:
        """
        Count projects for a user.

        Args:
            user_id: UUID of the user.
            include_archived: Whether to include archived projects.

        Returns:
            Count of projects.
        """
        from sqlalchemy import func

        query = (
            select(func.count()).select_from(Project).where(Project.user_id == user_id)
        )

        if not include_archived:
            query = query.where(Project.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update_project(
        self,
        project_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Project:
        """
        Update a project.

        Args:
            project_id: UUID of the project.
            name: Optional new name.
            description: Optional new description.

        Returns:
            Updated Project instance.
        """
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError("Project not found")

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description

        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def archive_project(self, project_id: uuid.UUID) -> Project:
        """
        Soft delete (archive) a project.

        Args:
            project_id: UUID of the project.

        Returns:
            Archived Project instance.
        """
        from datetime import datetime, timezone

        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError("Project not found")

        project.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def restore_project(self, project_id: uuid.UUID) -> Project:
        """
        Restore a previously archived project.

        Args:
            project_id: UUID of the project.

        Returns:
            Restored Project instance.
        """
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError("Project not found")

        project.deleted_at = None
        await self.session.flush()
        await self.session.refresh(project)
        return project
