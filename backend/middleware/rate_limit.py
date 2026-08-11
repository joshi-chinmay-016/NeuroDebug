"""
Rate limiting middleware for API endpoints.

Provides in-memory rate limiting with configurable limits per endpoint and tier.
"""

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.middleware.rate_limit")


class RateLimiter:
    """In-memory rate limiter using sliding window."""

    def __init__(self):
        """Initialize rate limiter with empty storage."""
        self.requests: defaultdict[str, list[float]] = defaultdict(list)

    def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """
        Check if request is allowed within rate limit.

        Args:
            key: Unique identifier for rate limiting (e.g., IP or user ID).
            limit: Maximum requests allowed in window.
            window_seconds: Time window in seconds.

        Returns:
            Tuple of (allowed, remaining, reset_time).
        """
        now = time.time()
        window_start = now - window_seconds

        # Clean old requests
        self.requests[key] = [
            timestamp for timestamp in self.requests[key] if timestamp > window_start
        ]

        # Check limit
        current_count = len(self.requests[key])
        remaining = max(0, limit - current_count)
        reset_time = int(now + window_seconds)

        if current_count >= limit:
            logger.warning(
                "Rate limit exceeded: key=%s count=%d limit=%d",
                key,
                current_count,
                limit,
            )
            return False, 0, reset_time

        # Add current request
        self.requests[key].append(now)
        return True, remaining - 1, reset_time


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit configurations
RATE_LIMITS = {
    "auth": {"limit": 10, "window": 60},  # 10 requests per minute for auth
    "default": {"limit": 60, "window": 60},  # 60 requests per minute default
    "debug": {"limit": 20, "window": 60},  # 20 requests per minute for debug
}


async def rate_limit_middleware(
    request: Request,
    call_next: Callable,
    limit: int = 60,
    window: int = 60,
    key_func: Callable[[Request], str] | None = None,
) -> Response:
    """
    Rate limiting middleware for FastAPI.

    Args:
        request: FastAPI request object.
        call_next: Next middleware/route handler.
        limit: Maximum requests per window.
        window: Time window in seconds.
        key_func: Optional function to extract rate limit key from request.

    Returns:
        Response object or HTTPException if rate limited.

    Raises:
        HTTPException: If rate limit exceeded.
    """
    # Get rate limit key
    if key_func:
        key = key_func(request)
    else:
        # Default to client IP
        key = request.client.host if request.client else "unknown"

    # Check rate limit
    allowed, remaining, reset_time = rate_limiter.is_allowed(key, limit, window)

    if not allowed:
        logger.warning("Rate limit exceeded for key: %s", key)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many requests",
                "limit": limit,
                "window": window,
                "reset_time": reset_time,
            },
        )

    # Add rate limit headers to response
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_time)

    return response


def get_rate_limit_by_path(path: str) -> tuple[int, int]:
    """
    Get rate limit configuration for a given path.

    Args:
        path: Request path.

    Returns:
        Tuple of (limit, window_seconds).
    """
    if "/auth" in path:
        config = RATE_LIMITS["auth"]
    elif "/debug" in path:
        config = RATE_LIMITS["debug"]
    else:
        config = RATE_LIMITS["default"]

    return config["limit"], config["window"]


def rate_limit_by_ip(limit: int = 60, window: int = 60):
    """
    Dependency factory for IP-based rate limiting.

    Args:
        limit: Maximum requests per window.
        window: Time window in seconds.

    Returns:
        Dependency function that applies rate limiting.
    """

    async def check_rate_limit(request: Request) -> None:
        """Check IP-based rate limit."""
        key = request.client.host if request.client else "unknown"
        allowed, remaining, reset_time = rate_limiter.is_allowed(key, limit, window)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests",
                    "limit": limit,
                    "window": window,
                    "reset_time": reset_time,
                },
            )

    return check_rate_limit


def rate_limit_by_user(limit: int = 60, window: int = 60):
    """
    Dependency factory for user-based rate limiting.

    Args:
        limit: Maximum requests per window.
        window: Time window in seconds.

    Returns:
        Dependency function that applies rate limiting.
    """
    from middleware.auth import get_current_user_optional

    async def check_rate_limit(
        request: Request,
        current_user: dict | None = Depends(get_current_user_optional),
    ) -> None:
        """Check user-based rate limit."""
        if current_user:
            key = str(current_user["user_id"])
        else:
            key = request.client.host if request.client else "unknown"

        allowed, remaining, reset_time = rate_limiter.is_allowed(key, limit, window)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests",
                    "limit": limit,
                    "window": window,
                    "reset_time": reset_time,
                },
            )

    return check_rate_limit
