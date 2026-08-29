"""
API routes for authentication endpoints.

Handles user registration, login, logout, and token refresh.
"""

import uuid

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field

from database import get_db_session
from database.models import SubscriptionTier
from repositories.subscription_repository import SubscriptionRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService, AuthenticationError
from utils.logging import get_logger

logger = get_logger("neurodebug.routes.auth")

router = APIRouter()


# ──────────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """Request model for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    display_name: str | None = Field(None, description="Optional display name")


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


class AuthResponse(BaseModel):
    """Response model for authentication operations."""

    access_token: str
    refresh_token: str
    user_id: uuid.UUID
    email: str
    display_name: str | None
    tier: str


class UserResponse(BaseModel):
    """Response model for user information."""

    user_id: uuid.UUID
    email: str
    display_name: str | None
    email_verified: bool
    tier: str


# ──────────────────────────────────────────────────────────────────
# Route Handlers
# ──────────────────────────────────────────────────────────────────


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    request: Request, response: Response, register_request: RegisterRequest
):
    """
    Register a new user account.

    Creates a user with email and password, assigns free tier,
    and returns authentication tokens.

    Args:
        request: FastAPI request object.
        response: FastAPI response object.
        register_request: Registration request with email and password.

    Returns:
        AuthResponse with access token, refresh token, and user info.

    Raises:
        HTTPException: If registration fails (email already exists, weak password).
    """
    async with get_db_session() as session:
        try:
            user_repo = UserRepository(session)
            subscription_repo = SubscriptionRepository(session)

            # Check if user already exists
            existing_user = await user_repo.get_by_email(register_request.email)
            if existing_user:
                logger.warning(
                    "Registration attempt with existing email: %s",
                    register_request.email,
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "email_exists",
                        "message": "Email already registered",
                    },
                )

            # Validate password strength
            is_valid, error_msg = AuthService.validate_password_strength(
                register_request.password
            )
            if not is_valid:
                logger.warning(
                    "Weak password attempt for email: %s", register_request.email
                )
                raise HTTPException(
                    status_code=400,
                    detail={"error": "weak_password", "message": error_msg},
                )

            # Get free subscription plan if seeded
            free_plan = await subscription_repo.get_by_tier(SubscriptionTier.FREE.value)
            subscription_plan_id = free_plan.id if free_plan else None

            # Hash password
            password_hash = AuthService.hash_password(register_request.password)

            # Create user
            user = await user_repo.create_user(
                email=register_request.email,
                password_hash=password_hash,
                display_name=register_request.display_name,
                subscription_plan_id=subscription_plan_id,
            )

            # Generate tokens
            access_token = AuthService.create_access_token(
                user_id=user.id,
                email=user.email,
                tier=SubscriptionTier.FREE.value,
            )
            refresh_token = AuthService.create_refresh_token(user_id=user.id)

            # Set refresh token in HTTP-only cookie
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,  # 30 days
            )

            logger.info("User registered successfully: %s", user.email)

            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                tier=SubscriptionTier.FREE.value,
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Unexpected error during registration")
            raise HTTPException(
                status_code=500,
                detail={"error": "internal_error", "message": "Registration failed"},
            )


