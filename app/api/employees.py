import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status as http_status

from app.core.dependencies import get_organization_id, get_employee_service
from app.services.employee_service import EmployeeService
from app.schemas.employee import PaginatedEmployeeResponse, EmployeeStatus
from app.config import get_settings

router = APIRouter(prefix="/employees", tags=["employees"])
settings = get_settings()


@router.get(
    "/search",
    response_model=PaginatedEmployeeResponse,
    summary="Search employees",
    description="Search employees with filters. Results are filtered based on organization's visible columns configuration.",
)
async def search_employees(
    organization_id: int = Depends(get_organization_id),
    employee_service: EmployeeService = Depends(get_employee_service),
    status: Optional[EmployeeStatus] = Query(None, description="Filter by employee status"),
    location: Optional[str] = Query(None, description="Filter by location (partial match)"),
    company: Optional[str] = Query(None, description="Filter by company (partial match)"),
    department: Optional[str] = Query(None, description="Filter by department (partial match)"),
    position: Optional[str] = Query(None, description="Filter by position (partial match)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Number of items per page"
    ),
):
    """
    Search employees with filtering and pagination.

    - **Multi-tenancy**: Only returns employees from the specified organization
    - **Dynamic columns**: Response fields are filtered based on organization's configuration
    - **Pagination**: Results are paginated for performance
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
        # Default visible columns if no config exists
        visible_columns = [
            "id", "first_name", "last_name", "email",
            "status", "location", "company", "department", "position"
        ]

    # Search employees
    employees, total = await employee_service.search_employees(
        organization_id=organization_id,
        status=status.value if status else None,
        location=location,
        company=company,
        department=department,
        position=position,
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
