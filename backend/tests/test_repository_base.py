"""
Tests for base repository functionality.
"""

import uuid

import pytest

from database import get_db_session
from repositories.user_repository import UserRepository


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_base_repository_crud():
    """Test basic CRUD operations of base repository."""
    async with get_db_session() as session:
        repo = UserRepository(session)

        # Create
        user = await repo.create_user(
            email="test@example.com", display_name="Test User"
        )
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"

        # Read
        found_user = await repo.get_by_id(user.id)
        assert found_user is not None
        assert found_user.email == "test@example.com"

        # Update
        updated_user = await repo.update(
            user.id, None, display_name="Updated User"  # No schema update
        )
        assert updated_user is not None
        assert updated_user.display_name == "Updated User"

        # Delete (soft)
        deleted = await repo.delete(user.id, hard_delete=False)
        assert deleted is True

        # Verify soft delete
        found_user = await repo.get_by_id(user.id)
        assert found_user is None  # Soft deleted, not returned by default

        # Read with include_deleted
        all_users = await repo.get_all(include_deleted=True)
        assert len(all_users) == 1
        assert all_users[0].is_deleted is True


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_base_repository_get_all():
    """Test get_all with pagination."""
    async with get_db_session() as session:
        repo = UserRepository(session)

        # Create multiple users
        for i in range(5):
            await repo.create_user(
                email=f"user{i}@example.com", display_name=f"User {i}"
            )

        # Get all with pagination
        users = await repo.get_all(skip=0, limit=3)
        assert len(users) == 3

        users = await repo.get_all(skip=3, limit=3)
        assert len(users) == 2


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_base_repository_count():
    """Test count functionality."""
    async with get_db_session() as session:
        repo = UserRepository(session)

        # Create users
        for i in range(3):
            await repo.create_user(
                email=f"user{i}@example.com", display_name=f"User {i}"
            )

        # Count
        count = await repo.count()
        assert count == 3

        # Soft delete one
        users = await repo.get_all()
        await repo.delete(users[0].id)

        # Count without deleted
        count = await repo.count(include_deleted=False)
        assert count == 2

        # Count with deleted
        count = await repo.count(include_deleted=True)
        assert count == 3


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_soft_delete_mixin():
    """Test soft delete mixin functionality."""
    async with get_db_session() as session:
        repo = UserRepository(session)

        user = await repo.create_user(
            email="softdelete@example.com", display_name="Soft Delete Test"
        )

        # Initially not deleted
        assert user.is_deleted is False
        assert user.deleted_at is None

        # Soft delete
        user.soft_delete()
        await session.flush()

        # Verify deleted
        assert user.is_deleted is True
        assert user.deleted_at is not None

        # Restore
        user.restore()
        await session.flush()

        # Verify restored
        assert user.is_deleted is False
        assert user.deleted_at is None


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_timestamp_mixin():
    """Test timestamp mixin functionality."""
    async with get_db_session() as session:
        repo = UserRepository(session)

        user = await repo.create_user(
            email="timestamp@example.com", display_name="Timestamp Test"
        )

        # Verify timestamps are set
        assert user.created_at is not None
        assert user.updated_at is not None

        initial_updated = user.updated_at

        # Update the user
        await repo.update(user.id, None, display_name="Updated Name")

        # Verify updated_at changed
        assert user.updated_at > initial_updated


@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_uuid_primary_key_mixin():
    """Test UUID primary key mixin functionality."""
    async with get_db_session() as session:
        repo = UserRepository(session)

        user = await repo.create_user(
            email="uuid@example.com", display_name="UUID Test"
        )

        # Verify UUID is set
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)

        # Verify it's a valid UUID
        try:
            uuid.UUID(str(user.id))
        except ValueError:
            pytest.fail("ID is not a valid UUID")
