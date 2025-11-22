from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.dynamic_column import ColumnType


class DynamicColumnBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z_][a-z0-9_]*$")
    display_name: str = Field(..., min_length=1, max_length=255)
    column_type: ColumnType = ColumnType.STRING
    is_required: bool = False
    is_searchable: bool = True
    is_visible: bool = True
    display_order: int = 0
    options: Optional[str] = Field(None, max_length=1000)
    default_value: Optional[str] = Field(None, max_length=500)


class DynamicColumnCreate(DynamicColumnBase):
    pass


class DynamicColumnUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    column_type: Optional[ColumnType] = None
    is_required: Optional[bool] = None
    is_searchable: Optional[bool] = None
    is_visible: Optional[bool] = None
    display_order: Optional[int] = None
    options: Optional[str] = Field(None, max_length=1000)
    default_value: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class DynamicColumnResponse(DynamicColumnBase):
    id: UUID
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
