"""
Session Repository
Handles database operations for user sessions and refresh token management.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from db.models.auth import Session
from app_logging.logger import get_logger
from app_logging.id_hasher import hash_id

logger = get_logger(__name__)


class SessionRepo:
    """Repository for session management operations."""
    
    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        refresh_token_hash: str,
        device_id: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Session:
        """
        Create a new session.
        
        If a session already exists for this user+device, the old one is DELETED.
        This enforces the one-session-per-device constraint.
        """
        # First, check if session exists for this user+device
        existing_session = await self.get_by_user_and_device(db, user_id, device_id)
        
        if existing_session:
            logger.info(
                "deleting_existing_session_for_device",
                user_id_hash=hash_id(user_id),
                device_id=device_id,
                old_session_id=hash_id(str(existing_session.id))
            )
            # DELETE instead of revoke to avoid unique constraint violation
            await db.delete(existing_session)
            await db.flush()
        
        # Create new session
        session = Session(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            device_id=device_id,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        db.add(session)
        
        try:
            await db.flush()  # Use flush instead of commit - let endpoint manage transaction
            await db.refresh(session)
            logger.info(
                "session_created",
                session_id_hash=hash_id(str(session.id)),
                user_id_hash=hash_id(user_id),
                device_id=device_id
            )
            return session
        except IntegrityError as e:
            logger.error("session_creation_failed", error=str(e), user_id_hash=hash_id(user_id))
            raise
    
    async def get_by_id(self, db: AsyncSession, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_refresh_token_hash(
        self, 
        db: AsyncSession, 
        token_hash: str
    ) -> Optional[Session]:
        """Get session by refresh token hash. Used during token refresh validation."""
        stmt = select(Session).where(Session.refresh_token_hash == token_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_user_and_device(
        self,
        db: AsyncSession,
        user_id: str,
        device_id: str
    ) -> Optional[Session]:
        """Get session for a specific user and device."""
        stmt = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.device_id == device_id
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def revoke_session(
        self, 
        db: AsyncSession, 
        session_id: str, 
        reason: str = "LOGOUT"
    ) -> Optional[Session]:
        """
        Revoke a session by setting revoked_at timestamp.
        
        Args:
            session_id: UUID of the session
            reason: Reason for revocation (LOGOUT, TOKEN_ROTATED, NEW_LOGIN, etc.)
        
        Returns:
            The revoked session, or None if not found
        """
        session = await self.get_by_id(db, session_id)
        
        if not session:
            logger.warning("session_not_found_for_revocation", session_id_hash=hash_id(session_id))
            return None
        
        # Only revoke if not already revoked
        if not session.revoked_at:
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = reason
            
            await db.flush()  # Use flush instead of commit
            await db.refresh(session)
            
            logger.info(
                "session_revoked",
                session_id_hash=hash_id(session_id),
                reason=reason
            )
        
        return session
    
    async def revoke_by_user_and_device(
        self,
        db: AsyncSession,
        user_id: str,
        device_id: str,
        reason: str = "NEW_LOGIN"
    ) -> None:
        """
        Revoke session for a specific user and device.
        Used when creating a new session for the same device.
        """
        session = await self.get_by_user_and_device(db, user_id, device_id)
        
        if session and not session.revoked_at:
            await self.revoke_session(db, str(session.id), reason=reason)
    
    async def revoke_all_for_user(
        self,
        db: AsyncSession,
        user_id: str,
        reason: str = "LOGOUT_ALL"
    ) -> int:
        """
        Revoke all active sessions for a user.
        Returns the number of sessions revoked.
        """
        # Get all active sessions
        stmt = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.revoked_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        count = 0
        for session in sessions:
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = reason
            count += 1
        
        if count > 0:
            await db.commit()
            logger.info(
                "all_sessions_revoked",
                user_id_hash=hash_id(user_id),
                count=count,
                reason=reason
            )
        
        return count
    
    async def get_active_sessions(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[Session]:
        """
        Get all active (non-revoked, non-expired) sessions for a user.
        Useful for displaying active devices to users.
        """
        stmt = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.revoked_at.is_(None),
                Session.expires_at > datetime.utcnow()
            )
        ).order_by(Session.created_at.desc())
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """
        Revoke all expired sessions.
        This can be run as a periodic cleanup task.
        Returns the number of sessions cleaned up.
        """
        stmt = select(Session).where(
            and_(
                Session.revoked_at.is_(None),
                Session.expires_at < datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        count = 0
        for session in sessions:
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = "EXPIRED"
            count += 1
        
        if count > 0:
            await db.commit()
            logger.info("expired_sessions_cleaned", count=count)
        
        return count
