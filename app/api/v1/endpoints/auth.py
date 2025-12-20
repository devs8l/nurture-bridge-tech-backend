from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app_logging.logger import get_logger
from app.api.deps import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, PasswordSetRequest
from app.schemas.user import UserResponse
from app.schemas.invitation import InvitationCreate, InvitationResponse
from security.rbac import require_role
from db.models.auth import UserRole

from app.api.deps import get_current_user # Need this import too!
from db.models.auth import User

logger = get_logger(__name__)
router = APIRouter()

@router.post("/invitations", response_model=InvitationResponse)
async def create_invitation(
    invitation_data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create an invitation.
    
    Permission Rules:
    - SUPER_ADMIN → can invite TENANT_ADMIN only
    - TENANT_ADMIN (Hospital IT Admin) → can invite HOD, DOCTOR, RECEPTIONIST only
    - RECEPTIONIST → can invite PARENT only
    - Others → cannot create invitations
    """
    # Enforce role-based permissions
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super Admin can only invite Tenant Admins
        if invitation_data.role != UserRole.TENANT_ADMIN:
            logger.warning(
                "unauthorized_invitation_attempt",
                user_id=str(current_user.id),
                user_role=current_user.role.value,
                attempted_role=invitation_data.role.value,
                reason="super_admin_can_only_invite_tenant_admin"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super Admin can only invite Tenant Admins"
            )
    
    elif current_user.role == UserRole.TENANT_ADMIN:
        # Tenant Admin can invite HOD, Doctor, Receptionist
        if invitation_data.role not in [UserRole.HOD, UserRole.DOCTOR, UserRole.RECEPTIONIST]:
            logger.warning(
                "unauthorized_invitation_attempt",
                user_id=str(current_user.id),
                user_role=current_user.role.value,
                attempted_role=invitation_data.role.value,
                reason="tenant_admin_can_only_invite_staff"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant Admin can only invite HOD, Doctor, or Receptionist"
            )
        
        # Validate department is provided for staff roles
        if not invitation_data.department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department is required for staff role invitations"
            )
        
        # Must be for their own tenant
        if str(invitation_data.tenant_id) != str(current_user.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot invite users to a different tenant"
            )
    
    elif current_user.role == UserRole.RECEPTIONIST:
        # Receptionist can only invite Parents
        if invitation_data.role != UserRole.PARENT:
            logger.warning(
                "unauthorized_invitation_attempt",
                user_id=str(current_user.id),
                user_role=current_user.role.value,
                attempted_role=invitation_data.role.value,
                reason="receptionist_can_only_invite_parents"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Receptionist can only invite Parents"
            )
        
        # Must be for their own tenant
        if str(invitation_data.tenant_id) != str(current_user.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot invite users to a different tenant"
            )
        
        # Validate doctor_id is provided for parent invitations
        # if not invitation_data.doctor_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Doctor assignment is required for Parent invitations"
        #     )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create invitations"
        )

    service = AuthService()
    return await service.create_invitation(
        db, 
        creator_user_id=str(current_user.id), 
        invitation_data=invitation_data
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login for API Clients (JSON).
    """
    service = AuthService()
    user = await service.authenticate_user(db, email=login_data.email, password=login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    return service.create_tokens(user_id=str(user.id), email=user.email, role=user.role.value, name=user.name, tenant_id=str(user.tenant_id) if user.tenant_id else None)

@router.post("/access-token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login for Swagger UI (Form Data).
    Compatible with OAuth2PasswordBearer.
    """
    service = AuthService()
    # OAuth2 spec says 'username', but we use 'email'
    user = await service.authenticate_user(db, email=form_data.username, password=form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return service.create_tokens(user_id=str(user.id), email=user.email, role=user.role.value, name=user.name, tenant_id=str(user.tenant_id) if user.tenant_id else None)

@router.post("/invitations/{token}/accept", response_model=UserResponse)
async def accept_invitation(
    token: str,
    password_data: PasswordSetRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService()
    user = await service.accept_invitation(db, token=token, name=password_data.name, password=password_data.password)
    return user
