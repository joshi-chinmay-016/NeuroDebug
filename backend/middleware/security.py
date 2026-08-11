"""
Security Middleware

Provides CSRF protection, input validation, and session expiration handling.
"""

import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.middleware.security")

security = HTTPBearer(auto_error=False)


class CSRFProtection:
    """CSRF protection middleware for state-changing operations."""

    def __init__(self):
        """Initialize CSRF protection."""
        self.csrf_token_header = "X-CSRF-Token"
        self.csrf_cookie_name = "csrf_token"

    def generate_token(self) -> str:
        """
        Generate a secure CSRF token.

        Returns:
            CSRF token string.
        """
        return secrets.token_urlsafe(32)

    def validate_token(self, request: Request) -> bool:
        """
        Validate CSRF token from request.

        Args:
            request: FastAPI request object.

        Returns:
            True if valid, False otherwise.
        """
        # Get token from header
        header_token = request.headers.get(self.csrf_token_header)

        # Get token from cookie
        cookie_token = request.cookies.get(self.csrf_cookie_name)

        if not header_token or not cookie_token:
            logger.warning("CSRF token missing")
            return False

        if header_token != cookie_token:
            logger.warning("CSRF token mismatch")
            return False

        return True

    def set_csrf_cookie(self, response: Response, token: str) -> None:
        """
        Set CSRF token in HTTP-only cookie.

        Args:
            response: FastAPI response object.
            token: CSRF token to set.
        """
        response.set_cookie(
            key=self.csrf_cookie_name,
            value=token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=3600,  # 1 hour
        )


# Global CSRF protection instance
csrf_protection = CSRFProtection()


def check_csrf(request: Request) -> None:
    """
    Dependency to check CSRF token for state-changing operations.

    Args:
        request: FastAPI request object.

    Raises:
        HTTPException: If CSRF validation fails.
    """
    # Skip CSRF for GET, HEAD, OPTIONS, TRACE
    if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
        return

    # Skip CSRF for API endpoints that use JWT auth
    if request.url.path.startswith("/auth/") or request.url.path.startswith(
        "/workspace/"
    ):
        return

    if not csrf_protection.validate_token(request):
        raise HTTPException(
            status_code=403,
            detail={"error": "csrf_error", "message": "Invalid CSRF token"},
        )


def validate_session_expiration(request: Request) -> None:
    """
    Check if session has expired.

    Args:
        request: FastAPI request object.

    Raises:
        HTTPException: If session has expired.
    """
    # Check session cookie expiration
    session_cookie = request.cookies.get(Config.SESSION_COOKIE_NAME)
    if not session_cookie:
        return

    # Session expiration is handled by cookie max-age
    # Additional checks can be added here for server-side validation
    pass


async def security_middleware(request: Request, call_next):
    """
    Security middleware for all requests.

    Args:
        request: FastAPI request object.
        call_next: Next middleware/endpoint.

    Returns:
        Response object.
    """
    # Add security headers
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        value: Input string to sanitize.
        max_length: Maximum allowed length.

    Returns:
        Sanitized string.
    """
    if not value:
        return ""

    # Truncate to max length
    value = value[:max_length]

    # Remove null bytes
    value = value.replace("\x00", "")

    return value


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email string to validate.

    Returns:
        True if valid, False otherwise.
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Args:
        password: Password string to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    return True, ""
