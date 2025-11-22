from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.middleware.tenant import get_current_organization, TenantContext
from app.services.dynamic_column import DynamicColumnService
from app.schemas.dynamic_column import (
    DynamicColumnCreate, DynamicColumnUpdate, DynamicColumnResponse
)

router = APIRouter(prefix="/columns", tags=["Dynamic Columns"])


@router.post("", response_model=DynamicColumnResponse, status_code=status.HTTP_201_CREATED)
async def create_column(
    data: DynamicColumnCreate,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new dynamic column for the organization.
    Dynamic columns allow customizing employee data fields per organization.
    """
    service = DynamicColumnService(db)
    return await service.create(tenant.organization_id, data)


@router.get("", response_model=List[DynamicColumnResponse])
async def list_columns(
    is_active: bool = None,
    is_visible: bool = None,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    List all dynamic columns for the organization.
    Results are ordered by display_order.
    """
    service = DynamicColumnService(db)
    return await service.get_all(
        tenant.organization_id,
        is_active=is_active,
        is_visible=is_visible
    )


@router.get("/{column_id}", response_model=DynamicColumnResponse)
async def get_column(
    column_id: UUID,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific dynamic column by ID."""
    service = DynamicColumnService(db)
    column = await service.get_by_id(tenant.organization_id, column_id)

    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found"
        )

    return column


@router.patch("/{column_id}", response_model=DynamicColumnResponse)
async def update_column(
    column_id: UUID,
    data: DynamicColumnUpdate,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update a dynamic column's configuration."""
    service = DynamicColumnService(db)
    column = await service.update(tenant.organization_id, column_id, data)

    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found"
        )

    return column


@router.delete("/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    column_id: UUID,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete a dynamic column."""
    service = DynamicColumnService(db)

    if not await service.delete(tenant.organization_id, column_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found"
        )


@router.post("/reorder", response_model=List[DynamicColumnResponse])
async def reorder_columns(
    column_orders: List[dict],
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Reorder dynamic columns.

    Expected format:
    ```json
    [
        {"id": "uuid-1", "display_order": 0},
        {"id": "uuid-2", "display_order": 1}
    ]
    ```
    """
    service = DynamicColumnService(db)
    return await service.reorder(tenant.organization_id, column_orders)
