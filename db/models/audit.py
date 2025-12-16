from datetime import datetime
from uuid import uuid4
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base

class AuditLog(Base):
    """
    Immutable audit log for compliance.
    Tracks WHO did WHAT to WHOM/WHAT and WHEN.
    """
    __tablename__ = "logs"
    __table_args__ = {"schema": "audit"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.id"),
        nullable=True,
        index=True
    )

    tenant_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenant.tenants.id"),
        nullable=True
    )

    child_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clinical.children.id"),
        nullable=True,
        index=True
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Effect: VIEW, CREATE, UPDATE, DELETE, LOGIN"
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    resource_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    tenant: Mapped["Tenant"] = relationship("Tenant")
    child: Mapped["Child"] = relationship("Child")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.user_id})>"
