from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class EmployeeBase(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[UUID] = None
    hire_date: Optional[datetime] = None
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    employee_id: Optional[str] = Field(None, min_length=1, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[UUID] = None
    hire_date: Optional[datetime] = None
    custom_fields: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    id: UUID
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmployeeList(BaseModel):
    items: List[EmployeeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EmployeeSearch(BaseModel):
    query: Optional[str] = Field(None, description="Search query for name, email, employee_id")
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None
    custom_field_filters: Optional[Dict[str, Any]] = Field(default=None, description="Filter by custom fields")
