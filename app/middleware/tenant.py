from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.models.organization import Organization
from app.models.api_key import APIKey


# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class TenantContext:
    """Context object to hold current tenant information."""

    def __init__(self, organization: Organization, api_key: APIKey):
        self.organization = organization
        self.organization_id = organization.id
        self.api_key = api_key


async def get_current_organization(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> TenantContext:
    """
    Dependency to get and validate the current organization from API key.
    This enforces multi-tenancy by extracting organization context from the API key.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Query API key with organization
    result = await db.execute(
        select(APIKey)
        .where(APIKey.key == api_key)
        .where(APIKey.is_active == True)
    )
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Check if API key is expired
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Get organization
    org_result = await db.execute(
        select(Organization)
        .where(Organization.id == api_key_obj.organization_id)
        .where(Organization.is_active == True)
    )
    organization = org_result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is not active or does not exist"
        )

    # Update last used timestamp
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    # Store in request state for other middleware/dependencies
    request.state.tenant = TenantContext(organization, api_key_obj)

    return request.state.tenant


class TenantMiddleware:
    """
    Middleware class for tenant-related operations.
    Note: Main tenant resolution is done via dependency injection (get_current_organization).
    This middleware is for optional additional tenant-related processing.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Initialize tenant state
            if not hasattr(scope.get("state", {}), "tenant"):
                scope.setdefault("state", {})["tenant"] = None

        await self.app(scope, receive, send)


def require_organization_access(organization_id: UUID):
    """
    Dependency to verify the current tenant has access to the specified organization.
    Used for additional security checks.
    """
    async def check_access(tenant: TenantContext = Depends(get_current_organization)) -> TenantContext:
        if tenant.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this organization's resources"
            )
        return tenant

    return check_access
