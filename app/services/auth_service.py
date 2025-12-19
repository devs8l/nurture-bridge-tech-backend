from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import jwt, JoseError

from app_logging.logger import get_logger
from app_logging.audit import audit_authentication, audit_authorization, audit_data_modification
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.repositories.user_repo import UserRepo
from app.repositories.invitation_repo import InvitationRepo
from app.schemas.invitation import InvitationCreate
from db.models.auth import User
from config.settings import settings

logger = get_logger(__name__)

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
            logger.warning("authentication_failed", reason="user_not_found", email=email)
            audit_authentication(
                actor=f"user:{email}",
                success=False,
                reason="user_not_found",
                email=email
            )
            return None
        
        if not verify_password(password, user.password_hash):
            logger.warning("authentication_failed", reason="invalid_password", email=email)
            audit_authentication(
                actor=f"user:{user.id}",
                success=False,
                reason="invalid_password",
                email=email
            )
            return None
        
        logger.info("user_authenticated", user_id=str(user.id), email=email, role=user.role.value)
        audit_authentication(
            actor=f"user:{user.id}",
            success=True,
            email=email,
            role=user.role.value
        )
        return user

    def create_tokens(self, user_id: str, email: str, role: str, name: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate access and refresh tokens for the user.
        """
        token_data = {"sub": user_id, "email": email, "role": role}

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(user_id=user_id)

        # Assuming settings.ACCESS_TOKEN_EXPIRE_MINUTES exists and is an integer
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "name": name,
            "role": role,
            "tenant_id": tenant_id,
            "email": email
        }

    async def create_invitation(
        self, 
        db: AsyncSession, 
        creator_user_id: str,
        invitation_data: Any # schema: InvitationCreate
    ) -> Any: # model: Invitation
        """
        Create a new invitation.
        """
        logger.info(
            "creating_invitation",
            creator_user_id=creator_user_id,
            role=invitation_data.role.value,
            tenant_id=str(invitation_data.tenant_id)
        )
        invitation_repo = InvitationRepo()
        invitation = await invitation_repo.create(
            db, 
            obj_in=invitation_data, 
            invited_by_user_id=creator_user_id
        )
        logger.info("invitation_created", invitation_id=str(invitation.id), email=invitation.email)
        return invitation

    async def accept_invitation(self, db: AsyncSession, token: str, name: str, password: str) -> User:
        """
        Accept an invitation.
        Validates token, checks expiration, creates user, marks invitation as accepted.
        """
        logger.info("accepting_invitation", token_prefix=token[:8] + "...")
        # Validate name is provided
        if not name or not name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name is required"
            )
        invitation_repo = InvitationRepo()
        invite = await invitation_repo.get_by_token(db, token=token)
        
        if not invite:
            logger.warning("invitation_not_found", token_prefix=token[:8] + "...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid invitation token"
            )
            
        if invite.status != "PENDING":
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation already accepted or expired"
            )

        if invite.expires_at < datetime.utcnow():
             invite.status = "EXPIRED" # Update status if possible, or just fail
             await db.commit()
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation expired"
            )

        # check if email already registered
        existing_user = await self.user_repo.get_by_email(db, email=invite.email)
        if existing_user:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
            
        # Create User
        logger.info(
            "creating_user_from_invitation",
            email=invite.email,
            role=invite.role_to_assign.value,
            tenant_id=invite.tenant_id
        )
        user = await self.user_repo.create_from_invitation(
            db,
            email=invite.email,
            name=name,
            password=password,
            role=invite.role_to_assign,
            tenant_id=invite.tenant_id
        )
        
        # Auto-create clinical profiles based on role
        from app.services.clinical_service import ClinicalService
        from db.models.auth import UserRole
        
        clinical_service = ClinicalService()
        
        if invite.role_to_assign == UserRole.DOCTOR:
            # Create doctor profile
            await clinical_service.create_doctor_profile(
                db,
                user_id=str(user.id),
                tenant_id=invite.tenant_id,
                name=name,
                license_number=""  # Can be updated later via PATCH
            )
        
        elif invite.role_to_assign == UserRole.PARENT:
            # Create parent profile with assigned doctor
            if not invite.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent invitations must include assigned doctor"
                )
            
            await clinical_service.create_parent_profile(
                db,
                user_id=str(user.id),
                tenant_id=invite.tenant_id,
                name=name,
                assigned_doctor_id=invite.doctor_id
            )
        
        # Mark invitation as accepted
        await invitation_repo.mark_as_accepted(db, invitation=invite)
        logger.info(
            "invitation_accepted",
            user_id=str(user.id),
            email=user.email,
            role=user.role.value
        )
        
        return user
