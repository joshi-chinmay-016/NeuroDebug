import uuid
import pytest
import pytest_asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from database.models import User
from services.auth_service import AuthService


@pytest_asyncio.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestAuthService:
    """Test authentication service methods."""

    def test_hash_and_verify_password(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert AuthService.verify_password(password, hashed) is True
        assert AuthService.verify_password("WrongPassword!", hashed) is False

    def test_password_strength_validation(self):
        """Test password complexity checks."""
        valid, msg = AuthService.validate_password_strength("Short1!")
        assert valid is False

        valid, msg = AuthService.validate_password_strength("alllowercase123!")
        assert valid is False

        valid, msg = AuthService.validate_password_strength("ALLUPPERCASE123!")
        assert valid is False

        valid, msg = AuthService.validate_password_strength("ValidPassword123!")
        assert valid is True

    def test_create_and_verify_access_token(self):
        """Test access token creation and verification."""
        user_id = uuid.uuid4()
        token = AuthService.create_access_token(user_id, "test@example.com", tier="free")

        assert isinstance(token, str)
        assert len(token) > 0

        payload = AuthService.verify_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["email"] == "test@example.com"
        assert payload["tier"] == "free"
        assert payload["type"] == "access"

    def test_create_and_verify_refresh_token(self):
        """Test refresh token creation and verification."""
        user_id = uuid.uuid4()
        token = AuthService.create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        verified_user_id = AuthService.verify_refresh_token(token)
        assert verified_user_id == user_id


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_and_login_flow(
        self, async_client: httpx.AsyncClient, db_session: AsyncSession
    ):
        """Test complete registration and login flow using isolated db session."""
        from contextlib import asynccontextmanager
        from unittest.mock import patch

        @asynccontextmanager
        async def mock_get_db():
            yield db_session

        with (
            patch("routes.auth.get_db_session", mock_get_db),
            patch("routes.workspace.get_db_session", mock_get_db),
        ):
            unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
            password = "SecurePassword123!"

            # Register
            reg_response = await async_client.post(
                "/auth/register",
                json={
                    "email": unique_email,
                    "password": password,
                    "display_name": "Test Engineer",
                },
            )

            assert reg_response.status_code == 201
            data = reg_response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["email"] == unique_email
            assert data["tier"] == "free"

            # Login
            login_response = await async_client.post(
                "/auth/login",
                json={"email": unique_email, "password": password},
            )

            assert login_response.status_code == 200
            login_data = login_response.json()
            assert "access_token" in login_data
            assert login_data["email"] == unique_email

            # Access Protected Route with Token
            access_token = login_data["access_token"]
            projects_response = await async_client.get(
                "/workspace/projects",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert projects_response.status_code == 200

            # Protected route without token
            unauth_response = await async_client.get("/workspace/projects")
            assert unauth_response.status_code == 401
