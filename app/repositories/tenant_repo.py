from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.tenant import TenantCreate, TenantUpdate
from db.models.tenant import Tenant
from db.repositories.base import BaseRepository

class TenantRepo(BaseRepository[Tenant, TenantCreate, TenantUpdate]):
    """
    Repository for Tenant operations.
    Inherits standard CRUD from BaseRepository.
    """
    
    def __init__(self):
        super().__init__(Tenant)

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Tenant]:
        """
        Get a tenant by its unique code.
        """
        query = select(self.model).where(self.model.code == code)
        result = await db.execute(query)
        return result.scalars().first()
