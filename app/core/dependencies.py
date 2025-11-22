from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.employee_service import EmployeeService


async def get_organization_id(
    x_organization_id: int = Header(..., description="Organization ID for multi-tenancy")
) -> int:
    """Extract and validate organization ID from request header."""
    if x_organization_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID"
        )
    return x_organization_id


async def get_employee_service(
    db: AsyncSession = Depends(get_db)
) -> EmployeeService:
    """Get employee service instance."""
    return EmployeeService(db)
