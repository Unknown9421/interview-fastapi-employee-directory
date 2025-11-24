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
        Search employees with Deferred Join (Late Row Lookup) pagination.

        This technique splits the query into 2 steps:
        1. Get IDs only (fast - uses covering index)
        2. JOIN back to get full data for those IDs only

        Performance: 10x-100x faster for deep pages compared to simple OFFSET.
        """
        # Build base conditions for filtering
        conditions = [
            Employee.organization_id == organization_id,
            Employee.is_deleted == False,
        ]

        # Handle include_terminated toggle
        if not include_terminated:
            conditions.append(Employee.status != EmployeeStatus.TERMINATED)

        # Text search (search in first_name, last_name, email)
        if q:
            search_term = f"%{q}%"
            conditions.append(
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
                conditions.append(Employee.status.in_(valid_statuses))

        # Apply multi-select filters
        if locations:
            conditions.append(Employee.location.in_(locations))

        if companies:
            conditions.append(Employee.company.in_(companies))

        if departments:
            conditions.append(Employee.department.in_(departments))

        if positions:
            conditions.append(Employee.position.in_(positions))

        # Step 1: Count total (for pagination info)
        count_query = select(func.count(Employee.id)).where(*conditions)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Step 2: Deferred Join - Get IDs only (fast, uses index)
        offset = (page - 1) * page_size
        id_subquery = (
            select(Employee.id)
            .where(*conditions)
            .order_by(Employee.id)
            .limit(page_size)
            .offset(offset)
        ).subquery()

        # Step 3: JOIN back to get full employee data
        query = (
            select(Employee)
            .join(id_subquery, Employee.id == id_subquery.c.id)
            .order_by(Employee.id)
        )

        # Execute query
        result = await self.db.execute(query)
        employees = list(result.scalars().all())

        return employees, total

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
