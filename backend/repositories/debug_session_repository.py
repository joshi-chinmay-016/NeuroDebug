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
