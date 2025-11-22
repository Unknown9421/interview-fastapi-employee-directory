from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from enum import Enum


class EmployeeStatus(str, Enum):
    ACTIVE = "Active"
    NOT_STARTED = "Not started"
    TERMINATED = "Terminated"


class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    status: EmployeeStatus
    location: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[EmployeeStatus] = None
    location: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None


class EmployeeSearchParams(BaseModel):
    status: Optional[EmployeeStatus] = None
    location: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    page: int = 1
    page_size: int = 20


class PaginatedEmployeeResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
