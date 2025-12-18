from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import jwt, JoseError

from app.core.security import verify_password, create_access_token, create_refresh_token
from app.repositories.user_repo import UserRepo
from app.repositories.invitation_repo import InvitationRepo
from app.schemas.invitation import InvitationCreate
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
        
        if not verify_password(password, user.password_hash):
            return None
            
        return user

    def create_tokens(self, user_id: str, email: str, role: str) -> Dict[str, Any]:
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
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    async def create_invitation(
        self, 
        db: AsyncSession, 
        creator_user_id: str,
        invitation_data: Any # schema: InvitationCreate
    ) -> Any: # model: Invitation
        """
        Create a new invitation and send email.
        """
        invitation_repo = InvitationRepo()
        invitation = await invitation_repo.create(
            db, 
            obj_in=invitation_data, 
            invited_by_user_id=creator_user_id
        )
        
        # Send invitation email
        from app.services.email_service import EmailService
        from app.repositories.tenant_repo import TenantRepo
        
        email_service = EmailService()
        
        # Get tenant name for email
        tenant_repo = TenantRepo()
        tenant = await tenant_repo.get(db, id=str(invitation.tenant_id))
        tenant_name = tenant.name if tenant else None
        
        # Send email (non-blocking, errors logged but don't fail the request)
        try:
            await email_service.send_invitation_email(
                to_email=invitation.email,
                token=invitation.token,
                role=invitation.role_to_assign.value,
                tenant_name=tenant_name
            )
        except Exception as e:
            # Log error but don't fail the invitation creation
            import structlog
            logger = structlog.get_logger(__name__)
            logger.error("failed_to_send_invitation_email", error=str(e), email=invitation.email)
        
        return invitation

    async def accept_invitation(self, db: AsyncSession, token: str, password: str) -> User:
        """
        Accept an invitation.
        Validates token, checks expiration, creates user, marks invitation as accepted.
        """
        invitation_repo = InvitationRepo()
        invite = await invitation_repo.get_by_token(db, token=token)
        
        if not invite:
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
        user = await self.user_repo.create_from_invitation(
            db,
            email=invite.email,
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
                assigned_doctor_id=invite.doctor_id
            )
        
        # Mark invitation as accepted
        await invitation_repo.mark_as_accepted(db, invitation=invite)
        
        return user
