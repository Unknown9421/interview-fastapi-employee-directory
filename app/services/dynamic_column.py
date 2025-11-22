from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException, status

from app.models.dynamic_column import DynamicColumn
from app.schemas.dynamic_column import DynamicColumnCreate, DynamicColumnUpdate


class DynamicColumnService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, organization_id: UUID, data: DynamicColumnCreate) -> DynamicColumn:
        column = DynamicColumn(
            organization_id=organization_id,
            name=data.name,
            display_name=data.display_name,
            column_type=data.column_type,
            is_required=data.is_required,
            is_searchable=data.is_searchable,
            is_visible=data.is_visible,
            display_order=data.display_order,
            options=data.options,
            default_value=data.default_value
        )

        try:
            self.db.add(column)
            await self.db.flush()
            await self.db.refresh(column)
            return column
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Column with this name already exists in this organization"
            )

    async def get_by_id(self, organization_id: UUID, column_id: UUID) -> Optional[DynamicColumn]:
        result = await self.db.execute(
            select(DynamicColumn)
            .where(DynamicColumn.id == column_id)
            .where(DynamicColumn.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, organization_id: UUID, name: str) -> Optional[DynamicColumn]:
        result = await self.db.execute(
            select(DynamicColumn)
            .where(DynamicColumn.name == name)
            .where(DynamicColumn.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        organization_id: UUID,
        is_active: Optional[bool] = None,
        is_visible: Optional[bool] = None
    ) -> List[DynamicColumn]:
        query = (
            select(DynamicColumn)
            .where(DynamicColumn.organization_id == organization_id)
        )

        if is_active is not None:
            query = query.where(DynamicColumn.is_active == is_active)

        if is_visible is not None:
            query = query.where(DynamicColumn.is_visible == is_visible)

        query = query.order_by(DynamicColumn.display_order, DynamicColumn.name)
        result = await self.db.execute(query)

        return result.scalars().all()

    async def update(
        self,
        organization_id: UUID,
        column_id: UUID,
        data: DynamicColumnUpdate
    ) -> Optional[DynamicColumn]:
        column = await self.get_by_id(organization_id, column_id)

        if not column:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(column, field, value)

        try:
            await self.db.flush()
            await self.db.refresh(column)
            return column
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Update would violate unique constraints"
            )

    async def delete(self, organization_id: UUID, column_id: UUID) -> bool:
        column = await self.get_by_id(organization_id, column_id)

        if not column:
            return False

        await self.db.delete(column)
        await self.db.flush()
        return True

    async def reorder(
        self,
        organization_id: UUID,
        column_orders: List[dict]
    ) -> List[DynamicColumn]:
        """
        Reorder columns.
        column_orders: [{"id": UUID, "display_order": int}, ...]
        """
        columns = []

        for item in column_orders:
            column = await self.get_by_id(organization_id, item["id"])
            if column:
                column.display_order = item["display_order"]
                columns.append(column)

        await self.db.flush()
        return columns
