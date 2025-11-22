from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    expires_at: Optional[datetime] = None


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyResponse(BaseModel):
    id: UUID
    organization_id: UUID
    key: str
    name: str
    description: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]

    model_config = {"from_attributes": True}


class APIKeyResponseWithoutKey(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]

    model_config = {"from_attributes": True}
