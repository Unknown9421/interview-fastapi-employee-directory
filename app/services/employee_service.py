from typing import Optional, Any
from sqlalchemy import select, func, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee, EmployeeStatus
from app.models.organization import Organization, OrganizationConfig


class EmployeeService:
    """Service layer for employee operations with optimized queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_organization_config(self, organization_id: int) -> Optional[list[str]]:
        """Get visible columns configuration for an organization."""
        result = await self.db.execute(
            select(OrganizationConfig.visible_columns)
            .where(OrganizationConfig.organization_id == organization_id)
        )
        config = result.scalar_one_or_none()
        return config if config else None

    async def validate_organization(self, organization_id: int) -> bool:
        """Check if organization exists and is active."""
        result = await self.db.execute(
            select(Organization.id)
            .where(Organization.id == organization_id)
            .where(Organization.is_active == True)
        )
        return result.scalar_one_or_none() is not None

    async def get_filter_options(self, organization_id: int) -> dict[str, list[str]]:
        """
        Get available filter options for dropdowns.
        Returns distinct values for locations, companies, departments, positions.
        """
        # Use a single query with multiple columns for efficiency
        # Only get options from non-deleted, non-terminated employees by default
        base_query = (
            select(Employee)
            .where(Employee.organization_id == organization_id)
            .where(Employee.is_deleted == False)
        )

        # Get distinct locations
        locations_result = await self.db.execute(
            select(distinct(Employee.location))
            .where(Employee.organization_id == organization_id)
            .where(Employee.is_deleted == False)
            .where(Employee.location.isnot(None))
            .order_by(Employee.location)
        )
        locations = [row[0] for row in locations_result.fetchall()]

        # Get distinct companies
        companies_result = await self.db.execute(
            select(distinct(Employee.company))
            .where(Employee.organization_id == organization_id)
            .where(Employee.is_deleted == False)
            .where(Employee.company.isnot(None))
            .order_by(Employee.company)
        )
        companies = [row[0] for row in companies_result.fetchall()]

        # Get distinct departments
        departments_result = await self.db.execute(
            select(distinct(Employee.department))
            .where(Employee.organization_id == organization_id)
            .where(Employee.is_deleted == False)
            .where(Employee.department.isnot(None))
            .order_by(Employee.department)
        )
        departments = [row[0] for row in departments_result.fetchall()]

        # Get distinct positions
        positions_result = await self.db.execute(
            select(distinct(Employee.position))
            .where(Employee.organization_id == organization_id)
            .where(Employee.is_deleted == False)
            .where(Employee.position.isnot(None))
            .order_by(Employee.position)
        )
        positions = [row[0] for row in positions_result.fetchall()]

        return {
            "locations": locations,
            "companies": companies,
            "departments": departments,
            "positions": positions,
        }

    async def search_employees_cursor(
        self,
        organization_id: int,
        q: Optional[str] = None,
        status: Optional[list[str]] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        department: Optional[str] = None,
        position: Optional[str] = None,
        include_terminated: bool = False,
        cursor: Optional[int] = None,
        limit: int = 20,
    ) -> tuple[list[Employee], int, bool, Optional[int]]:
        """
        Search employees with cursor-based pagination.

        Returns: (employees, total_count, has_next, next_cursor)

        Cursor-based pagination is more efficient for large datasets:
        - Uses keyset pagination (WHERE id > cursor)
        - Consistent results even with concurrent modifications
        - Better performance than OFFSET for large datasets
        """
        # Build base query with multi-tenancy filter
        query = select(Employee).where(Employee.organization_id == organization_id)

        # Filter out soft-deleted records
        query = query.where(Employee.is_deleted == False)

        # Handle include_terminated toggle
        if not include_terminated:
            query = query.where(Employee.status != EmployeeStatus.TERMINATED)

        # Text search (search in first_name, last_name, email)
        if q:
            search_term = f"%{q}%"
            query = query.where(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.email.ilike(search_term),
                )
            )

        # Apply status filter (multiple selection)
        if status:
            valid_statuses = []
            for s in status:
                try:
                    valid_statuses.append(EmployeeStatus(s))
                except ValueError:
                    pass

            if valid_statuses:
                query = query.where(Employee.status.in_(valid_statuses))

        # Apply text filters (exact match for dropdowns)
        if location:
            query = query.where(Employee.location == location)

        if company:
            query = query.where(Employee.company == company)

        if department:
            query = query.where(Employee.department == department)

        if position:
            query = query.where(Employee.position == position)

        # Get total count (without cursor filter)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply cursor-based pagination
        if cursor:
            query = query.where(Employee.id > cursor)

        # Order by ID for consistent cursor pagination
        query = query.order_by(Employee.id).limit(limit + 1)  # Fetch one extra to check has_next

        # Execute query
        result = await self.db.execute(query)
        employees = list(result.scalars().all())

        # Determine if there are more results
        has_next = len(employees) > limit
        if has_next:
            employees = employees[:limit]  # Remove the extra item

        # Get next cursor
        next_cursor = employees[-1].id if employees and has_next else None

        return employees, total, has_next, next_cursor

    async def search_employees(
        self,
        organization_id: int,
        status: Optional[list[str]] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        department: Optional[str] = None,
        position: Optional[str] = None,
        include_terminated: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Employee], int]:
        """
        Legacy search with offset pagination.
        Use search_employees_cursor for better performance.
        """
        # Build base query with multi-tenancy filter
        query = select(Employee).where(Employee.organization_id == organization_id)

        # Filter out soft-deleted records
        query = query.where(Employee.is_deleted == False)

        # Handle include_terminated toggle
        if not include_terminated:
            query = query.where(Employee.status != EmployeeStatus.TERMINATED)

        # Apply status filter (multiple selection)
        if status:
            valid_statuses = []
            for s in status:
                try:
                    valid_statuses.append(EmployeeStatus(s))
                except ValueError:
                    pass

            if valid_statuses:
                query = query.where(Employee.status.in_(valid_statuses))

        # Apply text filters
        if location:
            query = query.where(Employee.location.ilike(f"%{location}%"))

        if company:
            query = query.where(Employee.company.ilike(f"%{company}%"))

        if department:
            query = query.where(Employee.department.ilike(f"%{department}%"))

        if position:
            query = query.where(Employee.position.ilike(f"%{position}%"))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Employee.id)

        # Execute query
        result = await self.db.execute(query)
        employees = result.scalars().all()

        return list(employees), total

    def filter_employee_columns(
        self, employee: Employee, visible_columns: list[str]
    ) -> dict[str, Any]:
        """Filter employee data based on visible columns configuration."""
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

        # Return only visible columns
        return {k: v for k, v in all_columns.items() if k in visible_columns}
