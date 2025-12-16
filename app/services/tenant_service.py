from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.tenant_repo import TenantRepo
from app.schemas.tenant import TenantCreate, TenantUpdate
from db.models.tenant import Tenant

class TenantService:
    """
    Service for managing Tenants.
    Enforces business rules like unique codes.
    """

    def __init__(self):
        self.repo = TenantRepo()

    async def get_tenant(self, db: AsyncSession, tenant_id: UUID) -> Optional[Tenant]:
        return await self.repo.get(db, tenant_id)

    async def list_tenants(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Tenant]:
        return await self.repo.get_multi(db, skip=skip, limit=limit)

    async def create_tenant(self, db: AsyncSession, obj_in: TenantCreate) -> Tenant:
        """
        Create a new tenant.
        Enforces unique code constraint.
        """
        # Check for existing code
        existing = await self.repo.get_by_code(db, code=obj_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant with code '{obj_in.code}' already exists."
            )
        
        return await self.repo.create(db, obj_in=obj_in)

    async def update_tenant(self, db: AsyncSession, tenant_id: UUID, obj_in: TenantUpdate) -> Tenant:
        """
        Update an existing tenant.
        """
        tenant = await self.repo.get(db, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return await self.repo.update(db, db_obj=tenant, obj_in=obj_in)
