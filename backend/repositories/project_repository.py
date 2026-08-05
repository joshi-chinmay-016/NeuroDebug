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
