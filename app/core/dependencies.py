from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.employee_service import EmployeeService
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import OrganizationRepository


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


# ===== Repository Factories =====

def get_employee_repository(
    db: AsyncSession = Depends(get_db)
) -> EmployeeRepository:
    """
    Factory for injecting EmployeeRepository.

    Args:
        db: Database session from dependency injection

    Returns:
        EmployeeRepository instance
    """
    return EmployeeRepository(db)


def get_organization_repository(
    db: AsyncSession = Depends(get_db)
) -> OrganizationRepository:
    """
    Factory for injecting OrganizationRepository.

    Args:
        db: Database session from dependency injection

    Returns:
        OrganizationRepository instance
    """
    return OrganizationRepository(db)


# ===== Service Factory (Refactored) =====

def get_employee_service(
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    org_repo: OrganizationRepository = Depends(get_organization_repository),
) -> EmployeeService:
    """
    Factory for injecting EmployeeService with repositories.

    Service no longer receives database session directly - it only works
    with repositories, following Dependency Inversion Principle (DIP).

    Args:
        employee_repo: Employee repository from dependency injection
        org_repo: Organization repository from dependency injection

    Returns:
        EmployeeService instance configured with repositories
    """
    return EmployeeService(
        employee_repo=employee_repo,
        org_repo=org_repo
    )
