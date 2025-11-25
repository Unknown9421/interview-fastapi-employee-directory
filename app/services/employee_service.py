"""
Employee Service - Business Logic Layer.

This service contains ONLY business logic and orchestrates repository calls.
NO database queries should exist in this layer.
"""
from typing import Optional, Any

from app.models.employee import Employee
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import OrganizationRepository


class EmployeeService:
    """
    Service layer for employee operations with business logic.

    This service coordinates between multiple repositories and contains
    business logic such as filtering employee columns based on organization config.

    Following Repository Pattern:
    - NO direct database access (no SQLAlchemy queries)
    - ONLY business logic and orchestration
    - Delegates all data access to repositories
    """

    def __init__(
        self,
        employee_repo: EmployeeRepository,
        org_repo: OrganizationRepository
    ):
        """
        Initialize service with repository dependencies.

        Args:
            employee_repo: Repository for employee data access
            org_repo: Repository for organization data access
        """
        self.employee_repo = employee_repo
        self.org_repo = org_repo

    async def get_organization_config(self, organization_id: int) -> Optional[list[str]]:
        """
        Get visible columns configuration for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            List of visible column names, or None if no config exists
        """
        return await self.org_repo.get_visible_columns(organization_id)

    async def validate_organization(self, organization_id: int) -> bool:
        """
        Check if organization exists and is active.

        Args:
            organization_id: Organization ID to validate

        Returns:
            True if organization exists and is active, False otherwise
        """
        return await self.org_repo.exists_and_active(organization_id)

    async def get_filter_options(self, organization_id: int) -> dict[str, list[str]]:
        """
        Get available filter options for dropdowns.

        Returns distinct values for locations, companies, departments, positions.

        Args:
            organization_id: Organization ID to get filter options for

        Returns:
            Dictionary with keys: locations, companies, departments, positions
        """
        return await self.employee_repo.get_filter_options(organization_id)

    async def search_employees(
        self,
        organization_id: int,
        q: Optional[str] = None,
        status: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        companies: Optional[list[str]] = None,
        departments: Optional[list[str]] = None,
        positions: Optional[list[str]] = None,
        include_terminated: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Employee], int]:
        """
        Search employees with advanced filtering and pagination.

        This method delegates to EmployeeRepository which implements
        Deferred Join pagination for optimal performance.

        Args:
            organization_id: Organization ID to search within
            q: Text search query (searches first_name, last_name, email)
            status: List of status values to filter by
            locations: List of locations to filter by
            companies: List of companies to filter by
            departments: List of departments to filter by
            positions: List of positions to filter by
            include_terminated: Include terminated employees in results
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of employees, total count)
        """
        # Build filters dictionary
        filters = {
            "q": q,
            "status": status,
            "locations": locations,
            "companies": companies,
            "departments": departments,
            "positions": positions,
            "include_terminated": include_terminated,
        }

        # Delegate to repository
        return await self.employee_repo.find_by_organization(
            organization_id, filters, page, page_size
        )

    def filter_employee_columns(
        self, employee: Employee, visible_columns: list[str]
    ) -> dict[str, Any]:
        """
        Filter employee data based on visible columns configuration.

        This is BUSINESS LOGIC - determines what data should be exposed to API clients
        based on organization configuration.

        Args:
            employee: Employee entity from database
            visible_columns: List of column names that should be visible

        Returns:
            Dictionary with only visible columns and their values
        """
        all_columns = {
            "id": employee.id,
            "avatar_url": employee.avatar_url,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "email": employee.email,
            "phone": employee.phone,
            "status": employee.status.value if employee.status else None,
            "location": employee.location,
            "company": employee.company,
            "department": employee.department,
            "position": employee.position,
            "created_at": employee.created_at.isoformat() if employee.created_at else None,
            "updated_at": employee.updated_at.isoformat() if employee.updated_at else None,
        }

        # Return only visible columns (business rule)
        return {k: v for k, v in all_columns.items() if k in visible_columns}
