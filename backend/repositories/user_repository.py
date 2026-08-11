"""
Repository for user management operations.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User, Any, Any]):
    """Repository for user operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize user repository.

        Args:
            session: Async database session.
        """
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email address.

        Args:
            email: User email address.

        Returns:
            User instance or None.
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password_hash: str | None = None,
        display_name: str | None = None,
        subscription_plan_id: uuid.UUID | None = None,
    ) -> User:
        """
        Create a new user.

        Args:
            email: User email address.
            password_hash: Optional hashed password.
            display_name: Optional display name.
            subscription_plan_id: Optional subscription plan ID.

        Returns:
            Created User instance.
        """
        user = User(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            subscription_plan_id=subscription_plan_id,
            email_verified=False,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_password(
        self, user_id: uuid.UUID, password_hash: str
    ) -> User | None:
        """
        Update user's password.

        Args:
            user_id: UUID of the user.
            password_hash: New hashed password.

        Returns:
            Updated User instance or None.
        """
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.password_hash = password_hash
            await self.session.flush()
            await self.session.refresh(user)
        return user

    async def update_last_login(self, user_id: uuid.UUID) -> User | None:
        """
        Update user's last login timestamp.

        Args:
            user_id: UUID of the user.

        Returns:
            Updated User instance or None.
        """
        from datetime import datetime, timezone

        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(user)
        return user
