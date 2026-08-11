"""
API routes for workspace and project management.

Handles project CRUD operations for authenticated users.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import get_db_session
from database.models import Project
from middleware.auth import get_current_user_required
from repositories.project_repository import ProjectRepository
from utils.logging import get_logger

logger = get_logger("neurodebug.routes.workspace")

router = APIRouter()


# ──────────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────────


class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""

    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: str | None = Field(None, description="Optional project description")


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project."""

    name: str | None = Field(
        None, min_length=1, max_length=200, description="Project name"
    )
    description: str | None = Field(None, description="Project description")


class ProjectResponse(BaseModel):
    """Response model for project data."""

    project_id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    description: str | None
    created_at: str
    updated_at: str
    is_archived: bool


class ProjectsListResponse(BaseModel):
    """Response model for projects list."""

    projects: list[ProjectResponse]
    total: int


# ──────────────────────────────────────────────────────────────────
# Route Handlers
# ──────────────────────────────────────────────────────────────────


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: CreateProjectRequest,
    current_user: dict = Depends(get_current_user_required),
):
    """
    Create a new project for the authenticated user.

    Args:
        request: Project creation request.
        current_user: Current authenticated user from middleware.

    Returns:
        ProjectResponse with created project data.

    Raises:
        HTTPException: If project creation fails.
    """
    async with get_db_session() as session:
        try:
            project_repo = ProjectRepository(session)

            # Create project
            project = await project_repo.create_project(
                user_id=current_user["user_id"],
                name=request.name,
                description=request.description,
            )

            logger.info(
                "Project created: %s for user: %s", project.id, current_user["user_id"]
            )

            return ProjectResponse(
                project_id=project.id,
                user_id=project.user_id,
                name=project.name,
                description=project.description,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat(),
                is_archived=project.deleted_at is not None,
            )

        except Exception:
            logger.exception("Failed to create project")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": "Failed to create project",
                },
            )


