"""
Organization Repository with organization-specific queries.
Handles all database operations for Organization and OrganizationConfig entities.
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.organization import Organization, OrganizationConfig


class OrganizationRepository(BaseRepository[Organization]):
    """
    Repository for Organization entity.

    Provides methods for:
    - Getting active organizations
    - Validating organization existence
    - Getting organization configuration (visible columns)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize OrganizationRepository.

        Args:
            db: Async database session
        """
        super().__init__(Organization, db)

    async def get_active_by_id(self, org_id: int) -> Optional[Organization]:
        """
        Get active organization by ID.

        Args:
            org_id: Organization ID

        Returns:
            Organization instance or None if not found or inactive
        """
        result = await self.db.execute(
            select(Organization)
            .where(Organization.id == org_id)
            .where(Organization.is_active == True)
        )
        return result.scalar_one_or_none()

    async def exists_and_active(self, org_id: int) -> bool:
        """
        Check if organization exists and is active.

        This method is used for validation in API endpoints.

        Args:
            org_id: Organization ID to check

        Returns:
            True if organization exists and is active, False otherwise
        """
        result = await self.db.execute(
            select(Organization.id)
            .where(Organization.id == org_id)
            .where(Organization.is_active == True)
        )
        return result.scalar_one_or_none() is not None

    async def get_visible_columns(self, org_id: int) -> Optional[List[str]]:
        """
        Get visible columns configuration for an organization.

        This configuration determines which employee fields should be returned
        in API responses for this organization.

        Args:
            org_id: Organization ID

        Returns:
            List of column names that should be visible, or None if no config exists
        """
        result = await self.db.execute(
            select(OrganizationConfig.visible_columns)
            .where(OrganizationConfig.organization_id == org_id)
        )
        config = result.scalar_one_or_none()
        return config if config else None

    async def update_visible_columns(
        self,
        org_id: int,
        columns: List[str]
    ) -> bool:
        """
        Update visible columns configuration for an organization.

        Args:
            org_id: Organization ID
            columns: List of column names to make visible

        Returns:
            True if updated successfully, False if organization not found
        """
        result = await self.db.execute(
            select(OrganizationConfig)
            .where(OrganizationConfig.organization_id == org_id)
        )
        config = result.scalar_one_or_none()

        if config:
            config.visible_columns = columns
            await self.db.flush()
            return True
        return False

    async def get_all_active(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """
        Get all active organizations with pagination.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return

        Returns:
            List of active organizations
        """
        result = await self.db.execute(
            select(Organization)
            .where(Organization.is_active == True)
            .order_by(Organization.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def deactivate(self, org_id: int) -> bool:
        """
        Deactivate an organization.

        Args:
            org_id: Organization ID to deactivate

        Returns:
            True if deactivated successfully, False if not found
        """
        org = await self.get_by_id(org_id)
        if org:
            org.is_active = False
            await self.db.flush()
            return True
        return False

    async def activate(self, org_id: int) -> bool:
        """
        Activate an organization.

        Args:
            org_id: Organization ID to activate

        Returns:
            True if activated successfully, False if not found
        """
        org = await self.get_by_id(org_id)
        if org:
            org.is_active = True
            await self.db.flush()
            return True
        return False
