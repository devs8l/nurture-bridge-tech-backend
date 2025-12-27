"""
Pydantic schemas for assessment models.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# SECTION SCHEMAS
# ============================================================================

class SectionBase(BaseModel):
    """Base schema for assessment section."""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    order_number: int = Field(default=0)
    is_active: bool = Field(default=True)


class SectionCreate(SectionBase):
    """Schema for creating an assessment section."""
    pass


class SectionResponse(SectionBase):
    """Schema for assessment section response."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# QUESTION SCHEMAS
# ============================================================================

class QuestionBase(BaseModel):
    """Base schema for assessment question."""
    section_id: str
    text: str
    min_age_months: int = Field(default=0)
    max_age_months: int = Field(default=120)
    age_protocol: dict = Field(default_factory=dict)
    order_number: int = Field(default=0)


class QuestionCreate(QuestionBase):
    """Schema for creating an assessment question."""
    pass


class QuestionResponse(QuestionBase):
    """Schema for assessment question response."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ResponseBase(BaseModel):
    """Base schema for assessment response."""
    child_id: str
    section_id: str
    assessment_language: str = Field(default="ENGLISH")


class ResponseCreate(ResponseBase):
    """Schema for creating an assessment response."""
    pass


class ResponseResponse(ResponseBase):
    """Schema for assessment response."""
    id: str
    status: str
    total_score: Optional[int] = None
    max_possible_score: Optional[int] = None
    completed_at: Optional[datetime] = None
    unanswered_questions: List[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ANSWER SCHEMAS
# ============================================================================

class AnswerBase(BaseModel):
    """Base schema for assessment question answer."""
    response_id: str
    question_id: str
    raw_answer: str
    translated_answer: Optional[str] = None
    answer_bucket: str = Field(..., max_length=50)
    score: int


class AnswerCreate(AnswerBase):
    """Schema for creating an assessment answer."""
    pass


class AnswerResponse(AnswerBase):
    """Schema for assessment answer response."""
    id: str
    answered_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CONVERSATION SUBMIT SCHEMAS
# ============================================================================

class ConversationSubmitRequest(BaseModel):
    """Schema for submitting conversation-based assessment answers."""
    response_id: str = Field(..., description="Assessment response ID")
    conversation: List[dict] = Field(..., description="Voice conversation as list of messages")


class ConversationSubmitResponse(BaseModel):
    """Schema for conversation submit response."""
    success: bool
    response_id: str
    section_id: str
    child_id: str
    answers_created: int
    total_questions: int
    section_complete: bool
    completion_percentage: float
    unmapped_questions: List[str] = Field(default_factory=list)
    mapped_answers: List[dict] = Field(default_factory=list, description="Question-answer pairs without scores")
    message: str


# ============================================================================
# PROGRESS SCHEMAS
# ============================================================================

class SectionProgress(BaseModel):
    """Schema for individual section progress."""
    section_id: str
    section_title: str
    response_id: Optional[str] = None
    status: str
    total_questions: int
    answered_questions: int
    unanswered_questions: int
    completion_percentage: float
    assessment_language: str = Field(default="ENGLISH")
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AssessmentProgressResponse(BaseModel):
    """Schema for overall assessment progress."""
    child_id: str
    total_sections: int
    sections_not_started: int
    sections_in_progress: int
    sections_completed: int
    overall_completion_percentage: float
    section_progress: List[SectionProgress]
    
    model_config = ConfigDict(from_attributes=True)