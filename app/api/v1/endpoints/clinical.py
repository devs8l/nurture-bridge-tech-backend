from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_logging.logger import get_logger
from app.api.deps import get_db, get_current_user
from app.services.clinical_service import ClinicalService
from app.schemas.clinical import (
    DoctorUpdate, DoctorResponse,
    HODUpdate, HODResponse,
    ReceptionistUpdate, ReceptionistResponse,
    ParentUpdate, ParentResponse,
    ChildCreate, ChildUpdate, ChildResponse
)
from db.models.auth import User, UserRole

logger = get_logger(__name__)
router = APIRouter()

# ============================================================================
# DOCTOR ENDPOINTS
# ============================================================================

@router.get("/doctors/me", response_model=DoctorResponse)
async def get_my_doctor_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current doctor's profile.
    Role: DOCTOR only.
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access this endpoint"
        )
    
    service = ClinicalService()
    doctor = await service.get_doctor_by_user_id(db, user_id=str(current_user.id))
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )
    
    return doctor

@router.patch("/doctors/me", response_model=DoctorResponse)
async def update_my_doctor_profile(
    update_data: DoctorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current doctor's profile.
    Role: DOCTOR only.
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access this endpoint"
        )
    
    service = ClinicalService()
    doctor = await service.get_doctor_by_user_id(db, user_id=str(current_user.id))
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )
    
    return await service.update_doctor(db, doctor_id=str(doctor.id), update_data=update_data)

@router.get("/doctors/me/parents", response_model=List[ParentResponse])
async def get_my_assigned_parents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all parents assigned to current doctor.
    Role: DOCTOR only.
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access this endpoint"
        )
    
    service = ClinicalService()
    doctor = await service.get_doctor_by_user_id(db, user_id=str(current_user.id))
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )
    
    return await service.get_doctor_assigned_parents(db, doctor_id=str(doctor.id))

@router.get("/doctors/me/children", response_model=List[ChildResponse])
async def get_my_assigned_children(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all children under current doctor's care.
    Role: DOCTOR only.
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access this endpoint"
        )
    
    service = ClinicalService()
    doctor = await service.get_doctor_by_user_id(db, user_id=str(current_user.id))
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )
    
    return await service.get_doctor_children(db, doctor_id=str(doctor.id))

# ============================================================================
# HOD ENDPOINTS
# ============================================================================

@router.get("/hods/me", response_model=HODResponse)
async def get_my_hod_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current HOD's profile.
    Role: HOD only.
    """
    if current_user.role != UserRole.HOD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HODs can access this endpoint"
        )
    
    service = ClinicalService()
    hod = await service.get_hod_by_user_id(db, user_id=str(current_user.id))
    
    if not hod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HOD profile not found"
        )
    
    return hod

@router.patch("/hods/me", response_model=HODResponse)
async def update_my_hod_profile(
    update_data: HODUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current HOD's profile.
    Role: HOD only.
    """
    if current_user.role != UserRole.HOD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HODs can access this endpoint"
        )
    
    service = ClinicalService()
    hod = await service.get_hod_by_user_id(db, user_id=str(current_user.id))
    
    if not hod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HOD profile not found"
        )
    
    return await service.update_hod(db, hod_id=str(hod.id), update_data=update_data)

# ============================================================================
# RECEPTIONIST ENDPOINTS
# ============================================================================

@router.get("/receptionists/me", response_model=ReceptionistResponse)
async def get_my_receptionist_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current receptionist's profile.
    Role: RECEPTIONIST only.
    """
    if current_user.role != UserRole.RECEPTIONIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only receptionists can access this endpoint"
        )
    
    service = ClinicalService()
    receptionist = await service.get_receptionist_by_user_id(db, user_id=str(current_user.id))
    
    if not receptionist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receptionist profile not found"
        )
    
    return receptionist

@router.patch("/receptionists/me", response_model=ReceptionistResponse)
async def update_my_receptionist_profile(
    update_data: ReceptionistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current receptionist's profile.
    Role: RECEPTIONIST only.
    """
    if current_user.role != UserRole.RECEPTIONIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only receptionists can access this endpoint"
        )
    
    service = ClinicalService()
    receptionist = await service.get_receptionist_by_user_id(db, user_id=str(current_user.id))
    
    if not receptionist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receptionist profile not found"
        )
    
    return await service.update_receptionist(db, receptionist_id=str(receptionist.id), update_data=update_data)

