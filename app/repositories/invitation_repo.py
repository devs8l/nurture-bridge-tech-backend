from typing import Optional
from datetime import datetime, timedelta
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_logging.logger import get_logger
from db.repositories.base import BaseRepository
from db.models.auth import Invitation, InvitationStatus, UserRole
from app.schemas.invitation import InvitationCreate
from config.settings import settings

logger = get_logger(__name__)

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
            department=obj_in.department,  # Add department field
            token=token,
            status=InvitationStatus.PENDING,
            expires_at=expires_at
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info("invitation_created_in_db", invitation_id=str(db_obj.id), email=db_obj.email)
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

    async def get_by_tenant_and_roles(
        self, 
        db: AsyncSession, 
        *, 
        tenant_id: str, 
        roles: list[UserRole]
    ) -> list[Invitation]:
        """
        Get all invitations for a tenant filtered by specific roles.
        """
        query = select(Invitation).where(
            Invitation.tenant_id == tenant_id,
            Invitation.role_to_assign.in_(roles)
        ).order_by(Invitation.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
