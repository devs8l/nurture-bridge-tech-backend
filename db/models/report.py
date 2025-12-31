from datetime import datetime
from uuid import uuid4
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from db.base import Base
from db.models.mixins import TimestampMixin


class PoolSummary(Base, TimestampMixin):
    """
    AI-generated summary for a completed assessment pool.
    One summary per child per pool.
    """
    __tablename__ = "pool_summaries"
    __table_args__ = {"schema": "report"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    child_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clinical.children.id", ondelete="CASCADE"),
        nullable=False
    )

    pool_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        comment="Reference to assessment.pools.id (soft reference, no FK constraint)"
    )

    pool_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Denormalized pool title for convenience"
    )

    summary_content: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="AI-generated summary content"
    )

    total_sections: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Count of sections in this pool"
    )

    completed_sections: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Count of completed sections"
    )

    total_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Aggregate score across all sections in pool"
    )

    max_possible_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum possible aggregate score"
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when summary was generated"
    )

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="pool_summaries")

    def __repr__(self) -> str:
        return f"<PoolSummary(id={self.id}, child_id={self.child_id}, pool_id={self.pool_id})>"


class FinalReport(Base, TimestampMixin):
    """
    Comprehensive AI-generated final report combining all pool summaries.
    One report per child with two-stage review workflow (Doctor → HOD).
    """
    __tablename__ = "final_reports"
    __table_args__ = {"schema": "report"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    child_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clinical.children.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    overall_summary: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Comprehensive AI-generated summary including key findings and recommendations"
    )

    total_pools: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total count of pools"
    )

    completed_pools: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Count of completed pools with summaries"
    )

    overall_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Combined score across all pools"
    )

    overall_max_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Combined maximum possible score"
    )

    doctor_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="Timestamp when doctor reviewed/signed the report"
    )

    hod_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="Timestamp when HOD reviewed/signed the report (final sign-off)"
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when report was generated"
    )

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="final_report", uselist=False)

    def __repr__(self) -> str:
        return f"<FinalReport(id={self.id}, child_id={self.child_id})>"