# ============================================================================
# PARENT ENDPOINTS
# ============================================================================

@router.get("/parents/me", response_model=ParentResponse)
async def get_my_parent_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current parent's profile.
    Role: PARENT only.
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    service = ClinicalService()
    parent = await service.get_parent_by_user_id(db, user_id=str(current_user.id))
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    return parent

@router.patch("/parents/me", response_model=ParentResponse)
async def update_my_parent_profile(
    update_data: ParentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current parent's profile (phone number only).
    Role: PARENT only.
    NOTE: assigned_doctor_id is IMMUTABLE.
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    service = ClinicalService()
    parent = await service.get_parent_by_user_id(db, user_id=str(current_user.id))
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    return await service.update_parent(db, parent_id=str(parent.id), update_data=update_data)

@router.get("/parents/me/children", response_model=List[ChildResponse])
async def get_my_children(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all children of current parent.
    Role: PARENT only.
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    service = ClinicalService()
    parent = await service.get_parent_by_user_id(db, user_id=str(current_user.id))
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    return await service.get_parent_children(db, parent_id=str(parent.id))

@router.post("/parents/me/children", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    child_data: ChildCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new child for current parent.
    Role: PARENT only.
    This is the ONLY clinical entity parents can create directly.
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    service = ClinicalService()
    parent = await service.get_parent_by_user_id(db, user_id=str(current_user.id))
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    return await service.create_child(
        db,
        child_data=child_data,
        parent_id=str(parent.id),
        tenant_id=str(current_user.tenant_id)
    )

@router.patch("/parents/me/children/{child_id}", response_model=ChildResponse)
async def update_my_child(
    child_id: str,
    update_data: ChildUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update child information.
    Role: PARENT only.
    Parents can only update their own children.
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )
    
    service = ClinicalService()
    parent = await service.get_parent_by_user_id(db, user_id=str(current_user.id))
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    return await service.update_child(
        db,
        child_id=child_id,
        parent_id=str(parent.id),
        update_data=update_data
    )

# ============================================================================
# ADMIN ENDPOINTS (Tenant Admin)
# ============================================================================

@router.get("/doctors", response_model=List[DoctorResponse])
async def list_doctors(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all doctors in tenant.
    Role: TENANT_ADMIN or SUPER_ADMIN.
    """
    if current_user.role not in [UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    service = ClinicalService()
    return await service.list_doctors_in_tenant(
        db,
        tenant_id=str(current_user.tenant_id),
        skip=skip,
        limit=limit
    )

@router.get("/parents", response_model=List[ParentResponse])
async def list_parents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all parents in tenant.
    Role: TENANT_ADMIN or RECEPTIONIST or HOD.
    """
    if current_user.role not in [UserRole.TENANT_ADMIN, UserRole.RECEPTIONIST, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospital staff can access this endpoint"
        )
    
    service = ClinicalService()
    return await service.list_parents_in_tenant(
        db,
        tenant_id=str(current_user.tenant_id),
        skip=skip,
        limit=limit
    )

@router.get("/children", response_model=List[ChildResponse])
async def list_children(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all children in tenant.
    Role: TENANT_ADMIN or HOD.
    """
    if current_user.role not in [UserRole.TENANT_ADMIN, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospital staff can access this endpoint"
        )
    
    service = ClinicalService()
    return await service.list_children_in_tenant(
        db,
        tenant_id=str(current_user.tenant_id),
        skip=skip,
        limit=limit
    )
