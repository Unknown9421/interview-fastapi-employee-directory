from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID

from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate


class APIKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, organization_id: UUID, data: APIKeyCreate) -> APIKey:
        api_key = APIKey(
            organization_id=organization_id,
            key=APIKey.generate_key(),
            name=data.name,
            description=data.description,
            expires_at=data.expires_at
        )

        self.db.add(api_key)
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key

    async def get_by_id(self, organization_id: UUID, key_id: UUID) -> Optional[APIKey]:
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.id == key_id)
            .where(APIKey.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_by_key(self, key: str) -> Optional[APIKey]:
        result = await self.db.execute(
            select(APIKey).where(APIKey.key == key)
        )
        return result.scalar_one_or_none()

    async def get_all(self, organization_id: UUID) -> List[APIKey]:
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.organization_id == organization_id)
            .order_by(APIKey.created_at.desc())
        )
        return result.scalars().all()

    async def deactivate(self, organization_id: UUID, key_id: UUID) -> Optional[APIKey]:
        api_key = await self.get_by_id(organization_id, key_id)

        if not api_key:
            return None

        api_key.is_active = False
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key

    async def delete(self, organization_id: UUID, key_id: UUID) -> bool:
        api_key = await self.get_by_id(organization_id, key_id)

        if not api_key:
            return False

        await self.db.delete(api_key)
        await self.db.flush()
        return True
