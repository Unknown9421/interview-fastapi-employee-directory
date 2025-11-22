import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status as http_status

from app.core.dependencies import get_organization_id, get_employee_service
from app.services.employee_service import EmployeeService
from app.schemas.employee import (
    PaginatedEmployeeResponse,
    PaginatedResponseDTO,
    PaginationMetaDTO,
    FilterOptionsDTO,
    EmployeeStatus,
)
from app.config import get_settings

router = APIRouter(prefix="/employees", tags=["employees"])
settings = get_settings()


@router.get(
    "/filters",
    response_model=FilterOptionsDTO,
    summary="Get filter options",
    description="Get available filter options for dropdowns (locations, companies, departments, positions).",
)
async def get_filter_options(
    organization_id: int = Depends(get_organization_id),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    """
    Get available filter options for the organization.

    Returns distinct values for:
    - Locations
    - Companies
    - Departments
    - Positions
    - Statuses (fixed list)
    """
    # Validate organization exists
    is_valid = await employee_service.validate_organization(organization_id)
    if not is_valid:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {organization_id} not found or inactive"
        )

    options = await employee_service.get_filter_options(organization_id)

    return FilterOptionsDTO(
        locations=options["locations"],
        companies=options["companies"],
        departments=options["departments"],
        positions=options["positions"],
    )


@router.get(
    "/search",
    response_model=PaginatedResponseDTO,
    summary="Search employees (cursor-based)",
    description="Search employees with cursor-based pagination for optimal performance with large datasets.",
)
async def search_employees_v2(
    organization_id: int = Depends(get_organization_id),
    employee_service: EmployeeService = Depends(get_employee_service),
    q: Optional[str] = Query(None, description="Search query (name, email)"),
    status: Optional[list[EmployeeStatus]] = Query(
        None,
        description="Filter by employee status (can select multiple)"
    ),
    location: Optional[str] = Query(None, description="Filter by location (exact match)"),
    company: Optional[str] = Query(None, description="Filter by company (exact match)"),
    department: Optional[str] = Query(None, description="Filter by department (exact match)"),
    position: Optional[str] = Query(None, description="Filter by position (exact match)"),
    include_terminated: bool = Query(
        False,
        description="Include terminated employees in results"
    ),
    cursor: Optional[int] = Query(None, description="Cursor for pagination (last employee ID)"),
    limit: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Number of items per page"
    ),
):
    """
    Search employees with cursor-based pagination.

    **Benefits of cursor-based pagination:**
    - Better performance for large datasets (no OFFSET)
    - Consistent results even with concurrent data changes
    - Memory efficient

    **How to use:**
    1. First request: Don't send cursor
    2. Next page: Send `cursor` = `next_cursor` from previous response
    3. Continue until `has_next` = false
    """
    # Validate organization exists
    is_valid = await employee_service.validate_organization(organization_id)
    if not is_valid:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {organization_id} not found or inactive"
        )

    # Get organization's visible columns configuration
    visible_columns = await employee_service.get_organization_config(organization_id)
    if not visible_columns:
        visible_columns = [
            "id", "avatar_url", "first_name", "last_name", "email", "phone",
            "status", "location", "company", "department", "position"
        ]

    # Convert status enums to values
    status_values = [s.value for s in status] if status else None

    # Search with cursor-based pagination
    employees, total, has_next, next_cursor = await employee_service.search_employees_cursor(
        organization_id=organization_id,
        q=q,
        status=status_values,
        location=location,
        company=company,
        department=department,
        position=position,
        include_terminated=include_terminated,
        cursor=cursor,
        limit=limit,
    )

    # Filter columns based on organization config
    filtered_employees = [
        employee_service.filter_employee_columns(emp, visible_columns)
        for emp in employees
    ]

    return PaginatedResponseDTO(
        items=filtered_employees,
        pagination=PaginationMetaDTO(
            total=total,
            limit=limit,
            has_next=has_next,
            next_cursor=next_cursor,
        )
    )


@router.get(
    "/search/legacy",
    response_model=PaginatedEmployeeResponse,
    summary="Search employees (offset-based)",
    description="Legacy search with offset pagination. Use /search for better performance.",
    deprecated=True,
)
async def search_employees_legacy(
    organization_id: int = Depends(get_organization_id),
    employee_service: EmployeeService = Depends(get_employee_service),
    status: Optional[list[EmployeeStatus]] = Query(
        None,
        description="Filter by employee status (can select multiple)"
    ),
    location: Optional[str] = Query(None, description="Filter by location (partial match)"),
    company: Optional[str] = Query(None, description="Filter by company (partial match)"),
    department: Optional[str] = Query(None, description="Filter by department (partial match)"),
    position: Optional[str] = Query(None, description="Filter by position (partial match)"),
    include_terminated: bool = Query(
        False,
        description="Include terminated employees in results"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Number of items per page"
    ),
):
    """
    Legacy search with offset-based pagination.

    **Warning:** This endpoint uses OFFSET which can be slow for large datasets.
    Use `/search` with cursor-based pagination for better performance.
    """
    # Validate organization exists
    is_valid = await employee_service.validate_organization(organization_id)
    if not is_valid:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {organization_id} not found or inactive"
        )

    # Get organization's visible columns configuration
    visible_columns = await employee_service.get_organization_config(organization_id)
    if not visible_columns:
        visible_columns = [
            "id", "avatar_url", "first_name", "last_name", "email", "phone",
            "status", "location", "company", "department", "position"
        ]

    # Convert status enums to values
    status_values = [s.value for s in status] if status else None

    # Search employees
    employees, total = await employee_service.search_employees(
        organization_id=organization_id,
        status=status_values,
        location=location,
        company=company,
        department=department,
        position=position,
        include_terminated=include_terminated,
        page=page,
        page_size=page_size,
    )

    # Filter columns based on organization config
    filtered_employees = [
        employee_service.filter_employee_columns(emp, visible_columns)
        for emp in employees
    ]

    # Calculate pagination info
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedEmployeeResponse(
        items=filtered_employees,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
