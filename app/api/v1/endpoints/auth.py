from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, PasswordSetRequest
from app.schemas.user import UserResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    Returns access and refresh tokens.
    """
    service = AuthService()
    user = await service.authenticate_user(db, email=login_data.email, password=login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Import here to avoid circular dependency if possible, or move create_token_pair to service
    from app.core.security import create_access_token, create_refresh_token
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "roles": [user.role]}
    )
    refresh_token = create_refresh_token(user_id=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60 # 30 mins default
    )

@router.post("/invitations/{token}/accept", response_model=UserResponse)
async def accept_invitation(
    token: str,
    password_data: PasswordSetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept an invitation to join.
    Sets the password and creates the user.
    """
    service = AuthService()
    user = await service.accept_invitation(db, token=token, password=password_data.password)
    return user
