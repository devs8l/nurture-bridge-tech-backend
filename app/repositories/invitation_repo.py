from typing import Optional
from datetime import datetime, timedelta
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.base import BaseRepository
from db.models.auth import Invitation, InvitationStatus, UserRole
from app.schemas.invitation import InvitationCreate
from config.settings import settings

class InvitationRepo(BaseRepository[Invitation, InvitationCreate, InvitationCreate]):
    """
    Invitation Repository.
    Handles creation and retrieval of invitations.
    """
    
    def __init__(self):
        super().__init__(Invitation)

    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: InvitationCreate, 
        invited_by_user_id: str
    ) -> Invitation:
        """
        Create a new invitation.
        Generates a secure token and sets expiration.
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Set expiration (default 7 days)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        db_obj = Invitation(
            email=obj_in.email,
            role_to_assign=obj_in.role,
            invited_by_user_id=invited_by_user_id,
            tenant_id=str(obj_in.tenant_id),
            doctor_id=str(obj_in.doctor_id) if obj_in.doctor_id else None,
            token=token,
            status=InvitationStatus.PENDING,
            expires_at=expires_at
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_token(self, db: AsyncSession, *, token: str) -> Optional[Invitation]:
        """
        Get invitation by token.
        """
        query = select(Invitation).where(Invitation.token == token)
        result = await db.execute(query)
        return result.scalars().first()

    async def mark_as_accepted(self, db: AsyncSession, *, invitation: Invitation) -> Invitation:
        """
        Mark invitation as accepted.
        """
        invitation.status = InvitationStatus.ACCEPTED
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
        return invitation
