"""
Service for debug session history management.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from repositories.debug_session_repository import DebugSessionRepository


class HistoryService:
    """Service for debug session history operations."""

    def __init__(self, debug_session_repository: DebugSessionRepository):
        """
        Initialize history service.

        Args:
            debug_session_repository: Repository for debug session operations.
        """
        self.debug_session_repository = debug_session_repository

    async def list_sessions(
        self,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        project_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Any]:
        """
        List debug sessions with filters.

        Args:
            user_id: Optional user UUID.
            session_id: Optional session ID (for guest users).
            project_id: Optional project UUID to filter by.
            skip: Number of sessions to skip.
            limit: Maximum number of sessions to return.

        Returns:
            List of debug sessions.
        """
        if user_id:
            return await self.debug_session_repository.get_user_debug_sessions(
                user_id=user_id, skip=skip, limit=limit, project_id=project_id
            )
        elif session_id:
            return await self.debug_session_repository.get_by_session(session_id)
        else:
            return []

    async def get_session_by_id(
        self,
        session_id: uuid.UUID,
    ) -> Any | None:
        """
        Get a debug session by ID with details.

        Args:
            session_id: UUID of the debug session.

        Returns:
            Debug session instance with details or None.
        """
        return await self.debug_session_repository.get_session_with_details(session_id)

    async def search_sessions(
        self,
        user_id: uuid.UUID,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Any]:
        """
        Search debug sessions by code content.

        Args:
            user_id: UUID of the user.
            query: Search query string.
            skip: Number of sessions to skip.
            limit: Maximum number of sessions to return.

        Returns:
            List of matching debug sessions.
        """
        # Get all sessions for the user
        sessions = await self.debug_session_repository.get_user_debug_sessions(
            user_id=user_id, skip=skip, limit=limit
        )

        # Filter by query (simple substring search)
        if query:
            query_lower = query.lower()
            sessions = [
                session
                for session in sessions
                if query_lower in session.code.lower()
                or (session.error_type and query_lower in session.error_type.lower())
            ]

        return sessions

    async def filter_by_status(
        self,
        user_id: uuid.UUID,
        has_patch: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Any]:
        """
        Filter debug sessions by patch status.

        Args:
            user_id: UUID of the user.
            has_patch: Filter by whether session has a patch (None = no filter).
            skip: Number of sessions to skip.
            limit: Maximum number of sessions to return.

        Returns:
            List of filtered debug sessions.
        """
        from sqlalchemy.orm import selectinload

        sessions = await self.debug_session_repository.get_user_debug_sessions(
            user_id=user_id, skip=skip, limit=limit
        )

        # Load candidate_patches relationship to avoid lazy loading
        for session in sessions:
            await self.debug_session_repository.session.refresh(
                session, attribute_names=["candidate_patches"]
            )

        if has_patch is not None:
            sessions = [
                session
                for session in sessions
                if (len(session.candidate_patches) > 0) == has_patch
            ]

        return sessions

    async def export_session(
        self,
        session_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Export a debug session as a structured dictionary.

        Args:
            session_id: UUID of the debug session.

        Returns:
            Dictionary with session data.
        """
        session = await self.debug_session_repository.get_session_with_details(
            session_id
        )

        if not session:
            return {}

        return {
            "id": str(session.id),
            "session_id": session.session_id,
            "code": session.code,
            "error_type": session.error_type,
            "confidence_score": session.confidence_score,
            "pipeline_duration_ms": session.pipeline_duration_ms,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "candidate_patches": [
                {
                    "id": str(patch.id),
                    "patch_code": patch.patch_code,
                    "explanation": patch.explanation,
                    "confidence_score": patch.confidence_score,
                }
                for patch in session.candidate_patches
            ],
            "verification_reports": [
                {
                    "id": str(report.id),
                    "status": report.status,
                    "stdout": report.stdout,
                    "stderr": report.stderr,
                    "execution_time_ms": report.execution_time_ms,
                }
                for report in session.verification_reports
            ],
        }

    async def get_session_statistics(
        self,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Get statistics for a user's debug sessions.

        Args:
            user_id: UUID of the user.

        Returns:
            Dictionary with session statistics.
        """
        sessions = await self.debug_session_repository.get_user_debug_sessions(
            user_id=user_id, limit=1000
        )

        # Load candidate_patches relationship to avoid lazy loading
        for session in sessions:
            await self.debug_session_repository.session.refresh(
                session, attribute_names=["candidate_patches"]
            )

        total_sessions = len(sessions)
        sessions_with_patches = sum(1 for s in sessions if len(s.candidate_patches) > 0)
        avg_confidence = (
            sum(
                s.candidate_patches[0].confidence_score or 0
                for s in sessions
                if s.candidate_patches and s.candidate_patches[0].confidence_score
            )
            / sessions_with_patches
            if sessions_with_patches > 0
            else 0
        )

        # Count by error type
        error_types = {}
        for session in sessions:
            if session.error_type:
                error_types[session.error_type] = error_types.get(session.error_type, 0) + 1

        return {
            "total_sessions": total_sessions,
            "sessions_with_patches": sessions_with_patches,
            "sessions_without_patches": total_sessions - sessions_with_patches,
            "avg_confidence_score": round(avg_confidence, 2),
            "error_types": error_types,
        }
