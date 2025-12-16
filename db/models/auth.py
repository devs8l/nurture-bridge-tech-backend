from datetime import datetime
from uuid import uuid4
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base
from db.models.mixins import TimestampMixin, SoftDeleteMixin

class UserRole(str, PyEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    DOCTOR = "DOCTOR"
    PARENT = "PARENT"

class UserStatus(str, PyEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"

class User(Base, TimestampMixin, SoftDeleteMixin):
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

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", schema="auth"),
        nullable=False
    )

    tenant_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenant.tenants.id"),
        nullable=True,
        comment="Required for all except SUPER_ADMIN"
    )

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", schema="auth"),
        default=UserStatus.PENDING,
        nullable=False
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Relationships
    tenant: Mapped[Optional["Tenant"]] = relationship("Tenant", back_populates="users")
    doctor_profile: Mapped[Optional["Doctor"]] = relationship("Doctor", back_populates="user", uselist=False)
    parent_profile: Mapped[Optional["Parent"]] = relationship("Parent", back_populates="user", uselist=False)
    sent_invitations: Mapped[List["Invitation"]] = relationship("Invitation", back_populates="invited_by_user", foreign_keys="[Invitation.invited_by_user_id]")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class InvitationStatus(str, PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class Invitation(Base, TimestampMixin):
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
        Enum(UserRole, name="user_role", schema="auth"),
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

    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, name="invitation_status", schema="auth"),
        default=InvitationStatus.PENDING,
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    # Relationships
    invited_by_user: Mapped["User"] = relationship("User", back_populates="sent_invitations", foreign_keys=[invited_by_user_id])
    # tenant relationship omitted for brevity/circularity simplification, can add if needed
    # doctor relationship omitted for brevity
    
    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, email={self.email}, status={self.status})>"
