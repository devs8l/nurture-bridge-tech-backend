from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import jwt, JoseError

from app_logging.logger import get_logger
from app_logging.audit import audit_authentication, audit_authorization, audit_data_modification
from app_logging.id_hasher import hash_id, hash_email  # PHI protection
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.repositories.user_repo import UserRepo
from app.repositories.session_repo import SessionRepo
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
        self.session_repo = SessionRepo()

    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        """
        user = await self.user_repo.get_by_email(db, email=email)
        if not user:
            logger.warning("authentication_failed", reason="user_not_found", email_hash=hash_email(email))
            audit_authentication(
                actor=f"user:{email}",
                success=False,
                reason="user_not_found",
                email=email
            )
            return None
        
        if not verify_password(password, user.password_hash):
            logger.warning("authentication_failed", reason="invalid_password", email_hash=hash_email(email))
            audit_authentication(
                actor=f"user:{user.id}",
                success=False,
                reason="invalid_password",
                email=email
            )
            return None
        
        logger.info("user_authenticated", user_id_hash=hash_id(str(user.id)), email_hash=hash_email(email), role=user.role.value)
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
        DEPRECATED: Use create_session_and_tokens() instead for session management.
        """
        token_data = {"sub": user_id, "email": email, "role": role}

        access_token = create_access_token(data=token_data)
        # NOTE: This method is deprecated, cannot create refresh token without session_id
        # refresh_token = create_refresh_token(user_id=user_id, session_id="deprecated")

        # Assuming settings.ACCESS_TOKEN_EXPIRE_MINUTES exists and is an integer
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "name": name,
            "role": role,
            "tenant_id": tenant_id,
            "email": email
        }

    async def create_session_and_tokens(
        self,
        db: AsyncSession,
        user: User,
        device_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> tuple[str, str, str]:
        """
        Create session and token pair.
        
        Returns:
            Tuple of (access_token, refresh_token, session_id)
        """
        # Calculate expiry once to ensure JWT exp == DB expires_at
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Create new session (with placeholder hash)
        session = await self.session_repo.create_session(
            db=db,
            user_id=str(user.id),
            refresh_token_hash="placeholder",  # Will update after token generation
            device_id=device_id,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        # Generate tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.value})
        refresh_token = create_refresh_token(user_id=str(user.id), session_id=str(session.id))
        
        # Hash and store refresh token
        from app.core.security import hash_refresh_token
        session.refresh_token_hash = hash_refresh_token(refresh_token)
        await db.commit()
        await db.refresh(session)
        
        logger.info(
            "session_and_tokens_created",
            user_id_hash=hash_id(str(user.id)),
            session_id_hash=hash_id(str(session.id)),
            device_id=device_id
        )
        
        return access_token, refresh_token, str(session.id)

    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str,
        device_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> tuple[str, str, User]:
        """
        Refresh access token with session validation and rotation.
        
        Returns:
            Tuple of (new_access_token, new_refresh_token, user)
        
        Raises:
            HTTPException with specific error codes:
                - SESSION_REVOKED: Session has been revoked
                - TOKEN_EXPIRED: Session has expired
                - INVALID_TOKEN: Token validation failed
        """
        # Decode token
        from app.core.security import decode_refresh_token, hash_refresh_token
        user_id, session_id = decode_refresh_token(refresh_token)
        
        # Validate session exists and is active
        session = await self.session_repo.get_by_id(db, session_id)
        if not session:
            logger.warning("session_not_found", session_id_hash=hash_id(session_id))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_REVOKED", "message": "Session not found"}
            )
        
        if session.revoked_at:
            logger.warning(
                "session_already_revoked",
                session_id_hash=hash_id(session_id),
                reason=session.revoked_reason
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_REVOKED", "message": f"Session has been revoked: {session.revoked_reason}"}
            )
        
        if session.expires_at < datetime.utcnow():
            logger.warning("session_expired", session_id_hash=hash_id(session_id))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "TOKEN_EXPIRED", "message": "Session has expired"}
            )
        
        # Verify token hash matches
        token_hash = hash_refresh_token(refresh_token)
        if session.refresh_token_hash != token_hash:
            logger.error(
                "token_hash_mismatch",
                session_id_hash=hash_id(session_id),
                user_id_hash=hash_id(user_id)
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Token validation failed"}
            )
        
        # Fetch user
        user = await self.user_repo.get(db, id=user_id)
        if not user:
            logger.warning("user_not_found_for_refresh", user_id_hash=hash_id(user_id))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "User not found"}
            )
        
        # Rotate: Revoke old session and create new one
        await self.session_repo.revoke_session(db, session_id, reason="TOKEN_ROTATED")
        
        # Create new session and tokens
        access_token, new_refresh_token, new_session_id = await self.create_session_and_tokens(
            db, user, device_id, user_agent, ip_address
        )
        
        logger.info(
            "token_refreshed",
            user_id_hash=hash_id(user_id),
            old_session_id_hash=hash_id(session_id),
            new_session_id_hash=hash_id(new_session_id)
        )
        
        return access_token, new_refresh_token, user

    async def logout_session(self, db: AsyncSession, refresh_token: str) -> None:
        """
        Logout by revoking session.
        
        This is idempotent - if the token is already invalid, it silently succeeds.
        """
        try:
            from app.core.security import decode_refresh_token
            user_id, session_id = decode_refresh_token(refresh_token)
            await self.session_repo.revoke_session(db, session_id, reason="LOGOUT")
            logger.info("session_logged_out", session_id_hash=hash_id(session_id), user_id_hash=hash_id(user_id))
        except HTTPException:
            # Token already invalid, ignore
            logger.debug("logout_with_invalid_token")
            pass

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
            creator_user_id_hash=hash_id(creator_user_id),
            role=invitation_data.role.value,
            tenant_id_hash=hash_id(str(invitation_data.tenant_id))
        )
        invitation_repo = InvitationRepo()
        invitation = await invitation_repo.create(
            db, 
            obj_in=invitation_data, 
            invited_by_user_id=creator_user_id
        )
        logger.info("invitation_created", invitation_id_hash=hash_id(str(invitation.id)), email_hash=hash_email(invitation.email))
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
            
        # Parse name into first_name, last_name
        name_parts = name.strip().split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
            
        # Create User
        logger.info(
            "creating_user_from_invitation",
            email_hash=hash_email(invite.email),
            role=invite.role_to_assign.value,
            tenant_id_hash=hash_id(invite.tenant_id)
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
        
        if invite.role_to_assign == UserRole.HOD:
            # Validate department is present
            if not invite.department:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This invitation is missing department information. Please request a new invitation."
                )
            # Create HOD profile
            await clinical_service.create_hod_profile(
                db,
                user_id=str(user.id),
                tenant_id=invite.tenant_id,
                first_name=first_name,
                last_name=last_name,
                department=invite.department
            )
        
        elif invite.role_to_assign == UserRole.DOCTOR:
            # Validate department is present
            if not invite.department:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This invitation is missing department information. Please request a new invitation."
                )
            # Create doctor profile
            await clinical_service.create_doctor_profile(
                db,
                user_id=str(user.id),
                tenant_id=invite.tenant_id,
                first_name=first_name,
                last_name=last_name,
                department=invite.department,
                license_number=None  # Can be updated later via PATCH
            )
        
        elif invite.role_to_assign == UserRole.RECEPTIONIST:
            # Validate department is present
            if not invite.department:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This invitation is missing department information. Please request a new invitation."
                )
            # Create receptionist profile
            await clinical_service.create_receptionist_profile(
                db,
                user_id=str(user.id),
                tenant_id=invite.tenant_id,
                first_name=first_name,
                last_name=last_name,
                department=invite.department
            )
        
        elif invite.role_to_assign == UserRole.PARENT:
            # Create parent profile with assigned doctor
            # if not invite.doctor_id:
            #     raise HTTPException(
            #         status_code=status.HTTP_400_BAD_REQUEST,
            #         detail="Parent invitations must include assigned doctor"
            #     )
            
            await clinical_service.create_parent_profile(
                db,
                user_id=str(user.id),
                tenant_id=invite.tenant_id,
                first_name=first_name,
                last_name=last_name,
                assigned_doctor_id=invite.doctor_id
            )
        
        # Mark invitation as accepted
        await invitation_repo.mark_as_accepted(db, invitation=invite)
        logger.info(
            "invitation_accepted",
            user_id_hash=hash_id(str(user.id)),
            email_hash=hash_email(user.email),
            role=user.role.value
        )
        
        return user
