from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.middleware.tenant import get_current_organization, TenantContext
from app.services.api_key import APIKeyService
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyResponseWithoutKey

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key for the current organization.
    The full key is only returned once upon creation.
    """
    service = APIKeyService(db)
    return await service.create(tenant.organization_id, data)


@router.get("", response_model=List[APIKeyResponseWithoutKey])
async def list_api_keys(
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys for the current organization.
    Keys are partially masked for security.
    """
    service = APIKeyService(db)
    return await service.get_all(tenant.organization_id)


@router.post("/{key_id}/deactivate", response_model=APIKeyResponseWithoutKey)
async def deactivate_api_key(
    key_id: UUID,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate an API key. It can no longer be used for authentication."""
    service = APIKeyService(db)
    api_key = await service.deactivate(tenant.organization_id, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return api_key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Permanently delete an API key."""
    service = APIKeyService(db)

    if not await service.delete(tenant.organization_id, key_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
