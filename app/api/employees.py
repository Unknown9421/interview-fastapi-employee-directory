import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status as http_status

from app.core.dependencies import get_organization_id, get_employee_service
from app.services.employee_service import EmployeeService
from app.schemas.employee import (
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
    "",
    response_model=PaginatedResponseDTO,
    summary="List employees",
    description="Get employees with filters and pagination. Supports multi-select filters and page jumping.",
)
async def list_employees(
    organization_id: int = Depends(get_organization_id),
    employee_service: EmployeeService = Depends(get_employee_service),
    q: Optional[str] = Query(None, description="Search query (name, email)"),
    status: Optional[list[EmployeeStatus]] = Query(
        None,
        description="Filter by employee status (can select multiple)"
    ),
    location: Optional[list[str]] = Query(
        None,
        description="Filter by locations (can select multiple)"
    ),
    company: Optional[list[str]] = Query(
        None,
        description="Filter by companies (can select multiple)"
    ),
    department: Optional[list[str]] = Query(
        None,
        description="Filter by departments (can select multiple)"
    ),
    position: Optional[list[str]] = Query(
        None,
        description="Filter by positions (can select multiple)"
    ),
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
    List employees with filters and pagination.

    **Features:**
    - Multi-select filters for location, company, department, position
    - Text search across name and email
    - Page jumping support (go to any page directly)
    - Optimized with Deferred Join for large datasets

    **Example:**
    ```
    GET /api/v1/employees?department=Engineering&department=Sales&page=5
    ```
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

    # Search with Deferred Join pagination
    employees, total = await employee_service.search_employees(
        organization_id=organization_id,
        q=q,
        status=status_values,
        locations=location,
        companies=company,
        departments=department,
        positions=position,
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

    return PaginatedResponseDTO(
        items=filtered_employees,
        pagination=PaginationMetaDTO(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )
