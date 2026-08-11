"""
API routes for debug history management.

Handles listing, retrieving, and exporting debug sessions.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from database import get_db_session
from database.models import DebugSession
from middleware.auth import get_current_user_required
from repositories.debug_session_repository import DebugSessionRepository
from utils.logging import get_logger

logger = get_logger("neurodebug.routes.history")

router = APIRouter()


# ──────────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────────


class DebugSessionResponse(BaseModel):
    """Response model for debug session data."""

    session_id: uuid.UUID
    project_id: uuid.UUID | None
    code: str
    error_type: str | None
    confidence_score: float | None
    pipeline_duration_ms: float | None
    created_at: str
    updated_at: str


class DebugSessionDetailResponse(DebugSessionResponse):
    """Response model for debug session with full details."""

    candidate_patches: list[dict] = []
    verification_reports: list[dict] = []


class HistoryListResponse(BaseModel):
    """Response model for history list."""

    sessions: list[DebugSessionResponse]
    total: int


# ──────────────────────────────────────────────────────────────────
# Route Handlers
# ──────────────────────────────────────────────────────────────────


@router.get("/sessions", response_model=HistoryListResponse)
async def list_debug_sessions(
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum sessions to return"),
    project_id: uuid.UUID | None = Query(None, description="Filter by project ID"),
    current_user: dict = Depends(get_current_user_required),
):
    """
    List debug sessions for the authenticated user.

    Args:
        skip: Pagination offset.
        limit: Maximum results per page.
        project_id: Optional project filter.
        current_user: Current authenticated user.

    Returns:
        HistoryListResponse with sessions and total count.
    """
    async with get_db_session() as session:
        try:
            session_repo = DebugSessionRepository(session)

            # Get sessions
            sessions = await session_repo.get_user_debug_sessions(
                user_id=current_user["user_id"],
                skip=skip,
                limit=limit,
                project_id=project_id,
            )

            # Get total count
            total = await session_repo.count_user_debug_sessions(
                user_id=current_user["user_id"],
                project_id=project_id,
            )

            session_responses = [
                DebugSessionResponse(
                    session_id=s.id,
                    project_id=s.project_id,
                    code=s.code[:500] + "..." if len(s.code) > 500 else s.code,
                    error_type=s.error_type,
                    confidence_score=s.confidence_score,
                    pipeline_duration_ms=s.pipeline_duration_ms,
                    created_at=s.created_at.isoformat(),
                    updated_at=s.updated_at.isoformat(),
                )
                for s in sessions
            ]

            return HistoryListResponse(sessions=session_responses, total=total)

        except Exception:
            logger.exception("Failed to list debug sessions")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": "Failed to list sessions",
                },
            )


@router.get("/sessions/{session_id}", response_model=DebugSessionDetailResponse)
async def get_debug_session(
    session_id: uuid.UUID,
    current_user: dict = Depends(get_current_user_required),
):
    """
    Get a specific debug session with full details.

    Args:
        session_id: UUID of the debug session.
        current_user: Current authenticated user.

    Returns:
        DebugSessionDetailResponse with full session data.

    Raises:
        HTTPException: If session not found or access denied.
    """
    async with get_db_session() as session:
        try:
            session_repo = DebugSessionRepository(session)

            # Get session with details
            debug_session = await session_repo.get_session_with_details(session_id)

            if not debug_session:
                logger.warning("Debug session not found: %s", session_id)
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Session not found"},
                )

            # Check ownership
            if debug_session.user_id != current_user["user_id"]:
                logger.warning(
                    "Access denied to session: %s for user: %s",
                    session_id,
                    current_user["user_id"],
                )
                raise HTTPException(
                    status_code=403,
                    detail={"error": "access_denied", "message": "Access denied"},
                )

            # Convert patches and reports to dicts
            patches = [
                {
                    "id": p.id,
                    "patched_code": p.patched_code,
                    "diff": p.diff,
                    "validation_passed": p.validation_passed,
                    "created_at": p.created_at.isoformat(),
                }
                for p in debug_session.candidate_patches
            ]

            reports = [
                {
                    "id": r.id,
                    "verification_status": r.verification_status.value,
                    "execution_passed": r.execution_passed,
                    "test_passed": r.test_passed,
                    "error_message": r.error_message,
                    "created_at": r.created_at.isoformat(),
                }
                for r in debug_session.verification_reports
            ]

            return DebugSessionDetailResponse(
                session_id=debug_session.id,
                project_id=debug_session.project_id,
                code=debug_session.code,
                error_type=debug_session.error_type,
                confidence_score=debug_session.confidence_score,
                pipeline_duration_ms=debug_session.pipeline_duration_ms,
                created_at=debug_session.created_at.isoformat(),
                updated_at=debug_session.updated_at.isoformat(),
                candidate_patches=patches,
                verification_reports=reports,
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to get debug session")
            raise HTTPException(
                status_code=500,
                detail={"error": "internal_error", "message": "Failed to get session"},
            )


@router.get("/sessions/{session_id}/export")
async def export_debug_session(
    session_id: uuid.UUID,
    format: str = Query("json", regex="^(json|txt)$", description="Export format"),
    current_user: dict = Depends(get_current_user_required),
):
    """
    Export a debug session in specified format.

    Args:
        session_id: UUID of the debug session.
        format: Export format (json or txt).
        current_user: Current authenticated user.

    Returns:
        Exported session data.

    Raises:
        HTTPException: If session not found or access denied.
    """
    async with get_db_session() as session:
        try:
            session_repo = DebugSessionRepository(session)

            # Get session with details
            debug_session = await session_repo.get_session_with_details(session_id)

            if not debug_session:
                logger.warning("Debug session not found: %s", session_id)
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Session not found"},
                )

            # Check ownership
            if debug_session.user_id != current_user["user_id"]:
                logger.warning(
                    "Access denied to session: %s for user: %s",
                    session_id,
                    current_user["user_id"],
                )
                raise HTTPException(
                    status_code=403,
                    detail={"error": "access_denied", "message": "Access denied"},
                )

            # Format export
            if format == "json":
                from fastapi.responses import JSONResponse

                export_data = {
                    "session_id": str(debug_session.id),
                    "project_id": (
                        str(debug_session.project_id)
                        if debug_session.project_id
                        else None
                    ),
                    "code": debug_session.code,
                    "error_type": debug_session.error_type,
                    "confidence_score": debug_session.confidence_score,
                    "pipeline_duration_ms": debug_session.pipeline_duration_ms,
                    "created_at": debug_session.created_at.isoformat(),
                    "updated_at": debug_session.updated_at.isoformat(),
                    "candidate_patches": [
                        {
                            "patched_code": p.patched_code,
                            "diff": p.diff,
                            "validation_passed": p.validation_passed,
                        }
                        for p in debug_session.candidate_patches
                    ],
                    "verification_reports": [
                        {
                            "verification_status": r.verification_status.value,
                            "execution_passed": r.execution_passed,
                            "test_passed": r.test_passed,
                            "error_message": r.error_message,
                        }
                        for r in debug_session.verification_reports
                    ],
                }
                return JSONResponse(export_data)
            else:
                from fastapi.responses import PlainTextResponse

                lines = [
                    f"Debug Session: {debug_session.id}",
                    f"Created: {debug_session.created_at.isoformat()}",
                    f"Error Type: {debug_session.error_type or 'None'}",
                    f"Confidence: {debug_session.confidence_score or 0}",
                    "",
                    "=== Original Code ===",
                    debug_session.code,
                    "",
                ]

                if debug_session.candidate_patches:
                    lines.append("=== Candidate Patches ===")
                    for i, patch in enumerate(debug_session.candidate_patches, 1):
                        lines.append(f"\n--- Patch {i} ---")
                        lines.append(f"Valid: {patch.validation_passed}")
                        lines.append(patch.diff or patch.patched_code)

                if debug_session.verification_reports:
                    lines.append("\n=== Verification Reports ===")
                    for i, report in enumerate(debug_session.verification_reports, 1):
                        lines.append(f"\n--- Report {i} ---")
                        lines.append(f"Status: {report.verification_status.value}")
                        lines.append(f"Execution Passed: {report.execution_passed}")
                        lines.append(f"Test Passed: {report.test_passed}")
                        if report.error_message:
                            lines.append(f"Error: {report.error_message}")

                return PlainTextResponse("\n".join(lines))

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to export debug session")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": "Failed to export session",
                },
            )
