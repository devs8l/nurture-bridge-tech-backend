from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import jwt, JoseError

from app.core.security import verify_password, create_access_token, create_refresh_token
from app.repositories.user_repo import UserRepo
from db.models.auth import User
from config.settings import settings

class AuthService:
    """
    Authentication Service.
    Handles business logic for login and user management.
    """
    
    def __init__(self):
        self.user_repo = UserRepo()

    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        """
        user = await self.user_repo.get_by_email(db, email=email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
            
        return user

    async def accept_invitation(self, db: AsyncSession, token: str, password: str) -> User:
        """
        Accept an invitation.
        TODO: Implement InvitationRepo to validate token properly.
        For now, we will decode the token (if it's a JWT) or mock it.
        """
        # TEMP: Mock logic to allow development without Invitation implementation yet.
        # In real implementation:
        # invite = await self.invitation_repo.get_by_token(token)
        # if not invite or invite.expired: fail
        
        # For now, we assume the token is a dummy token containing email+role+tenant
        # Or we just fail for now if we don't have invitation logic.
        
        # Since the user requested "Verification Checklist -> Mock Invitation Acceptance":
        # We will assume the token is valid for now and just create a dummy user
        # OR better, fail if not implemented.
        # But wait, user said "Mock Logic".
        
        # Let's verify if the token is a JWT we signed for the invite?
        # Assuming we don't have the Invite repo yet, we can't create a real user linked to a real tenant without data.
        
        # I will leave this as a placeholder raising NotImplementedError or a simple Mock
        # that looks for a specifically formatted token string for testing.
        
        if token.startswith("mock-token:"):
            # Format: mock-token:email:role:tenant_id
            parts = token.split(":")
            if len(parts) == 4:
                email = parts[1]
                role = parts[2]
                tenant_id = parts[3]
                
                # Check if user already exists
                existing = await self.user_repo.get_by_email(db, email=email)
                if existing:
                     raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User already exists"
                    )

                return await self.user_repo.create_from_invitation(
                    db,
                    email=email,
                    password=password,
                    role=role,
                    tenant_id=tenant_id
                )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token"
        )
