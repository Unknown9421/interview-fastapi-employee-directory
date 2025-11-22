from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from datetime import datetime


class EmployeeStatus(str, Enum):
    ACTIVE = "Active"
    NOT_STARTED = "Not started"
    TERMINATED = "Terminated"


# ==================== DTOs ====================

class EmployeeCreateDTO(BaseModel):
    """DTO for creating an employee."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    location: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    position: Optional[str] = Field(None, max_length=255)


class EmployeeResponseDTO(BaseModel):
    """DTO for employee response with dynamic columns."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    avatar_url: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[EmployeeStatus] = None
    location: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==================== Search/Filter DTOs ====================

class SearchRequestDTO(BaseModel):
    """DTO for search request parameters."""
    # Text search
    q: Optional[str] = Field(None, description="Search query for name/email")

    # Filters
    status: Optional[list[EmployeeStatus]] = Field(None, description="Filter by status (multiple)")
    location: Optional[str] = Field(None, description="Filter by location")
    company: Optional[str] = Field(None, description="Filter by company")
    department: Optional[str] = Field(None, description="Filter by department")
    position: Optional[str] = Field(None, description="Filter by position")

    # Terminated toggle
    include_terminated: bool = Field(False, description="Include terminated employees")

    # Cursor-based pagination
    cursor: Optional[int] = Field(None, description="Cursor (last employee ID from previous page)")
    limit: int = Field(20, ge=1, le=100, description="Number of items per page")


class PaginationMetaDTO(BaseModel):
    """DTO for pagination metadata."""
    total: int
    limit: int
    has_next: bool
    next_cursor: Optional[int] = None


class PaginatedResponseDTO(BaseModel):
    """DTO for paginated response with cursor-based pagination."""
    items: list[dict[str, Any]]
    pagination: PaginationMetaDTO


# ==================== Filter Options DTOs ====================

class FilterOptionsDTO(BaseModel):
    """DTO for available filter options."""
    locations: list[str]
    companies: list[str]
    departments: list[str]
    positions: list[str]
    statuses: list[str] = [s.value for s in EmployeeStatus]


# ==================== Legacy Support (backward compatibility) ====================

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    status: EmployeeStatus
    location: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None


class EmployeeResponse(EmployeeResponseDTO):
    """Alias for backward compatibility."""
    pass


class EmployeeSearchParams(BaseModel):
    """Legacy search params - use SearchRequestDTO instead."""
    status: Optional[list[EmployeeStatus]] = None
    location: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    include_terminated: bool = False
    page: int = 1
    page_size: int = 20


class PaginatedEmployeeResponse(BaseModel):
    """Legacy paginated response - use PaginatedResponseDTO instead."""
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
