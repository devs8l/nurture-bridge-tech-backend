from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.base import BaseRepository
from db.models.auth import User, UserRole, UserStatus
from app.schemas.auth import LoginRequest
from app.core.security import hash_password

class UserRepo(BaseRepository[User, LoginRequest, LoginRequest]): # LoginRequest is just minimal place holder
    """
    User Repository.
    Handles database operations for User model.
    """
    
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Get user by email.
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()

    async def create_from_invitation(
        self, 
        db: AsyncSession, 
        *, 
        email: str, 
        password: str,
        role: UserRole,
        tenant_id: UUID
    ) -> User:
        """
        Create a new user from an invitation.
        Hashes password automatically.
        """
        hashed_password = hash_password(password)
        
        db_user = User(
            email=email,
            password_hash=hashed_password,
            role=role,
            tenant_id=str(tenant_id), # UUID to str for DB if model expects str or UUID type depending on implementation
            status=UserStatus.ACTIVE
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
