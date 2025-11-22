from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException, status

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: OrganizationCreate) -> Organization:
        organization = Organization(
            name=data.name,
            slug=data.slug,
            description=data.description
        )

        try:
            self.db.add(organization)
            await self.db.flush()
            await self.db.refresh(organization)
            return organization
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization with this name or slug already exists"
            )

    async def get_by_id(self, organization_id: UUID) -> Optional[Organization]:
        result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> tuple[List[Organization], int]:
        query = select(Organization)

        if is_active is not None:
            query = query.where(Organization.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Organization.name)
        result = await self.db.execute(query)

        return result.scalars().all(), total_count

    async def update(
        self,
        organization_id: UUID,
        data: OrganizationUpdate
    ) -> Optional[Organization]:
        organization = await self.get_by_id(organization_id)

        if not organization:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(organization, field, value)

        try:
            await self.db.flush()
            await self.db.refresh(organization)
            return organization
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization with this name or slug already exists"
            )

    async def delete(self, organization_id: UUID) -> bool:
        organization = await self.get_by_id(organization_id)

        if not organization:
            return False

        await self.db.delete(organization)
        await self.db.flush()
        return True
