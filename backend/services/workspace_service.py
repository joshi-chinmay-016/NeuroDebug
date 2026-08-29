"""
Service for workspace and project management.
"""

import uuid
from typing import Any

from repositories.project_repository import ProjectRepository


class WorkspaceService:
    """Service for workspace and project operations."""

    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize workspace service.

        Args:
            project_repository: Repository for project operations.
        """
        self.project_repository = project_repository

    async def create_project(
        self,
        name: str,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        description: str | None = None,
    ) -> Any:
        """
        Create a new project.

        Args:
            name: Project name.
            user_id: Optional user UUID (for authenticated users).
            session_id: Optional session ID (for guest users).
            description: Optional project description.

        Returns:
            Created project instance.
        """
        return await self.project_repository.create_project(
            name=name,
            user_id=user_id,
            session_id=session_id,
            description=description,
        )

    async def list_projects(
        self,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
        include_archived: bool = False,
    ) -> list[Any]:
        """
        List projects with filters.

        Args:
            user_id: Optional user UUID.
            session_id: Optional session ID (for guest users).
            skip: Number of projects to skip.
            limit: Maximum number of projects to return.
            include_archived: Whether to include archived projects.

        Returns:
            List of projects.
        """
        if user_id:
            return await self.project_repository.get_user_projects(
                user_id=user_id,
                skip=skip,
                limit=limit,
                include_archived=include_archived,
            )
        elif session_id:
            return await self.project_repository.get_by_session(session_id)
        else:
            return []

    async def update_project(
        self,
        project_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Any | None:
        """
        Update a project.

        Args:
            project_id: UUID of the project.
            name: Optional new name.
            description: Optional new description.

        Returns:
            Updated project instance or None if not found.
        """
        return await self.project_repository.update_project(
            project_id=project_id,
            name=name,
            description=description,
        )

    async def archive_project(
        self,
        project_id: uuid.UUID,
    ) -> Any:
        """
        Archive (soft delete) a project.

        Args:
            project_id: UUID of the project.

        Returns:
            Archived project instance.
        """
        return await self.project_repository.archive_project(project_id)

    async def restore_project(
        self,
        project_id: uuid.UUID,
    ) -> Any:
        """
        Restore a previously archived project.

        Args:
            project_id: UUID of the project.

        Returns:
            Restored project instance.
        """
        return await self.project_repository.restore_project(project_id)

    async def delete_project(
        self,
        project_id: uuid.UUID,
    ) -> bool:
        """
        Delete a project.

        Args:
            project_id: UUID of the project.

        Returns:
            True if successful, False otherwise.
        """
        return await self.project_repository.delete(project_id)

    async def get_project_statistics(
        self,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Get statistics for a user's projects.

        Args:
            user_id: UUID of the user.

        Returns:
            Dictionary with project statistics.
        """
        total_projects = await self.project_repository.count_user_projects(
            user_id=user_id, include_archived=False
        )
        archived_projects = await self.project_repository.count_user_projects(
            user_id=user_id, include_archived=True
        ) - total_projects

        return {
            "total_projects": total_projects,
            "active_projects": total_projects,
            "archived_projects": archived_projects,
        }
