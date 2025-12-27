from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app_logging.logger import get_logger
from db.repositories.base import BaseRepository
from db.models.clinical import Doctor, Parent, Child, HOD, Receptionist
from app.schemas.clinical import DoctorUpdate, ParentUpdate, ChildCreate, ChildUpdate, HODUpdate, ReceptionistUpdate

logger = get_logger(__name__)

# ============================================================================
# DOCTOR REPOSITORY
# ============================================================================

class DoctorRepo(BaseRepository[Doctor, DoctorUpdate, DoctorUpdate]):
    """
    Repository for Doctor entity.
    NOTE: No create method - doctors are created via invitation acceptance only.
    """
    
    def __init__(self):
        super().__init__(Doctor)
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[Doctor]:
        """Get doctor by their user account ID."""
        query = select(Doctor).where(Doctor.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_tenant(self, db: AsyncSession, *, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Doctor]:
        """Get all doctors in a tenant."""
        query = (
            select(Doctor)
            .where(Doctor.tenant_id == tenant_id)
            .where(Doctor.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_assigned_parents(self, db: AsyncSession, *, doctor_id: str) -> List[Parent]:
        """Get all parents assigned to this doctor."""
        query = (
            select(Parent)
            .options(selectinload(Parent.user))
            .where(Parent.assigned_doctor_id == doctor_id)
            .where(Parent.is_deleted == False)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

# ============================================================================
# HOD REPOSITORY
# ============================================================================

class HODRepo(BaseRepository[HOD, HODUpdate, HODUpdate]):
    """
    Repository for HOD (Head of Department) entity.
    NOTE: No create method - HODs are created via invitation acceptance only.
    """
    
    def __init__(self):
        super().__init__(HOD)
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[HOD]:
        """Get HOD by their user account ID."""
        query = select(HOD).where(HOD.user_id == user_id, HOD.deleted_at.is_(None))
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_department(self, db: AsyncSession, *, tenant_id: str, department: str) -> List[HOD]:
        """Get all HODs in a specific department within a tenant."""
        query = (
            select(HOD)
            .where(HOD.tenant_id == tenant_id)
            .where(HOD.department == department)
            .where(HOD.deleted_at.is_(None))
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_tenant(self, db: AsyncSession, *, tenant_id: str, skip: int = 0, limit: int = 100) -> List[HOD]:
        """Get all HODs in a tenant."""
        query = (
            select(HOD)
            .where(HOD.tenant_id == tenant_id)
            .where(HOD.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

# ============================================================================
# RECEPTIONIST REPOSITORY
# ============================================================================

class ReceptionistRepo(BaseRepository[Receptionist, ReceptionistUpdate, ReceptionistUpdate]):
    """
    Repository for Receptionist entity.
    NOTE: No create method - Receptionists are created via invitation acceptance only.
    """
    
    def __init__(self):
        super().__init__(Receptionist)
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[Receptionist]:
        """Get receptionist by their user account ID."""
        query = select(Receptionist).where(Receptionist.user_id == user_id, Receptionist.deleted_at.is_(None))
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_department(self, db: AsyncSession, *, tenant_id: str, department: str) -> List[Receptionist]:
        """Get all receptionists in a specific department within a tenant."""
        query = (
            select(Receptionist)
            .where(Receptionist.tenant_id == tenant_id)
            .where(Receptionist.department == department)
            .where(Receptionist.deleted_at.is_(None))
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_tenant(self, db: AsyncSession, *, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Receptionist]:
        """Get all receptionists in a tenant."""
        query = (
            select(Receptionist)
            .where(Receptionist.tenant_id == tenant_id)
            .where(Receptionist.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

# ============================================================================
# PARENT REPOSITORY
# ============================================================================

class ParentRepo(BaseRepository[Parent, ParentUpdate, ParentUpdate]):
    """
    Repository for Parent entity.
    NOTE: No create method - parents are created via invitation acceptance only.
    """
    
    def __init__(self):
        super().__init__(Parent)
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[Parent]:
        """Get parent by their user account ID."""
        query = select(Parent).options(selectinload(Parent.user)).where(Parent.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_doctor(self, db: AsyncSession, *, doctor_id: str, skip: int = 0, limit: int = 100) -> List[Parent]:
        """Get all parents assigned to a specific doctor."""
        query = (
            select(Parent)
            .options(selectinload(Parent.user), selectinload(Parent.children))
            .where(Parent.assigned_doctor_id == doctor_id)
            .where(Parent.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_tenant(self, db: AsyncSession, *, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Parent]:
        """Get all parents in a tenant."""
        query = (
            select(Parent)
            .options(selectinload(Parent.user), selectinload(Parent.children))
            .where(Parent.tenant_id == tenant_id)
            .where(Parent.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_children(self, db: AsyncSession, *, parent_id: str) -> List[Child]:
        """Get all children of this parent."""
        query = (
            select(Child)
            .where(Child.parent_id == parent_id)
            .where(Child.is_deleted == False)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

# ============================================================================
# CHILD REPOSITORY
# ============================================================================

class ChildRepo(BaseRepository[Child, ChildCreate, ChildUpdate]):
    """
    Repository for Child entity.
    Children CAN be created via API by parents.
    """
    
    def __init__(self):
        super().__init__(Child)
    
    async def create(self, db: AsyncSession, *, obj_in: ChildCreate, parent_id: str, tenant_id: str) -> Child:
        """
        Create a child for a parent.
        Automatically sets parent_id and tenant_id.
        """
        db_obj = Child(
            parent_id=parent_id,
            tenant_id=tenant_id,
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            date_of_birth=obj_in.date_of_birth,
            gender=obj_in.gender
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_by_parent(self, db: AsyncSession, *, parent_id: str) -> List[Child]:
        """Get all children of a parent."""
        query = (
            select(Child)
            .where(Child.parent_id == parent_id)
            .where(Child.is_deleted == False)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_tenant(self, db: AsyncSession, *, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Child]:
        """Get all children in a tenant (admin view)."""
        query = (
            select(Child)
            .where(Child.tenant_id == tenant_id)
            .where(Child.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_doctor(self, db: AsyncSession, *, doctor_id: str) -> List[Child]:
        """
        Get all children under a doctor's care.
        Returns children of all parents assigned to this doctor.
        """
        query = (
            select(Child)
            .join(Parent, Child.parent_id == Parent.id)
            .where(Parent.assigned_doctor_id == doctor_id)
            .where(Child.is_deleted == False)
            .where(Parent.is_deleted == False)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
