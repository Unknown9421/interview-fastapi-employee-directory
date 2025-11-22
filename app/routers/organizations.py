from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.tenant import get_current_organization, TenantContext
from app.schemas.organization import OrganizationResponse

router = APIRouter(prefix="/organization", tags=["Organization"])


@router.get("/me", response_model=OrganizationResponse)
async def get_current_org(
    tenant: TenantContext = Depends(get_current_organization)
):
    """
    Get the current organization based on API key.
    This endpoint is useful for clients to verify their API key and get organization info.
    """
    return tenant.organization
