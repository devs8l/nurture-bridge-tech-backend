from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_logging.logger import get_logger
from app.repositories.clinical_repo import DoctorRepo, ParentRepo, ChildRepo
from app.schemas.clinical import (
    DoctorUpdate, DoctorResponse,
    ParentUpdate, ParentResponse,
    ChildCreate, ChildUpdate, ChildResponse
)
from db.models.clinical import Doctor, Parent, Child

logger = get_logger(__name__)

class ClinicalService:
    """
    Service layer for clinical entities.
    Enforces business rules and tenant isolation.
    """
    
    def __init__(self):
        self.doctor_repo = DoctorRepo()
        self.parent_repo = ParentRepo()
        self.child_repo = ChildRepo()
    
    # ========================================================================
    # DOCTOR METHODS
    # ========================================================================
    
    async def create_doctor_profile(
        self, 
        db: AsyncSession, 
        *, 
        user_id: str, 
        tenant_id: str,
        license_number: str = "",
        specialization: Optional[str] = None
    ) -> Doctor:
        """
        Create doctor profile during invitation acceptance.
        INTERNAL USE ONLY - called from auth_service.
        """
        logger.info(
            "creating_doctor_profile",
            user_id=user_id,
            tenant_id=tenant_id,
            has_license=bool(license_number)
        )
        doctor = Doctor(
            user_id=user_id,
            tenant_id=tenant_id,
            license_number=license_number,
            specialization=specialization
        )
        db.add(doctor)
        await db.commit()
        await db.refresh(doctor)
        logger.info("doctor_profile_created", doctor_id=str(doctor.id), user_id=user_id)
        return doctor
    
    async def get_doctor_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[Doctor]:
        """Get doctor profile by user ID."""
        return await self.doctor_repo.get_by_user_id(db, user_id=user_id)
    
    async def update_doctor(
        self, 
        db: AsyncSession, 
        *, 
        doctor_id: str, 
        update_data: DoctorUpdate
    ) -> Doctor:
        """Update doctor profile."""
        doctor = await self.doctor_repo.get(db, id=doctor_id)
        if not doctor:
            logger.warning("doctor_not_found", doctor_id=doctor_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found"
            )
        logger.info("updating_doctor_profile", doctor_id=doctor_id)
        return await self.doctor_repo.update(db, db_obj=doctor, obj_in=update_data)
    
    async def get_doctor_assigned_parents(
        self, 
        db: AsyncSession, 
        *, 
        doctor_id: str
    ) -> List[Parent]:
        """Get all parents assigned to this doctor."""
        return await self.doctor_repo.get_assigned_parents(db, doctor_id=doctor_id)
    
    async def get_doctor_children(
        self, 
        db: AsyncSession, 
        *, 
        doctor_id: str
    ) -> List[Child]:
        """Get all children under doctor's care."""
        return await self.child_repo.get_by_doctor(db, doctor_id=doctor_id)
    
    async def list_doctors_in_tenant(
        self, 
        db: AsyncSession, 
        *, 
        tenant_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Doctor]:
        """List all doctors in tenant (admin only)."""
        return await self.doctor_repo.get_by_tenant(
            db, 
            tenant_id=tenant_id, 
            skip=skip, 
            limit=limit
        )
    
    # ========================================================================
    # PARENT METHODS
    # ========================================================================
    
    async def create_parent_profile(
        self, 
        db: AsyncSession, 
        *, 
        user_id: str, 
        tenant_id: str,
        assigned_doctor_id: str,
        phone_number: Optional[str] = None
    ) -> Parent:
        """
        Create parent profile during invitation acceptance.
        INTERNAL USE ONLY - called from auth_service.
        """
        logger.info(
            "creating_parent_profile",
            user_id=user_id,
            tenant_id=tenant_id,
            assigned_doctor_id=assigned_doctor_id
        )
        parent = Parent(
            user_id=user_id,
            tenant_id=tenant_id,
            assigned_doctor_id=assigned_doctor_id,
            phone_number=phone_number
        )
        db.add(parent)
        await db.commit()
        await db.refresh(parent)
        logger.info("parent_profile_created", parent_id=str(parent.id), user_id=user_id)
        return parent
    
    async def get_parent_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[Parent]:
        """Get parent profile by user ID."""
        return await self.parent_repo.get_by_user_id(db, user_id=user_id)
    
    async def update_parent(
        self, 
        db: AsyncSession, 
        *, 
        parent_id: str, 
        update_data: ParentUpdate
    ) -> Parent:
        """Update parent profile (phone number only)."""
        parent = await self.parent_repo.get(db, id=parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent not found"
            )
        return await self.parent_repo.update(db, db_obj=parent, obj_in=update_data)
    
    async def get_parent_children(
        self, 
        db: AsyncSession, 
        *, 
        parent_id: str
    ) -> List[Child]:
        """Get all children of this parent."""
        return await self.parent_repo.get_children(db, parent_id=parent_id)
    
    async def list_parents_in_tenant(
        self, 
        db: AsyncSession, 
        *, 
        tenant_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Parent]:
        """List all parents in tenant (admin only)."""
        return await self.parent_repo.get_by_tenant(
            db, 
            tenant_id=tenant_id, 
            skip=skip, 
            limit=limit
        )
    
    # ========================================================================
    # CHILD METHODS
    # ========================================================================
    
    async def create_child(
        self, 
        db: AsyncSession, 
        *, 
        child_data: ChildCreate,
        parent_id: str,
        tenant_id: str
    ) -> Child:
        """
        Create a child for a parent.
        This is the ONLY clinical entity parents can create via API.
        """
        logger.info("creating_child", parent_id=parent_id, tenant_id=tenant_id)
        child = await self.child_repo.create(
            db, 
            obj_in=child_data, 
            parent_id=parent_id,
            tenant_id=tenant_id
        )
        logger.info("child_created", child_id=str(child.id), parent_id=parent_id)
        return child
    
    async def update_child(
        self, 
        db: AsyncSession, 
        *, 
        child_id: str,
        parent_id: str,  # For ownership verification
        update_data: ChildUpdate
    ) -> Child:
        """Update child information."""
        child = await self.child_repo.get(db, id=child_id)
        if not child:
            logger.warning("child_not_found", child_id=child_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Verify ownership
        if child.parent_id != parent_id:
            logger.warning(
                "unauthorized_child_update",
                child_id=child_id,
                parent_id=parent_id,
                actual_parent_id=child.parent_id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this child"
            )
        
        logger.info("updating_child", child_id=child_id, parent_id=parent_id)
        return await self.child_repo.update(db, db_obj=child, obj_in=update_data)
    
    async def get_child(self, db: AsyncSession, *, child_id: str) -> Optional[Child]:
        """Get child by ID."""
        return await self.child_repo.get(db, id=child_id)
    
    async def list_children_in_tenant(
        self, 
        db: AsyncSession, 
        *, 
        tenant_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Child]:
        """List all children in tenant (admin only)."""
        return await self.child_repo.get_by_tenant(
            db, 
            tenant_id=tenant_id, 
            skip=skip, 
            limit=limit
        )
