from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeSearch


class EmployeeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, organization_id: UUID, data: EmployeeCreate) -> Employee:
        employee = Employee(
            organization_id=organization_id,
            employee_id=data.employee_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            department=data.department,
            position=data.position,
            manager_id=data.manager_id,
            hire_date=data.hire_date,
            custom_fields=data.custom_fields or {}
        )

        try:
            self.db.add(employee)
            await self.db.flush()
            await self.db.refresh(employee)
            return employee
        except IntegrityError as e:
            await self.db.rollback()
            if "ix_employees_org_employee_id" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Employee with this employee_id already exists in this organization"
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Database integrity error"
            )

    async def get_by_id(self, organization_id: UUID, employee_id: UUID) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee)
            .where(Employee.id == employee_id)
            .where(Employee.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_by_employee_id(self, organization_id: UUID, employee_id: str) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee)
            .where(Employee.employee_id == employee_id)
            .where(Employee.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        organization_id: UUID,
        search_params: EmployeeSearch,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Employee], int]:
        """
        High-performance search optimized for millions of records.
        Uses composite indexes and efficient query building.
        """
        # Base query with organization filter (uses index)
        query = select(Employee).where(Employee.organization_id == organization_id)

        # Build WHERE conditions
        conditions = []

        # Text search on name, email, employee_id
        if search_params.query:
            search_term = f"%{search_params.query}%"
            conditions.append(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.email.ilike(search_term),
                    Employee.employee_id.ilike(search_term),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term)
                )
            )

        # Department filter (uses index)
        if search_params.department:
            conditions.append(Employee.department == search_params.department)

        # Position filter (uses index)
        if search_params.position:
            conditions.append(Employee.position == search_params.position)

        # Active status filter (uses index)
        if search_params.is_active is not None:
            conditions.append(Employee.is_active == search_params.is_active)

        # Custom field filters (uses GIN index on JSONB)
        if search_params.custom_field_filters:
            for key, value in search_params.custom_field_filters.items():
                # Use PostgreSQL JSONB containment operator
                conditions.append(
                    Employee.custom_fields.contains({key: value})
                )

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))

        # Get total count efficiently
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # Apply pagination and ordering
        query = (
            query
            .order_by(Employee.last_name, Employee.first_name)
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all(), total_count

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None
    ) -> tuple[List[Employee], int]:
        query = select(Employee).where(Employee.organization_id == organization_id)

        if is_active is not None:
            query = query.where(Employee.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar()

        # Get paginated results
        query = (
            query
            .order_by(Employee.last_name, Employee.first_name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)

        return result.scalars().all(), total_count

    async def update(
        self,
        organization_id: UUID,
        employee_id: UUID,
        data: EmployeeUpdate
    ) -> Optional[Employee]:
        employee = await self.get_by_id(organization_id, employee_id)

        if not employee:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle custom_fields merge
        if 'custom_fields' in update_data and update_data['custom_fields'] is not None:
            # Merge with existing custom fields
            existing_fields = employee.custom_fields or {}
            existing_fields.update(update_data['custom_fields'])
            update_data['custom_fields'] = existing_fields

        for field, value in update_data.items():
            setattr(employee, field, value)

        try:
            await self.db.flush()
            await self.db.refresh(employee)
            return employee
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Update would violate unique constraints"
            )

    async def delete(self, organization_id: UUID, employee_id: UUID) -> bool:
        employee = await self.get_by_id(organization_id, employee_id)

        if not employee:
            return False

        await self.db.delete(employee)
        await self.db.flush()
        return True

    async def bulk_create(
        self,
        organization_id: UUID,
        employees_data: List[EmployeeCreate]
    ) -> List[Employee]:
        """Bulk create employees for better performance with large datasets."""
        employees = []

        for data in employees_data:
            employee = Employee(
                organization_id=organization_id,
                employee_id=data.employee_id,
                first_name=data.first_name,
                last_name=data.last_name,
                email=data.email,
                phone=data.phone,
                department=data.department,
                position=data.position,
                manager_id=data.manager_id,
                hire_date=data.hire_date,
                custom_fields=data.custom_fields or {}
            )
            employees.append(employee)

        try:
            self.db.add_all(employees)
            await self.db.flush()
            return employees
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="One or more employees violate unique constraints"
            )

    async def get_departments(self, organization_id: UUID) -> List[str]:
        """Get distinct departments for an organization."""
        result = await self.db.execute(
            select(Employee.department)
            .where(Employee.organization_id == organization_id)
            .where(Employee.department.isnot(None))
            .distinct()
            .order_by(Employee.department)
        )
        return [row[0] for row in result.all()]

    async def get_positions(self, organization_id: UUID) -> List[str]:
        """Get distinct positions for an organization."""
        result = await self.db.execute(
            select(Employee.position)
            .where(Employee.organization_id == organization_id)
            .where(Employee.position.isnot(None))
            .distinct()
            .order_by(Employee.position)
        )
        return [row[0] for row in result.all()]