@router.post("/login", response_model=AuthResponse)
async def login(request: Request, response: Response, login_request: LoginRequest):
    """
    Authenticate a user and return tokens.

    Validates email and password, generates JWT токены,
    and sets refresh token in HTTP-only cookie.

    Args:
        request: FastAPI request object.
        response: FastAPI response object.
        login_request: Login request with email and password.

    Returns:
        AuthResponse with access token, refresh token, and user info.

    Raises:
        HTTPException: If authentication fails (invalid credentials).
    """
    async with get_db_session() as session:
        try:
            user_repo = UserRepository(session)

            # Get user by email
            user = await user_repo.get_by_email(login_request.email)
            if not user:
                logger.warning(
                    "Login attempt with non-existent email: %s", login_request.email
                )
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "invalid_credentials",
                        "message": "Invalid email or password",
                    },
                )

            # Verify password
            if not user.password_hash:
                logger.warning(
                    "Login attempt for user without password: %s", login_request.email
                )
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "invalid_credentials",
                        "message": "Invalid email or password",
                    },
                )

            if not AuthService.verify_password(
                login_request.password, user.password_hash
            ):
                logger.warning(
                    "Login attempt with invalid password: %s", login_request.email
                )
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "invalid_credentials",
                        "message": "Invalid email or password",
                    },
                )

            # Determine user tier
            tier = SubscriptionTier.GUEST.value
            if user.subscription_plan:
                tier = user.subscription_plan.tier

            # Update last login
            await user_repo.update_last_login(user.id)

            # Generate tokens
            access_token = AuthService.create_access_token(
                user_id=user.id,
                email=user.email,
                tier=tier,
            )
            refresh_token = AuthService.create_refresh_token(user_id=user.id)

            # Set refresh token in HTTP-only cookie
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,  # 30 days
            )

            logger.info("User logged in successfully: %s", user.email)

            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                tier=tier,
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Unexpected error during login")
            raise HTTPException(
                status_code=500,
                detail={"error": "internal_error", "message": "Login failed"},
            )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout a user by clearing the refresh token cookie.

    Args:
        response: FastAPI response object.

    Returns:
        Success message.
    """
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax",
    )

    logger.info("User logged out")
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_request: RefreshTokenRequest | None = None,
):
    """
    Refresh an access token using a refresh token.

    Accepts refresh token from request body or HTTP-only cookie.

    Args:
        request: FastAPI request object.
        response: FastAPI response object.
        refresh_request: Optional refresh token in request body.

    Returns:
        AuthResponse with new access token and refresh token.

    Raises:
        HTTPException: If refresh token is invalid or expired.
    """
    # Get refresh token from body or cookie
    token = None
    if refresh_request:
        token = refresh_request.refresh_token
    else:
        token = request.cookies.get("refresh_token")

    if not token:
        logger.warning("Refresh token not provided")
        raise HTTPException(
            status_code=401,
            detail={"error": "missing_token", "message": "Refresh token required"},
        )

    try:
        # Verify refresh token and get user ID
        user_id = AuthService.verify_refresh_token(token)

        async with get_db_session() as session:
            user_repo = UserRepository(session)

            # Get user
            user = await user_repo.get_by_id(user_id)
            if not user:
                logger.warning("Refresh token for non-existent user: %s", user_id)
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "invalid_token",
                        "message": "Invalid refresh token",
                    },
                )

            # Determine user tier
            tier = SubscriptionTier.GUEST.value
            if user.subscription_plan:
                tier = user.subscription_plan.tier

            # Generate new tokens
            access_token = AuthService.create_access_token(
                user_id=user.id,
                email=user.email,
                tier=tier,
            )
            new_refresh_token = AuthService.create_refresh_token(user_id=user.id)

            # Update refresh token in cookie
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,  # 30 days
            )

            logger.info("Token refreshed for user: %s", user.email)

            return AuthResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                tier=tier,
            )

    except AuthenticationError as exc:
        logger.warning("Token refresh failed: %s", exc.message)
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "message": exc.message},
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during token refresh")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "Token refresh failed"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request):
    """
    Get current user information from access token.

    Args:
        request: FastAPI request object.

    Returns:
        UserResponse with user information.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    # Get authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing or invalid authorization header")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "missing_token",
                "message": "Authorization header required",
            },
        )

    token = auth_header[7:]  # Remove "Bearer " prefix

    try:
        # Verify access token
        payload = AuthService.verify_access_token(token)
        user_id = uuid.UUID(payload["sub"])

        async with get_db_session() as session:
            user_repo = UserRepository(session)

            # Get user
            user = await user_repo.get_by_id(user_id)
            if not user:
                logger.warning("Token for non-existent user: %s", user_id)
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "invalid_token",
                        "message": "Invalid access token",
                    },
                )

            # Determine user tier
            tier = SubscriptionTier.GUEST.value
            if user.subscription_plan:
                tier = user.subscription_plan.tier

            return UserResponse(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                email_verified=user.email_verified,
                tier=tier,
            )

    except AuthenticationError as exc:
        logger.warning("Token verification failed: %s", exc.message)
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "message": exc.message},
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error getting current user")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "Failed to get user info"},
        )
