"""
Authentication service for JWT token management and password hashing.

Provides secure token generation, validation, and password operations.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
import bcrypt

from models.errors import NeuroDebugError
from utils.config import Config
from utils.logging import get_logger

logger = get_logger("neurodebug.auth_service")


class AuthenticationError(NeuroDebugError):
    """Authentication-specific errors."""

    def __init__(self, message: str, error_type: str = "auth_error"):
        super().__init__(message, error_type)


class AuthService:
    """Service for authentication operations."""

    # Token configuration
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days
    ALGORITHM = "HS256"

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using native bcrypt.

        Args:
            password: Plain text password.

        Returns:
            Hashed password string.
        """
        pwd_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password.
            hashed_password: Hashed password string.

        Returns:
            True if password matches, False otherwise.
        """
        try:
            pwd_bytes = plain_password.encode("utf-8")[:72]
            hash_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(pwd_bytes, hash_bytes)
        except Exception:
            return False

    @staticmethod
    def create_access_token(user_id: uuid.UUID, email: str, tier: str = "guest") -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User UUID.
            email: User email.
            tier: User subscription tier.

        Returns:
            Encoded JWT access token.
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user_id),
            "email": email,
            "tier": tier,
            "type": "access",
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
        }

        token = jwt.encode(payload, Config.JWT_SECRET, algorithm=AuthService.ALGORITHM)
        logger.info("Access token created for user: %s", email)
        return token

    @staticmethod
    def create_refresh_token(user_id: uuid.UUID) -> str:
        """
        Create a JWT refresh token.

        Args:
            user_id: User UUID.

        Returns:
            Encoded JWT refresh token.
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
        }

        token = jwt.encode(payload, Config.JWT_SECRET, algorithm=AuthService.ALGORITHM)
        logger.info("Refresh token created for user: %s", user_id)
        return token

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string.

        Returns:
            Decoded token payload.

        Raises:
            AuthenticationError: If token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                token, Config.JWT_SECRET, algorithms=[AuthService.ALGORITHM]
            )
            return payload
        except JWTError as exc:
            logger.warning("Token validation failed: %s", exc)
            raise AuthenticationError("Invalid or expired token", "invalid_token")

    @staticmethod
    def verify_access_token(token: str) -> dict[str, Any]:
        """
        Verify an access token and return its payload.

        Args:
            token: JWT access token.

        Returns:
            Token payload with user information.

        Raises:
            AuthenticationError: If token is invalid, expired, or not an access token.
        """
        payload = AuthService.decode_token(token)

        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type", "invalid_token_type")

        return payload

    @staticmethod
    def verify_refresh_token(token: str) -> uuid.UUID:
        """
        Verify a refresh token and return the user ID.

        Args:
            token: JWT refresh token.

        Returns:
            User UUID.

        Raises:
            AuthenticationError: If token is invalid, expired, or not a refresh token.
        """
        payload = AuthService.decode_token(token)

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type", "invalid_token_type")

        return uuid.UUID(payload["sub"])

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Validate password strength.

        Args:
            password: Password to validate.

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
