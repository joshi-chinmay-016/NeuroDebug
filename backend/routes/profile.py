"""
API routes for user profile management.

Handles profile updates, password changes, and API key management.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from database import get_db_session
from database.models import User, UserProfile
from middleware.auth import get_current_user_required
from middleware.security import validate_email, validate_password_strength
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from utils.logging import get_logger

logger = get_logger("neurodebug.routes.profile")

router = APIRouter()


# ──────────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────────


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""

    display_name: str | None = Field(None, max_length=100)
    email: EmailStr | None = None


class ChangePasswordRequest(BaseModel):
    """Request model for changing password."""

    current_password: str
    new_password: str = Field(..., min_length=8)


class ProfileResponse(BaseModel):
    """Response model for user profile."""

    id: uuid.UUID
    email: str
    display_name: str | None
    avatar: str | None
    theme: str


class ApiKeyResponse(BaseModel):
    """Response model for API key."""

    id: uuid.UUID
    name: str
    key_prefix: str
    created_at: str


# ──────────────────────────────────────────────────────────────────
# Route Handlers
# ──────────────────────────────────────────────────────────────────


@router.get("", response_model=ProfileResponse)
@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: dict = Depends(get_current_user_required)):
    """
    Get current user profile.

    Args:
        current_user: Current authenticated user.

    Returns:
        ProfileResponse with user profile data.
    """
    async with get_db_session() as session:
        try:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(current_user["user_id"])

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "User not found"},
                )

            return ProfileResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                avatar=None,  # Will be populated from UserProfile
                theme="dark",  # Default theme
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to get profile")
            raise HTTPException(
                status_code=500,
                detail={"error": "internal_error", "message": "Failed to get profile"},
            )


@router.patch("")
@router.patch("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user_required),
):
    """
    Update user profile.

    Args:
        request: Profile update request.
        current_user: Current authenticated user.

    Returns:
        Updated profile data.
    """
    async with get_db_session() as session:
        try:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(current_user["user_id"])

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "User not found"},
                )

            # Validate email if provided
            if request.email and request.email != user.email:
                if not validate_email(request.email):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "invalid_email",
                            "message": "Invalid email format",
                        },
                    )

                # Check if email is already taken
                existing = await user_repo.get_by_email(request.email)
                if existing and existing.id != user.id:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "email_exists",
                            "message": "Email already in use",
                        },
                    )

            # Update user
            if request.display_name is not None:
                user.display_name = request.display_name
            if request.email is not None:
                user.email = request.email

            await session.commit()
            await session.refresh(user)

            return ProfileResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                avatar=None,
                theme="dark",
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to update profile")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": "Failed to update profile",
                },
            )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user_required),
):
    """
    Change user password.

    Args:
        request: Password change request.
        current_user: Current authenticated user.

    Returns:
        Success message.
    """
    async with get_db_session() as session:
        try:
            user_repo = UserRepository(session)
            auth_service = AuthService()
            user = await user_repo.get_by_id(current_user["user_id"])

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "User not found"},
                )

            # Verify current password
            if not auth_service.verify_password(
                request.current_password, user.password_hash
            ):
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "invalid_password",
                        "message": "Current password is incorrect",
                    },
                )

            # Validate new password strength
            is_valid, error_msg = validate_password_strength(request.new_password)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "weak_password", "message": error_msg},
                )

            # Update password
            new_hash = auth_service.hash_password(request.new_password)
            await user_repo.update_password(user.id, new_hash)

            return {"message": "Password changed successfully"}

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to change password")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": "Failed to change password",
                },
            )
