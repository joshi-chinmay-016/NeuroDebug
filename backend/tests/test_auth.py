import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.main import app
from backend.database.models import User
from backend.services.auth_service import AuthService
from backend.middleware.auth import create_access_token, create_refresh_token
import bcrypt


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for authentication tests."""
    password_hash = bcrypt.hashpw(
        "test_password123".encode(), bcrypt.gensalt()
    ).decode()
    user = User(
        email="test@example.com",
        password_hash=password_hash,
        display_name="Test User",
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestAuthService:
    """Test authentication service methods."""

    @pytest.mark.asyncio
    async def test_hash_password(self):
        """Test password hashing."""
        password = "secure_password123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert bcrypt.checkpw(password.encode(), hashed.encode())

    @pytest.mark.asyncio
    async def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "secure_password123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    @pytest.mark.asyncio
    async def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "secure_password123"
        wrong_password = "wrong_password"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_password, hashed) is False

    @pytest.mark.asyncio
    async def test_create_access_token(self):
        """Test access token creation."""
        user_id = "test-user-id"
        token = create_access_token(data={"sub": user_id})

        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "test-user-id"
        token = create_refresh_token(data={"sub": user_id})

        assert isinstance(token, str)
        assert len(token) > 0


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "display_name": "New User",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 400

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weak",
                "display_name": "New User",
            },
        )

        assert response.status_code == 400

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "test_password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_email(self, client: TestClient):
        """Test login with invalid email."""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "test_password123"},
        )

        assert response.status_code == 401

    def test_login_invalid_password(self, client: TestClient, test_user):
        """Test login with invalid password."""
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrong_password"},
        )

        assert response.status_code == 401

    def test_refresh_token_success(self, client: TestClient, test_user):
        """Test successful token refresh."""
        # First login to get refresh token
        login_response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "test_password123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post("/auth/refresh", json={"refresh_token": "invalid_token"})

        assert response.status_code == 401

    def test_logout_success(self, client: TestClient, test_user):
        """Test successful logout."""
        login_response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "test_password123"},
        )
        access_token = login_response.json()["access_token"]

        response = client.post(
            "/auth/logout", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200

    def test_protected_route_without_token(self, client: TestClient):
        """Test accessing protected route without token."""
        response = client.get("/workspace/projects")

        assert response.status_code == 401

    def test_protected_route_with_token(self, client: TestClient, test_user):
        """Test accessing protected route with valid token."""
        login_response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "test_password123"},
        )
        access_token = login_response.json()["access_token"]

        response = client.get(
            "/workspace/projects", headers={"Authorization": f"Bearer {access_token}"}
        )

        # Should not be 401 (might be 200 or other status based on actual implementation)
        assert response.status_code != 401