@router.get("/projects", response_model=ProjectsListResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 50,
    include_archived: bool = False,
    current_user: dict = Depends(get_current_user_required),
):
    """
    List all projects for the authenticated user.

    Args:
        skip: Number of projects to skip (pagination).
        limit: Maximum number of projects to return.
        include_archived: Whether to include archived projects.
        current_user: Current authenticated user from middleware.

    Returns:
        ProjectsListResponse with list of projects.
    """
    async with get_db_session() as session:
        try:
            project_repo = ProjectRepository(session)

            # Get projects
            projects = await project_repo.get_user_projects(
                user_id=current_user["user_id"],
                skip=skip,
                limit=limit,
                include_archived=include_archived,
            )

            # Get total count
            total = await project_repo.count_user_projects(
                user_id=current_user["user_id"],
                include_archived=include_archived,
            )

            project_responses = [
                ProjectResponse(
                    project_id=p.id,
                    user_id=p.user_id,
                    name=p.name,
                    description=p.description,
                    created_at=p.created_at.isoformat(),
                    updated_at=p.updated_at.isoformat(),
                    is_archived=p.deleted_at is not None,
                )
                for p in projects
            ]

            return ProjectsListResponse(projects=project_responses, total=total)

        except Exception:
            logger.exception("Failed to list projects")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": "Failed to list projects",
                },
            )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: dict = Depends(get_current_user_required),
):
    """
    Get a specific project by ID.

    Args:
        project_id: UUID of the project.
        current_user: Current authenticated user from middleware.

    Returns:
        ProjectResponse with project data.

    Raises:
        HTTPException: If project not found or access denied.
    """
    async with get_db_session() as session:
        try:
            project_repo = ProjectRepository(session)

            # Get project
            project = await project_repo.get_by_id(project_id)

            if not project:
                logger.warning("Project not found: %s", project_id)
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Project not found"},
                )

            # Check ownership
            if project.user_id != current_user["user_id"]:
                logger.warning(
                    "Access denied to project: %s for user: %s",
                    project_id,
                    current_user["user_id"],
                )
                raise HTTPException(
                    status_code=403,
                    detail={"error": "access_denied", "message": "Access denied"},
                )

            return ProjectResponse(
                project_id=project.id,
                user_id=project.user_id,
                name=project.name,
                description=project.description,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat(),
                is_archived=project.deleted_at is not None,
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to get project")
            raise HTTPException(
                status_code=500,
                detail={"error": "internal_error", "message": "Failed to get project"},
            )


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    request: UpdateProjectRequest,
    current_user: dict = Depends(get_current_user_required),
):
    """
    Update a project.

    Args:
        project_id: UUID of the project.
        request: Project update request.
        current_user: Current authenticated user from middleware.

    Returns:
        ProjectResponse with updated project data.

    Raises:
        HTTPException: If project not found or access denied.
    """
    async with get_db_session() as session:
        try:
            project_repo = ProjectRepository(session)

            # Get project
            project = await project_repo.get_by_id(project_id)

            if not project:
                logger.warning("Project not found: %s", project_id)
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Project not found"},
                )

            # Check ownership
            if project.user_id != current_user["user_id"]:
                logger.warning(
                    "Access denied to project: %s for user: %s",
                    project_id,
                    current_user["user_id"],
                )
                raise HTTPException(
                    status_code=403,
                    detail={"error": "access_denied", "message": "Access denied"},
                )

            # Update project
            updated_project = await project_repo.update_project(
                project_id=project_id,
                name=request.name,
                description=request.description,
            )

            logger.info("Project updated: %s", project_id)

            return ProjectResponse(
                project_id=updated_project.id,
                user_id=updated_project.user_id,
                name=updated_project.name,
                description=updated_project.description,
                created_at=updated_project.created_at.isoformat(),
                updated_at=updated_project.updated_at.isoformat(),
                is_archived=updated_project.deleted_at is not None,
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to update project")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": "Failed to update project",
                },
            )


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    current_user: dict = Depends(get_current_user_required),
):
    """
    Soft delete (archive) a project.

    Args:
        project_id: UUID of the project.
        current_user: Current authenticated user from middleware.

    Returns:
        Success message.

    Raises:
        HTTPException: If project not found or access denied.
    """
    async with get_db_session() as session:
        try:
            project_repo = ProjectRepository(session)

            # Get project
            project = await project_repo.get_by_id(project_id)

            if not project:
                logger.warning("Project not found: %s", project_id)
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Project not found"},
                )

            # Check ownership
            if project.user_id != current_user["user_id"]:
                logger.warning(
                    "Access denied to project: %s for user: %s",
                    project_id,
                    current_user["user_id"],
                )
                raise HTTPException(
                    status_code=403,
                    detail={"error": "access_denied", "message": "Access denied"},
                )

            # Archive project
            await project_repo.archive_project(project_id)

            logger.info("Project archived: %s", project_id)

            return {"message": "Project archived successfully"}

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to archive project")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": "Failed to archive project",
                },
            )


@router.post("/projects/{project_id}/restore")
async def restore_project(
    project_id: uuid.UUID,
    current_user: dict = Depends(get_current_user_required),
):
    """
    Restore a previously archived project.

    Args:
        project_id: UUID of the project.
        current_user: Current authenticated user from middleware.

    Returns:
        Success message.

    Raises:
        HTTPException: If project not found or access denied.
    """
    async with get_db_session() as session:
        try:
            project_repo = ProjectRepository(session)

            # Get project
            project = await project_repo.get_by_id(project_id, include_archived=True)

            if not project:
                logger.warning("Project not found: %s", project_id)
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Project not found"},
                )

            # Check ownership
            if project.user_id != current_user["user_id"]:
                logger.warning(
                    "Access denied to project: %s for user: %s",
                    project_id,
                    current_user["user_id"],
                )
                raise HTTPException(
                    status_code=403,
                    detail={"error": "access_denied", "message": "Access denied"},
                )

            # Restore project
            await project_repo.restore_project(project_id)

            logger.info("Project restored: %s", project_id)

            return {"message": "Project restored successfully"}

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to restore project")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": "Failed to restore project",
                },
            )
