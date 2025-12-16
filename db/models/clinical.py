from datetime import date
from uuid import uuid4
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, Date, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base
from db.models.mixins import TimestampMixin, SoftDeleteMixin

class Gender(str, PyEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class Doctor(Base, TimestampMixin, SoftDeleteMixin):
    """
    Represents a licensed clinician.
    """
    __tablename__ = "doctors"
    __table_args__ = {"schema": "clinical"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.id"),
        unique=True,
        nullable=False,
        comment="1-to-1 link with auth.users"
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenant.tenants.id"),
        nullable=False
    )

    license_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    specialization: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="doctor_profile")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="doctors")
    assigned_parents: Mapped[List["Parent"]] = relationship("Parent", back_populates="assigned_doctor")
    
    def __repr__(self) -> str:
        return f"<Doctor(id={self.id}, license={self.license_number})>"


class Parent(Base, TimestampMixin, SoftDeleteMixin):
    """
    Represents a parent or primary caregiver.
    """
    __tablename__ = "parents"
    __table_args__ = {"schema": "clinical"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.id"),
        unique=True,
        nullable=False,
        comment="1-to-1 link with auth.users"
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenant.tenants.id"),
        nullable=False
    )

    assigned_doctor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clinical.doctors.id"),
        nullable=False
    )

    phone_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="parent_profile")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="parents")
    assigned_doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="assigned_parents")
    children: Mapped[List["Child"]] = relationship("Child", back_populates="parent")

    def __repr__(self) -> str:
        return f"<Parent(id={self.id}, user_id={self.user_id})>"


class Child(Base, TimestampMixin, SoftDeleteMixin):
    """
    Represents the subject of assessment.
    """
    __tablename__ = "children"
    __table_args__ = {"schema": "clinical"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    parent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clinical.parents.id"),
        nullable=False
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenant.tenants.id"),
        nullable=False
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    gender: Mapped[Gender] = mapped_column(
        Enum(Gender, name="child_gender", schema="clinical"),
        nullable=False
    )

    # Relationships
    parent: Mapped["Parent"] = relationship("Parent", back_populates="children")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="children")
    responses: Mapped[List["AssessmentResponse"]] = relationship("AssessmentResponse", back_populates="child")
    intake_responses: Mapped[List["IntakeResponse"]] = relationship("IntakeResponse", back_populates="child")

    def __repr__(self) -> str:
        return f"<Child(id={self.id}, name={self.first_name} {self.last_name})>"
