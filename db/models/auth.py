from datetime import datetime
from uuid import uuid4
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base
from db.models.mixins import TimestampMixin, SoftDeleteMixin

class UserRole(str, PyEnum):
    """
    User roles in the system.
    
    SUPER_ADMIN: Platform administrator
    TENANT_ADMIN: Hospital IT/System administrator (NOT receptionist)
    HOD: Head of Department - Clinical authority
    DOCTOR: Clinical reviewer
    RECEPTIONIST: Patient onboarding staff
    PARENT: Parent/caregiver
    """
    SUPER_ADMIN = "SUPER_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    HOD = "HOD"
    DOCTOR = "DOCTOR"
    RECEPTIONIST = "RECEPTIONIST"
    PARENT = "PARENT"

class UserStatus(str, PyEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"

class User(Base, TimestampMixin):
    """
    Represents an authenticated user.
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="NBT_super_admin",
        comment="User's full name, default for super admin"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        nullable=False
    )

    tenant_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenant.tenants.id"),
        nullable=True,
        comment="Required for all except SUPER_ADMIN"
    )

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False),
        default=UserStatus.PENDING,
        nullable=False
    )

    # Relationships
    tenant: Mapped[Optional["Tenant"]] = relationship("Tenant", back_populates="users")
    doctor_profile: Mapped[Optional["Doctor"]] = relationship("Doctor", back_populates="user", uselist=False)
    hod_profile: Mapped[Optional["HOD"]] = relationship("HOD", back_populates="user", uselist=False)
    receptionist_profile: Mapped[Optional["Receptionist"]] = relationship("Receptionist", back_populates="user", uselist=False)
    parent_profile: Mapped[Optional["Parent"]] = relationship("Parent", back_populates="user", uselist=False)
    sent_invitations: Mapped[List["Invitation"]] = relationship("Invitation", back_populates="invited_by_user", foreign_keys="[Invitation.invited_by_user_id]")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class InvitationStatus(str, PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class Invitation(Base): # <--- Removed TimestampMixin
    """
    Pending invitations to join the system.
    """
    __tablename__ = "invitations"
    __table_args__ = {"schema": "auth"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    role_to_assign: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        nullable=False
    )

    invited_by_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.id"),
        nullable=False
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenant.tenants.id"),
        nullable=False
    )

    doctor_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clinical.doctors.id"),
        nullable=True,
        comment="If user is a PARENT, this is their assigning doctor"
    )
    
    department: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Required for HOD/DOCTOR/RECEPTIONIST invitations"
    )

    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, native_enum=False),
        default=InvitationStatus.PENDING,
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    invited_by_user: Mapped["User"] = relationship("User", back_populates="sent_invitations", foreign_keys=[invited_by_user_id])
    # tenant relationship omitted for brevity/circularity simplification, can add if needed
    # doctor relationship omitted for brevity
    
    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, email={self.email}, status={self.status})>"


class Session(Base, TimestampMixin):
    """
    User session for refresh token management.
    Supports multi-device authentication with revocation.
    """
    __tablename__ = "sessions"
    __table_args__ = (
        UniqueConstraint('user_id', 'device_id', name='uq_user_device'),
        {"schema": "auth"}
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False
    )

    refresh_token_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="SHA-256 hash of refresh token, never store plaintext"
    )

    device_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Client-generated stable device identifier"
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Session expiry, should match JWT exp claim"
    )

    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When session was revoked, NULL if active"
    )

    revoked_reason: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="Reason for revocation: LOGOUT, TOKEN_ROTATED, etc."
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, device_id={self.device_id}, revoked={self.revoked_at is not None})>"
