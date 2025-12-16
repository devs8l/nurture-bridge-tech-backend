from datetime import datetime
from uuid import uuid4
from typing import Optional, List

from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base
from db.models.mixins import TimestampMixin, SoftDeleteMixin

class Tenant(Base, TimestampMixin, SoftDeleteMixin):
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

    settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Tenant-specific configuration (branding, features, etc.)"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="tenant")
    doctors: Mapped[List["Doctor"]] = relationship("Doctor", back_populates="tenant")
    parents: Mapped[List["Parent"]] = relationship("Parent", back_populates="tenant")
    children: Mapped[List["Child"]] = relationship("Child", back_populates="tenant")
    sections: Mapped[List["AssessmentSection"]] = relationship("AssessmentSection", back_populates="tenant")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, code={self.code}, name={self.name})>"
