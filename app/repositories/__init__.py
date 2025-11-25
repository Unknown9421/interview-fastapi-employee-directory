"""
Repository Layer - Data Access Abstraction.

This layer contains all database access logic, providing a clean interface
for the service layer to interact with data without knowing database details.

Key Components:
- BaseRepository: Generic CRUD operations for any entity
- EmployeeRepository: Employee-specific queries and operations
- OrganizationRepository: Organization-specific queries and operations

Benefits:
- Separation of Concerns: Service layer contains only business logic
- Testability: Easy to mock repositories for unit testing
- Maintainability: Database changes don't affect business logic
- Reusability: BaseRepository reduces code duplication
"""
from app.repositories.base import BaseRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import OrganizationRepository

__all__ = [
    "BaseRepository",
    "EmployeeRepository",
    "OrganizationRepository",
]
