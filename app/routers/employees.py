from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.core.database import get_db
from app.core.config import settings
from app.middleware.tenant import get_current_organization, TenantContext
from app.services.employee import EmployeeService
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    EmployeeList, EmployeeSearch
)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: EmployeeCreate,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create a new employee in the current organization."""
    service = EmployeeService(db)
    return await service.create(tenant.organization_id, data)


@router.get("", response_model=EmployeeList)
async def list_employees(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    is_active: Optional[bool] = None,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    List all employees in the current organization with pagination.
    Optimized for large datasets.
    """
    service = EmployeeService(db)
    skip = (page - 1) * page_size

    employees, total = await service.get_all(
        tenant.organization_id,
        skip=skip,
        limit=page_size,
        is_active=is_active
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return EmployeeList(
        items=employees,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/search", response_model=EmployeeList)
async def search_employees(
    search_params: EmployeeSearch,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Search employees with various filters.
    Optimized for millions of records using composite indexes.

    - **query**: Search across first_name, last_name, email, employee_id
    - **department**: Filter by exact department
    - **position**: Filter by exact position
    - **is_active**: Filter by active status
    - **custom_field_filters**: Filter by custom field values (JSONB)
    """
    service = EmployeeService(db)
    skip = (page - 1) * page_size

    employees, total = await service.search(
        tenant.organization_id,
        search_params,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return EmployeeList(
        items=employees,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/departments", response_model=List[str])
async def list_departments(
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get all distinct departments in the organization."""
    service = EmployeeService(db)
    return await service.get_departments(tenant.organization_id)


@router.get("/positions", response_model=List[str])
async def list_positions(
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get all distinct positions in the organization."""
    service = EmployeeService(db)
    return await service.get_positions(tenant.organization_id)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific employee by ID."""
    service = EmployeeService(db)
    employee = await service.get_by_id(tenant.organization_id, employee_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return employee


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    data: EmployeeUpdate,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an employee's information.
    Custom fields are merged with existing values.
    """
    service = EmployeeService(db)
    employee = await service.update(tenant.organization_id, employee_id, data)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: UUID,
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Delete an employee."""
    service = EmployeeService(db)

    if not await service.delete(tenant.organization_id, employee_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )


@router.post("/bulk", response_model=List[EmployeeResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_employees(
    employees: List[EmployeeCreate],
    tenant: TenantContext = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk create multiple employees at once.
    More efficient for importing large datasets.
    """
    if len(employees) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 1000 employees per bulk request"
        )

    service = EmployeeService(db)
    return await service.bulk_create(tenant.organization_id, employees)
