from datetime import datetime
from uuid import uuid4
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base
from db.models.mixins import TimestampMixin

class IntakeStatus(str, PyEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class IntakeSection(Base, TimestampMixin):
    """
    Logical UI sections for intake (e.g., "Birth History").
    """
    __tablename__ = "sections"
    __table_args__ = {"schema": "intake"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    order_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationships
    questions: Mapped[List["IntakeQuestion"]] = relationship("IntakeQuestion", back_populates="section")

    def __repr__(self) -> str:
        return f"<IntakeSection(id={self.id}, title={self.title})>"


class IntakeQuestion(Base, TimestampMixin):
    """
    Questions for intake forms. Configuration driven.
    """
    __tablename__ = "questions"
    __table_args__ = {"schema": "intake"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    section_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("intake.sections.id"),
        nullable=False
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    question_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="TEXT, RADIO, CHECKBOX, etc."
    )

    options: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    is_scorable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    scoring_logic: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Logic to derive score from answer"
    )

    order_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Relationships
    section: Mapped["IntakeSection"] = relationship("IntakeSection", back_populates="questions")

    def __repr__(self) -> str:
        return f"<IntakeQuestion(id={self.id}, text={self.text[:20]}...)>"


class IntakeResponse(Base, TimestampMixin):
    """
    One intake session per child.
    Mutable and resumable.
    """
    __tablename__ = "responses"
    __table_args__ = {"schema": "intake"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    child_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clinical.children.id"),
        nullable=False
    )

    status: Mapped[IntakeStatus] = mapped_column(
        Enum(IntakeStatus, name="intake_status", schema="intake"),
        default=IntakeStatus.IN_PROGRESS,
        nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="intake_responses")
    answers: Mapped[List["IntakeAnswer"]] = relationship("IntakeAnswer", back_populates="response")

    def __repr__(self) -> str:
        return f"<IntakeResponse(id={self.id}, status={self.status})>"


class IntakeAnswer(Base, TimestampMixin):
    """
    Answers to intake questions.
    MUTABLE unlike assessment answers.
    """
    __tablename__ = "answers"
    __table_args__ = {"schema": "intake"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    response_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("intake.responses.id"),
        nullable=False
    )

    question_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("intake.questions.id"),
        nullable=False
    )

    raw_answer: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    answer_bucket: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Informational score, recomputable"
    )

    # Relationships
    response: Mapped["IntakeResponse"] = relationship("IntakeResponse", back_populates="answers")
    question: Mapped["IntakeQuestion"] = relationship("IntakeQuestion")

    def __repr__(self) -> str:
        return f"<IntakeAnswer(id={self.id}, question_id={self.question_id})>"
