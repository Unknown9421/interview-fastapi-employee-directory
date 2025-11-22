from typing import Optional, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee, EmployeeStatus
from app.models.organization import Organization, OrganizationConfig


class EmployeeService:
    """Service layer for employee operations."""

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

    async def search_employees(
        self,
        organization_id: int,
        status: Optional[str] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        department: Optional[str] = None,
        position: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Employee], int]:
        """
        Search employees with filters and pagination.
        Returns (employees, total_count).
        """
        # Build base query with multi-tenancy filter
        query = select(Employee).where(Employee.organization_id == organization_id)

        # Apply filters
        if status:
            try:
                status_enum = EmployeeStatus(status)
                query = query.where(Employee.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter

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
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "email": employee.email,
            "phone": employee.phone,
            "status": employee.status.value if employee.status else None,
            "location": employee.location,
            "company": employee.company,
            "department": employee.department,
            "position": employee.position,
        }

        # Return only visible columns
        return {k: v for k, v in all_columns.items() if k in visible_columns}
