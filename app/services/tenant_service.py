from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_logging.logger import get_logger
from app.repositories.tenant_repo import TenantRepo
from app.schemas.tenant import TenantCreate, TenantUpdate
from db.models.tenant import Tenant

logger = get_logger(__name__)

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
            logger.warning("tenant_code_conflict", code=obj_in.code)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant with code '{obj_in.code}' already exists."
            )
        
        logger.info("creating_tenant", code=obj_in.code, name=obj_in.name)
        tenant = await self.repo.create(db, obj_in=obj_in)
        logger.info("tenant_created", tenant_id=str(tenant.id), code=tenant.code)
        return tenant

    async def update_tenant(self, db: AsyncSession, tenant_id: UUID, obj_in: TenantUpdate) -> Tenant:
        """
        Update an existing tenant.
        """
        tenant = await self.repo.get(db, tenant_id)
        if not tenant:
            logger.warning("tenant_not_found", tenant_id=str(tenant_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        logger.info("updating_tenant", tenant_id=str(tenant_id))
        return await self.repo.update(db, db_obj=tenant, obj_in=obj_in)
