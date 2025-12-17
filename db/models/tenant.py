from datetime import datetime
from uuid import uuid4
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, JSON, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base
from db.models.mixins import SoftDeleteMixin

class TenantStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class Tenant(Base):
    """
    Represents a hospital, clinic, or organization.
    Partitioning key for most data.
    """
    __tablename__ = "tenants"
    __table_args__ = {"schema": "tenant"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Human-friendly unique identifier (e.g., 'MAYO-CLINIC')"
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name of the organization"
    )

    registration_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    registration_authority: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    accreditation_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, native_enum=False),
        default=TenantStatus.ACTIVE,
        nullable=False
    )

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="tenant")
    doctors: Mapped[List["Doctor"]] = relationship("Doctor", back_populates="tenant")
    parents: Mapped[List["Parent"]] = relationship("Parent", back_populates="tenant")
    children: Mapped[List["Child"]] = relationship("Child", back_populates="tenant")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, code={self.code}, name={self.name})>"
