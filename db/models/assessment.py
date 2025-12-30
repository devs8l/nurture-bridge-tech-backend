from datetime import datetime
from uuid import uuid4
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Integer, JSON, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base
from db.models.mixins import TimestampMixin

class AssessmentStatus(str, PyEnum):
    NOT_STARTED = "NOT_STARTED"
    PROCESSING = "PROCESSING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class AssessmentPool(Base, TimestampMixin):
    """
    Pool container that groups multiple assessment sections.
    """
    __tablename__ = "pools"
    __table_args__ = {"schema": "assessment"}

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

    def __repr__(self) -> str:
        return f"<AssessmentPool(id={self.id}, title={self.title})>"

class AssessmentSection(Base, TimestampMixin):
    """
    Assessment module (e.g. Social Interaction).
    """
    __tablename__ = "sections"
    __table_args__ = {"schema": "assessment"}

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

    pool_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        comment="Optional pool identifier (no foreign key constraint)"
    )

    def __repr__(self) -> str:
        return f"<AssessmentSection(id={self.id}, title={self.title})>"


class AssessmentQuestion(Base, TimestampMixin):
    """
    Single assessment question configuration.
    """
    __tablename__ = "questions"
    __table_args__ = {"schema": "assessment"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    section_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("assessment.sections.id"),
        nullable=False
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    min_age_months: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    max_age_months: Mapped[int] = mapped_column(
        Integer,
        default=120, # 10 years default cap
        nullable=False
    )

    age_protocol: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Defines behavior by age (e.g. valid answers, scoring logic)"
    )

    order_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<AssessmentQuestion(id={self.id}, text={self.text[:20]}...)>"


class ConversationLog(Base):
    """
    Stores raw conversation data from assessment submissions.
    Immutable - logs are never updated, only created.
    """
    __tablename__ = "conversation_logs"
    __table_args__ = {"schema": "assessment"}

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    response_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("assessment.responses.id"),
        nullable=False
    )

    conversation: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Raw conversation data from submission"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    response: Mapped["AssessmentResponse"] = relationship(
        "AssessmentResponse", 
        back_populates="conversation_logs",
        foreign_keys=[response_id]
    )

    def __repr__(self) -> str:
        return f"<ConversationLog(id={self.id}, response_id={self.response_id})>"


class AssessmentResponse(Base, TimestampMixin):
    """
    One assessment session for a child.
    """
    __tablename__ = "responses"
    __table_args__ = (
        UniqueConstraint('child_id', 'section_id', name='uq_child_section_response'),
        {"schema": "assessment"}
    )

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

    section_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("assessment.sections.id"),
        nullable=False
    )

    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus, name="assessment_status", schema="assessment"),
        default=AssessmentStatus.NOT_STARTED,
        nullable=False
    )

    total_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    max_possible_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    unanswered_questions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default='[]',
        comment="Array of question objects that were not answered in the conversation"
    )

    assessment_language: Mapped[str] = mapped_column(
        String(50),
        default="ENGLISH",
        nullable=False,
        server_default="ENGLISH"
    )

    last_conversation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        comment="ID of the most recent conversation log, overwritten on resume (not a FK to avoid circular dependency)"
    )

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="responses")
    section: Mapped["AssessmentSection"] = relationship("AssessmentSection")
    answers: Mapped[List["AssessmentQuestionAnswer"]] = relationship("AssessmentQuestionAnswer", back_populates="response")
    conversation_logs: Mapped[List["ConversationLog"]] = relationship(
        "ConversationLog", 
        back_populates="response",
        foreign_keys="[ConversationLog.response_id]"
    )

    def __repr__(self) -> str:
        return f"<AssessmentResponse(id={self.id}, status={self.status})>"


class AssessmentQuestionAnswer(Base, TimestampMixin):
    """
    Immutable answer to an assessment question.
    """
    __tablename__ = "question_answers"
    __table_args__ = (
        UniqueConstraint('response_id', 'question_id', name='uq_assessment_response_question'),
        {"schema": "assessment"}
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )

    response_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("assessment.responses.id"),
        nullable=False
    )

    question_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("assessment.questions.id"),
        nullable=False
    )

    raw_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What the parent actually selected/wrote"
    )

    translated_answer: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="English translation of the answer if provided in another language"
    )

    answer_bucket: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Normalized category (e.g. YES, NO)"
    )

    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Numeric score derived at that moment"
    )

    answered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    response: Mapped["AssessmentResponse"] = relationship("AssessmentResponse", back_populates="answers")
    question: Mapped["AssessmentQuestion"] = relationship("AssessmentQuestion")

    def __repr__(self) -> str:
        return f"<AssessmentQuestionAnswer(id={self.id}, score={self.score})>"
