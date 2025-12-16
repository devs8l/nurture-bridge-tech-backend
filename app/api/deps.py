from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import JoseError

from db.base import get_db
from app.core.security import decode_token
from app.repositories.user_repo import UserRepo
from db.models.auth import User

# This enables the "Authorize" button in Swagger UI to show a Username/Password form
# It points to the endpoint that generates tokens.
security = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/access-token")

async def get_current_user(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    Validates JWT and checks if user exists in DB.
    """
    try:
        # OAuth2PasswordBearer returns the token string directly
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        
    repo = UserRepo()
    # Assuming get_by_email or get (by ID). The payload 'sub' is usually ID.
    # Our create_access_token used 'sub': user_id. 
    # But UserRepo only has get_by_email and generic get(id).
    user = await repo.get(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
        
    return user
