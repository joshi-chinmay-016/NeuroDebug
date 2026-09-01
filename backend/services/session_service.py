"""
Session management service for anonymous and authenticated users.

Handles temporary session IDs for guests and user sessions for authenticated users.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import SubscriptionTier
from repositories.user_repository import UserRepository
from services.usage_limit_service import UsageLimitService
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.session_service")


class SessionService:
    """
    Service for managing user sessions.

    Supports both anonymous guest sessions and authenticated user sessions.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository | None = None,
        usage_limit_service: UsageLimitService | None = None,
    ):
        """
        Initialize session service.

        Args:
            session: Async database session.
            user_repo: Optional user repository.
            usage_limit_service: Optional usage limit service.
        """
        self.session = session
        self.user_repo = user_repo or UserRepository(session)
        self.usage_limit_service = usage_limit_service or UsageLimitService(session)

    def generate_session_id(self) -> str:
        """
        Generate a secure random session ID.

        Returns:
            Secure random session ID string.
        """
        return secrets.token_urlsafe(32)

    def get_session_id_from_request(self, request: Request) -> str | None:
        """
        Extract session ID from request cookies or headers.

        Args:
            request: FastAPI request object.

        Returns:
            Session ID string or None.
        """
        # Try cookie first
        session_id = request.cookies.get(Config.SESSION_COOKIE_NAME)
        if session_id:
            return session_id

        # Try header as fallback
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            return session_id

        return None

    def set_session_cookie(
        self,
        response: Response,
        session_id: str,
        max_age_hours: int | None = None,
    ) -> None:
        """
        Set session cookie in response.

        Args:
            response: FastAPI response object.
            session_id: Session ID string.
            max_age_hours: Optional cookie expiry in hours.
        """
        max_age = (max_age_hours or Config.SESSION_EXPIRY_HOURS) * 3600
        expiry = datetime.now(timezone.utc) + timedelta(
            hours=max_age_hours or Config.SESSION_EXPIRY_HOURS
        )

        response.set_cookie(
            key=Config.SESSION_COOKIE_NAME,
            value=session_id,
            max_age=max_age,
            expires=expiry,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
        )

        logger.debug(
            "Session cookie set: session_id=%s max_age=%d", session_id, max_age
        )

    def clear_session_cookie(self, response: Response) -> None:
        """
        Clear session cookie from response.

        Args:
            response: FastAPI response object.
        """
        response.delete_cookie(
            key=Config.SESSION_COOKIE_NAME,
            httponly=True,
            secure=False,
            samesite="lax",
        )
        logger.debug("Session cookie cleared")

    async def get_or_create_session(
        self,
        request: Request,
        response: Response,
        user_id: uuid.UUID | None = None,
    ) -> tuple[str, str]:
        """
        Get existing session or create new one.

        Args:
            request: FastAPI request object.
            response: FastAPI response object.
            user_id: Optional user UUID for authenticated users.

        Returns:
            Tuple of (session_id, subscription_tier).
        """
        session_id = self.get_session_id_from_request(request)

        if user_id:
            # Authenticated user - determine tier from user
            tier = SubscriptionTier.FREE.value
            try:
                user = await self.user_repo.get_by_id(user_id)
                if user and user.subscription_plan:
                    tier = user.subscription_plan.tier
            except Exception:
                tier = SubscriptionTier.FREE.value
        else:
            # Guest user
            tier = SubscriptionTier.GUEST.value

        if not session_id:
            session_id = self.generate_session_id()
            self.set_session_cookie(response, session_id)
            logger.info("New session created: session_id=%s tier=%s", session_id, tier)
        else:
            logger.debug(
                "Existing session retrieved: session_id=%s tier=%s", session_id, tier
            )

        return session_id, tier

    async def validate_session(self, session_id: str) -> tuple[bool, str]:
        """
        Validate a session ID.

        Args:
            session_id: Session ID string.

        Returns:
            Tuple of (is_valid, subscription_tier).
        """
        if not session_id or len(session_id) < 16:
            return False, SubscriptionTier.GUEST.value

        # In a production system, you might check against a sessions table
        # For now, we assume any properly formatted session ID is valid
        return True, SubscriptionTier.GUEST.value

    async def upgrade_session(
        self,
        session_id: str,
        user_id: uuid.UUID,
        response: Response,
    ) -> tuple[str, str]:
        """
        Upgrade a guest session to an authenticated user session.

        Args:
            session_id: Current session ID.
            user_id: User UUID.
            response: FastAPI response object.

        Returns:
            Tuple of (new_session_id, subscription_tier).
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Generate new session ID for the authenticated user
        new_session_id = self.generate_session_id()
        self.set_session_cookie(response, new_session_id)

        # Update user's last login
        await self.user_repo.update_last_login(user_id)

        tier = SubscriptionTier.FREE.value
        try:
            if user.subscription_plan:
                tier = user.subscription_plan.tier
        except Exception:
            tier = SubscriptionTier.FREE.value

        logger.info(
            "Session upgraded: old_session=%s new_session=%s user_id=%s tier=%s",
            session_id,
            new_session_id,
            user_id,
            tier,
        )

        return new_session_id, tier

    async def check_rate_limit(
        self,
        session_id: str,
        tier: str,
        user_id: uuid.UUID | None = None,
    ) -> tuple[bool, int, int]:
        """
        Check if session is within rate limits.

        Args:
            session_id: Session ID string.
            tier: Subscription tier.
            user_id: Optional user UUID.

        Returns:
            Tuple of (allowed, current_usage, limit).
        """
        return await self.usage_limit_service.check_usage_limit(
            session_id=session_id, tier=tier, user_id=user_id
        )

    async def get_usage_info(
        self,
        session_id: str,
        tier: str,
        user_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Get usage information for a session.

        Args:
            session_id: Session ID string.
            tier: Subscription tier.
            user_id: Optional user UUID.

        Returns:
            Dictionary with usage information.
        """
        remaining = await self.usage_limit_service.get_remaining_requests(
            session_id=session_id, tier=tier, user_id=user_id
        )
        limit = await self.usage_limit_service.get_daily_limit(tier)

        return {
            "remaining_requests": remaining,
            "daily_limit": limit,
            "tier": tier,
            "session_id": session_id,
        }
