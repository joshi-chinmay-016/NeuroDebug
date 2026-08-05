"""
Base repository class providing common CRUD operations.

All repositories should inherit from this base class.
"""

import uuid
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository with common CRUD operations.

    Generic type parameters:
        ModelType: The SQLAlchemy model class
        CreateSchemaType: The Pydantic schema for creation
        UpdateSchemaType: The Pydantic schema for updates
    """

    def __init__(self, model: type[ModelType], session: AsyncSession):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class.
            session: Async database session.
        """
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        """
        Get a single record by ID.

        Args:
            id: UUID of the record.

        Returns:
            Model instance or None if not found.
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[ModelType]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            include_deleted: Whether to include soft-deleted records.

        Returns:
            List of model instances.
        """
        query = select(self.model)

        if not include_deleted and issubclass(self.model, SoftDeleteMixin):
            query = query.where(self.model.deleted_at.is_(None))

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        schema: CreateSchemaType,
        **kwargs: Any,
    ) -> ModelType:
        """
        Create a new record.

        Args:
            schema: Pydantic schema with creation data.
            **kwargs: Additional fields to set.

        Returns:
            Created model instance.
        """
        db_obj = self.model(**schema.model_dump(), **kwargs)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        id: uuid.UUID,
        schema: UpdateSchemaType,
        **kwargs: Any,
    ) -> ModelType | None:
        """
        Update an existing record.

        Args:
            id: UUID of the record to update.
            schema: Pydantic schema with update data.
            **kwargs: Additional fields to update.

        Returns:
            Updated model instance or None if not found.
        """
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        update_data.update(kwargs)

        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
        )
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: uuid.UUID, hard_delete: bool = False) -> bool:
        """
        Delete a record (soft delete by default).

        Args:
            id: UUID of the record to delete.
            hard_delete: If True, perform hard delete instead of soft delete.

        Returns:
            True if deleted, False if not found.
        """
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False

        if hard_delete or not issubclass(self.model, SoftDeleteMixin):
            await self.session.execute(delete(self.model).where(self.model.id == id))
        else:
            db_obj.soft_delete()

        await self.session.flush()
        return True

    async def count(self, include_deleted: bool = False) -> int:
        """
        Count total records.

        Args:
            include_deleted: Whether to include soft-deleted records.

        Returns:
            Total count of records.
        """
        query = select(self.model)

        if not include_deleted and issubclass(self.model, SoftDeleteMixin):
            query = query.where(self.model.deleted_at.is_(None))

        result = await self.session.execute(query)
        return len(result.scalars().all())
