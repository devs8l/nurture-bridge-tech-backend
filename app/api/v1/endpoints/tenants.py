from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.services.tenant_service import TenantService
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from db.models.auth import User, UserRole
from security.rbac import require_role

router = APIRouter()

# Dependency for Super Admin access only
# We use the require_role dependency factory from security.rbac
require_super_admin = require_role("SUPER_ADMIN")

@router.get("/", response_model=List[TenantResponse], dependencies=[Depends(require_super_admin)])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user) # Implicitly checked by require_role
):
    """
    List all tenants.
    Restricted to SUPER_ADMIN.
    """
    service = TenantService()
    return await service.list_tenants(db, skip=skip, limit=limit)

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_super_admin)])
async def create_tenant(
    tenant_in: TenantCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new tenant.
    Restricted to SUPER_ADMIN.
    """
    service = TenantService()
    return await service.create_tenant(db, obj_in=tenant_in)

@router.get("/{tenant_id}", response_model=TenantResponse, dependencies=[Depends(require_super_admin)])
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific tenant by ID.
    Restricted to SUPER_ADMIN.
    """
    service = TenantService()
    return await service.get_tenant(db, tenant_id)

@router.patch("/{tenant_id}", response_model=TenantResponse, dependencies=[Depends(require_super_admin)])
async def update_tenant(
    tenant_id: UUID,
    tenant_in: TenantUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a tenant.
    Restricted to SUPER_ADMIN.
    """
    service = TenantService()
    return await service.update_tenant(db, tenant_id, obj_in=tenant_in)
