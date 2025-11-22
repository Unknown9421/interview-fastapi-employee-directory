from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.services.organization import OrganizationService
from app.services.api_key import APIKeyService
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from app.schemas.api_key import APIKeyCreate, APIKeyResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new organization. This is an admin endpoint.
    In production, this should be protected by admin authentication.
    """
    service = OrganizationService(db)
    return await service.create(data)


@router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: AsyncSession = Depends(get_db)
):
    """List all organizations. Admin endpoint."""
    service = OrganizationService(db)
    organizations, _ = await service.get_all(skip=skip, limit=limit, is_active=is_active)
    return organizations


@router.get("/organizations/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get organization by ID. Admin endpoint."""
    from uuid import UUID
    service = OrganizationService(db)
    organization = await service.get_by_id(UUID(organization_id))
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return organization


@router.patch("/organizations/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update organization. Admin endpoint."""
    from uuid import UUID
    service = OrganizationService(db)
    organization = await service.update(UUID(organization_id), data)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return organization


@router.delete("/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete organization. Admin endpoint."""
    from uuid import UUID
    service = OrganizationService(db)
    if not await service.delete(UUID(organization_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )


@router.post("/organizations/{organization_id}/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key_for_organization(
    organization_id: str,
    data: APIKeyCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create an API key for an organization. Admin endpoint.
    Use this to create the first API key for a new organization.
    """
    from uuid import UUID

    # Verify organization exists
    org_service = OrganizationService(db)
    organization = await org_service.get_by_id(UUID(organization_id))
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    api_key_service = APIKeyService(db)
    return await api_key_service.create(UUID(organization_id), data)
