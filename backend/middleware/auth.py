"""
Authentication middleware for protected routes.

Provides dependency injection for FastAPI routes to require authentication.
"""

import uuid

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services.auth_service import AuthService, AuthenticationError
from utils.logging import get_logger

logger = get_logger("neurodebug.middleware.auth")

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """
    Get current user from access token if present (optional authentication).

    Args:
        request: FastAPI request object.
        credentials: Optional HTTP authorization credentials.

    Returns:
        User payload dict if token valid, None otherwise.
    """
    token = None
    if isinstance(credentials, HTTPAuthorizationCredentials):
        token = credentials.credentials
    elif isinstance(credentials, str):
        token = credentials
    else:
        # Fallback to direct inspection of the request Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None

    try:
        payload = AuthService.verify_access_token(token)
        return {
            "user_id": uuid.UUID(payload["sub"]),
            "email": payload["email"],
            "tier": payload["tier"],
        }
    except AuthenticationError as exc:
        logger.warning("Optional auth failed: %s", exc.message)
        return None


async def get_current_user_required(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Get current user from access token (required authentication).

    Args:
        request: FastAPI request object.
        credentials: HTTP authorization credentials.

    Returns:
        User payload dict with user_id, email, tier.

    Raises:
        HTTPException: If token is missing or invalid.
    """
    token = None
    if isinstance(credentials, HTTPAuthorizationCredentials):
        token = credentials.credentials
    elif isinstance(credentials, str):
        token = credentials
    else:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        logger.warning("Missing authorization header")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "missing_token",
                "message": "Authorization header required",
            },
        )

    try:
        payload = AuthService.verify_access_token(token)
        return {
            "user_id": uuid.UUID(payload["sub"]),
            "email": payload["email"],
            "tier": payload["tier"],
        }
    except AuthenticationError as exc:
        logger.warning("Authentication failed: %s", exc.message)
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "message": exc.message},
        )


async def require_tier(minimum_tier: str = "free"):
    """
    Dependency factory to require minimum subscription tier.

    Args:
        minimum_tier: Minimum required tier (guest, free, pro, enterprise).

    Returns:
        Dependency function that checks user tier.
    """

    async def check_tier(
        current_user: dict = Depends(get_current_user_required),
    ) -> dict:
        """Check if user meets minimum tier requirement."""
        tier_hierarchy = {"guest": 0, "free": 1, "pro": 2, "enterprise": 3}

        user_tier = current_user.get("tier", "guest")
        user_level = tier_hierarchy.get(user_tier, 0)
        required_level = tier_hierarchy.get(minimum_tier, 1)

        if user_level < required_level:
            logger.warning(
                "Tier requirement failed: user_tier=%s required=%s",
                user_tier,
                minimum_tier,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_tier",
                    "message": f"This feature requires {minimum_tier} tier or higher",
                    "current_tier": user_tier,
                    "required_tier": minimum_tier,
                },
            )

        return current_user

    return check_tier
