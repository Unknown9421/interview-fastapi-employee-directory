"""
Base Repository with Generic CRUD operations.
Provides reusable data access methods for all entities.
"""
from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update as sql_update, delete as sql_delete
from sqlalchemy.sql import Select

from app.models.base import BaseModel, SoftDeletableModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Generic Repository providing CRUD operations for any SQLAlchemy model.

    All specific repositories should inherit from this class to reuse common operations.

    Example:
        class EmployeeRepository(BaseRepository[Employee]):
            def __init__(self, db: AsyncSession):
                super().__init__(Employee, db)
    """

    def __init__(self, model: Type[T], db: AsyncSession):
        """
        Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> Optional[T]:
        """
        Get single record by ID.

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None
    ) -> List[T]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            order_by: Column to order by (default: id)

        Returns:
            List of model instances
        """
        query = select(self.model)

        if order_by is not None:
            query = query.order_by(order_by)
        else:
            query = query.order_by(self.model.id)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """
        Create new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            Created model instance with ID assigned
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: int, **kwargs) -> Optional[T]:
        """
        Update existing record.

        Args:
            id: Primary key of record to update
            **kwargs: Fields to update with new values

        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.db.flush()
            await self.db.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """
        Hard delete record from database.

        Args:
            id: Primary key of record to delete

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id)
        if instance:
            await self.db.delete(instance)
            await self.db.flush()
            return True
        return False

    async def soft_delete(self, id: int, deleted_by: Optional[str] = None) -> bool:
        """
        Soft delete record (only for models with SoftDeleteMixin).

        Args:
            id: Primary key of record to soft delete
            deleted_by: User/system that performed the deletion

        Returns:
            True if soft deleted, False if not found
        """
        # Check if model supports soft delete
        if not issubclass(self.model, SoftDeletableModel):
            raise ValueError(
                f"Model {self.model.__name__} does not support soft delete. "
                "Use hard delete() method instead."
            )

        instance = await self.get_by_id(id)
        if instance:
            instance.is_deleted = True
            if deleted_by:
                instance.deleted_by = deleted_by
            await self.db.flush()
            await self.db.refresh(instance)
            return True
        return False

    async def count(self, where_clause: Optional[Any] = None) -> int:
        """
        Count total records.

        Args:
            where_clause: Optional WHERE condition to filter count

        Returns:
            Total number of records
        """
        query = select(func.count(self.model.id))
        if where_clause is not None:
            query = query.where(where_clause)

        result = await self.db.execute(query)
        return result.scalar()

    async def exists(self, id: int) -> bool:
        """
        Check if record exists by ID.

        Args:
            id: Primary key value

        Returns:
            True if exists, False otherwise
        """
        result = await self.db.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return result.scalar() > 0

    async def find(self, where_clause: Any, limit: Optional[int] = None) -> List[T]:
        """
        Find records matching WHERE condition.

        Args:
            where_clause: SQLAlchemy WHERE clause
            limit: Optional limit on number of results

        Returns:
            List of matching model instances
        """
        query = select(self.model).where(where_clause)
        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_one(self, where_clause: Any) -> Optional[T]:
        """
        Find single record matching WHERE condition.

        Args:
            where_clause: SQLAlchemy WHERE clause

        Returns:
            Model instance or None if not found
        """
        result = await self.db.execute(
            select(self.model).where(where_clause)
        )
        return result.scalar_one_or_none()

    def _build_query(self) -> Select:
        """
        Build base SELECT query for this model.
        Protected method for use by subclasses.

        Returns:
            Base SQLAlchemy SELECT statement
        """
        return select(self.model)
