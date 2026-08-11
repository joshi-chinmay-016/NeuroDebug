"""
Repository for debug session management operations.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import DebugSession
from repositories.base import BaseRepository


class DebugSessionRepository(BaseRepository[DebugSession, Any, Any]):
    """Repository for debug session operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize debug session repository.

        Args:
            session: Async database session.
        """
        super().__init__(DebugSession, session)

    async def get_by_user(self, user_id: uuid.UUID) -> list[DebugSession]:
        """
        Get all debug sessions for a specific user.

        Args:
            user_id: UUID of the user.

        Returns:
            List of DebugSession instances.
        """
        result = await self.session.execute(
            select(DebugSession)
            .where(DebugSession.user_id == user_id)
            .order_by(DebugSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_session(self, session_id: str) -> list[DebugSession]:
        """
        Get all debug sessions for a specific session ID (guest users).

        Args:
            session_id: Session ID string.

        Returns:
            List of DebugSession instances.
        """
        result = await self.session.execute(
            select(DebugSession)
            .where(DebugSession.session_id == session_id)
            .order_by(DebugSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_project(self, project_id: uuid.UUID) -> list[DebugSession]:
        """
        Get all debug sessions for a specific project.

        Args:
            project_id: UUID of the project.

        Returns:
            List of DebugSession instances.
        """
        result = await self.session.execute(
            select(DebugSession)
            .where(DebugSession.project_id == project_id)
            .order_by(DebugSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_debug_session(
        self,
        session_id: str,
        code: str,
        user_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        error_type: str | None = None,
        confidence_score: float | None = None,
        pipeline_duration_ms: float | None = None,
    ) -> DebugSession:
        """
        Create a new debug session.

        Args:
            session_id: Session ID string.
            code: Source code being debugged.
            user_id: Optional user UUID.
            project_id: Optional project UUID.
            error_type: Optional detected error type.
            confidence_score: Optional confidence score.
            pipeline_duration_ms: Optional pipeline duration in milliseconds.

        Returns:
            Created DebugSession instance.
        """
        debug_session = DebugSession(
            session_id=session_id,
            code=code,
            user_id=user_id,
            project_id=project_id,
            error_type=error_type,
            confidence_score=confidence_score,
            pipeline_duration_ms=pipeline_duration_ms,
        )
        self.session.add(debug_session)
        await self.session.flush()
        await self.session.refresh(debug_session)
        return debug_session

    async def get_user_debug_sessions(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        project_id: uuid.UUID | None = None,
    ) -> list[DebugSession]:
        """
        Get debug sessions for a user with pagination and optional project filter.

        Args:
            user_id: UUID of the user.
            skip: Number of sessions to skip.
            limit: Maximum number of sessions to return.
            project_id: Optional project UUID to filter by.

        Returns:
            List of DebugSession instances.
        """
        query = select(DebugSession).where(DebugSession.user_id == user_id)

        if project_id:
            query = query.where(DebugSession.project_id == project_id)

        query = query.order_by(DebugSession.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_user_debug_sessions(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID | None = None,
    ) -> int:
        """
        Count debug sessions for a user.

        Args:
            user_id: UUID of the user.
            project_id: Optional project UUID to filter by.

        Returns:
            Count of debug sessions.
        """
        from sqlalchemy import func

        query = (
            select(func.count())
            .select_from(DebugSession)
            .where(DebugSession.user_id == user_id)
        )

        if project_id:
            query = query.where(DebugSession.project_id == project_id)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_session_with_details(
        self,
        session_id: uuid.UUID,
    ) -> DebugSession | None:
        """
        Get a debug session with all related data (patches, verification reports).

        Args:
            session_id: UUID of the debug session.

        Returns:
            DebugSession instance with loaded relationships or None.
        """
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            select(DebugSession)
            .where(DebugSession.id == session_id)
            .options(
                selectinload(DebugSession.candidate_patches),
                selectinload(DebugSession.verification_reports),
            )
        )
        return result.scalar_one_or_none()
