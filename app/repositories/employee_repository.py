"""
Employee Repository with specialized queries.
Handles all database operations for Employee entity.
"""
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.employee import Employee, EmployeeStatus


class EmployeeRepository(BaseRepository[Employee]):
    """
    Repository for Employee entity with complex search and filter operations.

    Provides methods for:
    - Advanced search with multiple filters
    - Deferred Join pagination for performance
    - Getting distinct values for filter dropdowns
    - Organization-scoped queries
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize EmployeeRepository.

        Args:
            db: Async database session
        """
        super().__init__(Employee, db)

    async def find_by_organization(
        self,
        organization_id: int,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Employee], int]:
        """
        Search employees with Deferred Join (Late Row Lookup) pagination.

        This technique splits the query into 2 steps:
        1. Get IDs only (fast - uses covering index)
        2. JOIN back to get full data for those IDs only

        Performance: 10x-100x faster for deep pages compared to simple OFFSET.

        Args:
            organization_id: Organization ID to filter by
            filters: Dictionary of filter conditions:
                - q: Text search term (searches first_name, last_name, email)
                - status: List of status values to filter by
                - locations: List of locations to filter by
                - companies: List of companies to filter by
                - departments: List of departments to filter by
                - positions: List of positions to filter by
                - include_terminated: Include terminated employees (default False)
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of employees, total count)
        """
        # Build WHERE conditions
        conditions = self._build_search_conditions(organization_id, filters)

        # Step 1: Count total (for pagination info)
        total = await self._count_with_conditions(conditions)

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

    async def get_distinct_values(
        self,
        organization_id: int,
        column_name: str
    ) -> List[str]:
        """
        Get distinct values for a column (used for filter dropdowns).

        Args:
            organization_id: Organization ID to filter by
            column_name: Column name to get distinct values from
                         (location, company, department, position)

        Returns:
            Sorted list of distinct non-null values

        Raises:
            AttributeError: If column_name doesn't exist on Employee model
        """
        # Get column dynamically
        if not hasattr(Employee, column_name):
            raise AttributeError(
                f"Employee model has no attribute '{column_name}'"
            )

        column = getattr(Employee, column_name)

        # Query distinct values
        result = await self.db.execute(
            select(distinct(column))
            .where(Employee.organization_id == organization_id)
            .where(Employee.is_deleted == False)
            .where(column.isnot(None))
            .order_by(column)
        )

        return [row[0] for row in result.fetchall()]

    async def get_filter_options(
        self,
        organization_id: int
    ) -> Dict[str, List[str]]:
        """
        Get all available filter options for dropdowns.

        Returns distinct values for locations, companies, departments, positions.

        Args:
            organization_id: Organization ID to filter by

        Returns:
            Dictionary with keys: locations, companies, departments, positions
        """
        # Mapping of singular field names to plural keys
        # (handles irregular plurals like "company" -> "companies")
        field_mapping = {
            "location": "locations",
            "company": "companies",  # Irregular plural
            "department": "departments",
            "position": "positions",
        }

        options = {}
        for field, plural_key in field_mapping.items():
            options[plural_key] = await self.get_distinct_values(
                organization_id, field
            )

        return options

    async def exists_by_organization(self, organization_id: int) -> bool:
        """
        Check if organization has any employees.

        Args:
            organization_id: Organization ID to check

        Returns:
            True if organization has employees, False otherwise
        """
        result = await self.db.execute(
            select(func.count(Employee.id))
            .where(Employee.organization_id == organization_id)
            .where(Employee.is_deleted == False)
        )
        return result.scalar() > 0

    async def count_by_organization(
        self,
        organization_id: int,
        include_deleted: bool = False
    ) -> int:
        """
        Count employees in an organization.

        Args:
            organization_id: Organization ID to count
            include_deleted: Include soft-deleted employees in count

        Returns:
            Number of employees
        """
        query = select(func.count(Employee.id)).where(
            Employee.organization_id == organization_id
        )

        if not include_deleted:
            query = query.where(Employee.is_deleted == False)

        result = await self.db.execute(query)
        return result.scalar()

    # ===== PRIVATE HELPER METHODS =====

    def _build_search_conditions(
        self,
        organization_id: int,
        filters: Dict[str, Any]
    ) -> List[Any]:
        """
        Build WHERE conditions from filters dictionary.

        Args:
            organization_id: Organization ID to filter by
            filters: Dictionary of filter conditions

        Returns:
            List of SQLAlchemy WHERE clauses
        """
        conditions = [
            Employee.organization_id == organization_id,
            Employee.is_deleted == False,
        ]

        # Handle include_terminated toggle
        include_terminated = filters.get("include_terminated", False)
        if not include_terminated:
            conditions.append(Employee.status != EmployeeStatus.TERMINATED)

        # Text search (search in first_name, last_name, email)
        if q := filters.get("q"):
            search_term = f"%{q}%"
            conditions.append(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.email.ilike(search_term),
                )
            )

        # Apply status filter (multiple selection)
        if status := filters.get("status"):
            # Convert string values to EmployeeStatus enums
            valid_statuses = []
            for s in status:
                try:
                    # Handle both string and enum values
                    if isinstance(s, EmployeeStatus):
                        valid_statuses.append(s)
                    else:
                        valid_statuses.append(EmployeeStatus(s))
                except ValueError:
                    pass  # Skip invalid status values
            if valid_statuses:
                conditions.append(Employee.status.in_(valid_statuses))

        # Apply multi-select filters
        if locations := filters.get("locations"):
            conditions.append(Employee.location.in_(locations))

        if companies := filters.get("companies"):
            conditions.append(Employee.company.in_(companies))

        if departments := filters.get("departments"):
            conditions.append(Employee.department.in_(departments))

        if positions := filters.get("positions"):
            conditions.append(Employee.position.in_(positions))

        return conditions

    async def _count_with_conditions(self, conditions: List[Any]) -> int:
        """
        Count records matching WHERE conditions.

        Args:
            conditions: List of SQLAlchemy WHERE clauses

        Returns:
            Number of matching records
        """
        result = await self.db.execute(
            select(func.count(Employee.id)).where(*conditions)
        )
        return result.scalar()
