from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app_logging.logger import get_logger
from app_logging.id_hasher import hash_id
from config.settings import settings
from app.api.deps import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, PasswordSetRequest, RefreshTokenRequest
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
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Login for API Clients (JSON).
    Creates session and sets refresh token in HttpOnly cookie.
    """
    service = AuthService()
    user = await service.authenticate_user(db, email=login_data.email, password=login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # CRITICAL: Require device_id
    device_id = request.headers.get("X-Device-ID")
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-ID header is required"
        )
    
    user_agent = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None
    
    # Create session and tokens
    access_token, refresh_token, session_id = await service.create_session_and_tokens(
        db=db,
        user=user,
        device_id=device_id,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    # Set refresh token cookie
    from app.core.security import set_refresh_token_cookie
    set_refresh_token_cookie(response, refresh_token)
    
    # Build response (without refresh_token in JSON)
    token_response = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "name": user.name,
        "role": user.role.value,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "email": user.email
    }
    
    # For parents, check if they have created any children
    if user.role == UserRole.PARENT:
        from app.repositories.clinical_repo import ParentRepo
        parent_repo = ParentRepo()
        parent = await parent_repo.get_by_user_id(db, user_id=str(user.id))
        
        if parent:
            # Check if parent has any children and get the first child's ID
            from sqlalchemy import select
            from db.models.clinical import Child
            stmt = select(Child).where(Child.parent_id == parent.id).limit(1)
            result = await db.execute(stmt)
            child = result.scalar_one_or_none()
            token_response["isChildCreated"] = str(child.id) if child else None
        else:
            token_response["isChildCreated"] = None
    
    return token_response

@router.post("/access-token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    response: Response = None,
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
    
    # CRITICAL: Require device_id
    device_id = request.headers.get("X-Device-ID") if request else None
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-ID header is required"
        )
    
    user_agent = request.headers.get("User-Agent") if request else None
    ip_address = request.client.host if request and request.client else None
    
    # Create session and tokens
    access_token, refresh_token, session_id = await service.create_session_and_tokens(
        db=db,
        user=user,
        device_id=device_id,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    # Set refresh token cookie
    from app.core.security import set_refresh_token_cookie
    if response:
        set_refresh_token_cookie(response, refresh_token)
    
    # Build response
    token_response = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "name": user.name,
        "role": user.role.value,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "email": user.email
    }
    
    # For parents, check if they have created any children
    if user.role == UserRole.PARENT:
        from app.repositories.clinical_repo import ParentRepo
        parent_repo = ParentRepo()
        parent = await parent_repo.get_by_user_id(db, user_id=str(user.id))
        
        if parent:
            # Check if parent has any children and get the first child's ID
            from sqlalchemy import select
            from db.models.clinical import Child
            stmt = select(Child).where(Child.parent_id == parent.id).limit(1)
            result = await db.execute(stmt)
            child = result.scalar_one_or_none()
            token_response["isChildCreated"] = str(child.id) if child else None
        else:
            token_response["isChildCreated"] = None
    
    return token_response

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None)
):
    """
    Refresh access token using refresh token from HttpOnly cookie.
    Returns a new access token and rotates the refresh token.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Refresh token missing"}
        )
    
    service = AuthService()
    
    # CRITICAL: Require device_id
    device_id = request.headers.get("X-Device-ID")
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-ID header is required"
        )
    
    user_agent = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None
    
    # Refresh with session validation and rotation
    access_token, new_refresh_token, user = await service.refresh_access_token(
        db=db,
        refresh_token=refresh_token,
        device_id=device_id,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    # Set new refresh token cookie
    from app.core.security import set_refresh_token_cookie
    set_refresh_token_cookie(response, new_refresh_token)
    
    # Build response
    token_response = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "name": user.name,
        "role": user.role.value,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "email": user.email
    }
    
    # For parents, check if they have created any children
    if user.role == UserRole.PARENT:
        from app.repositories.clinical_repo import ParentRepo
        parent_repo = ParentRepo()
        parent = await parent_repo.get_by_user_id(db, user_id=str(user.id))
        
        if parent:
            # Check if parent has any children and get the first child's ID
            from sqlalchemy import select
            from db.models.clinical import Child
            stmt = select(Child).where(Child.parent_id == parent.id).limit(1)
            result = await db.execute(stmt)
            child = result.scalar_one_or_none()
            token_response["isChildCreated"] = str(child.id) if child else None
        else:
            token_response["isChildCreated"] = None
    
    return token_response

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None)
):
    """
    Logout by revoking session and clearing refresh token cookie.
    Idempotent - succeeds even if token is already invalid.
    """
    # IDEMPOTENT: Always clear cookie even if DB operation fails
    from app.core.security import clear_refresh_token_cookie
    clear_refresh_token_cookie(response)
    
    # Best-effort revocation (ignore errors)
    if refresh_token:
        try:
            service = AuthService()
            await service.logout_session(db, refresh_token)
        except Exception as e:
            # Log but don't fail - cookie already cleared
            logger.warning("logout_session_failed", error=str(e))
    
    return None

@router.post("/invitations/{token}/accept", response_model=UserResponse)
async def accept_invitation(
    token: str,
    password_data: PasswordSetRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService()
    user = await service.accept_invitation(db, token=token, name=password_data.name, password=password_data.password)
    return user
