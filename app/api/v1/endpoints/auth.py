from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, PasswordSetRequest
from app.schemas.user import UserResponse
from app.schemas.invitation import InvitationCreate, InvitationResponse
from security.rbac import require_role
from db.models.auth import UserRole

from app.api.deps import get_current_user # Need this import too!
from db.models.auth import User

router = APIRouter()

@router.post("/invitations", response_model=InvitationResponse)
async def create_invitation(
    invitation_data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create an invitation (Super Admin or Tenant Admin only).
    """
    # Enforce permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create invitations"
        )
    
    # Additional Tenant check: Tenant Admin can only invite to their own tenant
    if current_user.role == UserRole.TENANT_ADMIN:
        if str(invitation_data.tenant_id) != str(current_user.tenant_id):
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot invite users to a different tenant"
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
        
    return service.create_tokens(user_id=str(user.id), email=user.email, role=user.role.value)

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
    
    return service.create_tokens(user_id=str(user.id), email=user.email, role=user.role.value)

@router.post("/invitations/{token}/accept", response_model=UserResponse)
async def accept_invitation(
    token: str,
    password_data: PasswordSetRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService()
    user = await service.accept_invitation(db, token=token, password=password_data.password)
    return user
