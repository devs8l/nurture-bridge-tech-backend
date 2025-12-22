from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import Field

from app.schemas.base import BaseSchema
from db.models.intake import IntakeStatus

# ============================================================================
# SECTION SCHEMAS
# ============================================================================

class IntakeSectionCreate(BaseSchema):
    """Schema for creating an intake section."""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    order_number: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)


class IntakeSectionUpdate(BaseSchema):
    """Schema for updating an intake section."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    order_number: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class IntakeSectionResponse(BaseSchema):
    """Schema for intake section response."""
    id: UUID
    title: str
    description: Optional[str] = None
    order_number: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# QUESTION SCHEMAS
# ============================================================================

class IntakeQuestionCreate(BaseSchema):
    """Schema for creating an intake question."""
    section_id: UUID
    text: str
    question_type: str = Field(..., max_length=50, description="TEXT, RADIO, CHECKBOX, SELECT, etc.")
    options: Optional[Dict[str, Any]] = None
    is_scorable: bool = Field(default=False)
    scoring_logic: Optional[Dict[str, Any]] = None
    order_number: int = Field(default=0, ge=0)


class IntakeQuestionUpdate(BaseSchema):
    """Schema for updating an intake question."""
    section_id: Optional[UUID] = None
    text: Optional[str] = None
    question_type: Optional[str] = Field(None, max_length=50)
    options: Optional[Dict[str, Any]] = None
    is_scorable: Optional[bool] = None
    scoring_logic: Optional[Dict[str, Any]] = None
    order_number: Optional[int] = Field(None, ge=0)


class IntakeQuestionResponse(BaseSchema):
    """Schema for intake question response."""
    id: UUID
    section_id: UUID
    text: str
    question_type: str
    options: Optional[Dict[str, Any]] = None
    is_scorable: bool
    scoring_logic: Optional[Dict[str, Any]] = None
    order_number: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# ANSWER SCHEMAS
# ============================================================================

class IntakeAnswerCreate(BaseSchema):
    """Schema for creating/updating an answer."""
    question_id: UUID
    raw_answer: Optional[str] = None
    answer_bucket: Optional[str] = Field(None, max_length=100)
    score: Optional[int] = None


class IntakeAnswerUpdate(BaseSchema):
    """Schema for updating an answer."""
    raw_answer: Optional[str] = None
    answer_bucket: Optional[str] = Field(None, max_length=100)
    score: Optional[int] = None


class IntakeAnswerResponse(BaseSchema):
    """Schema for intake answer response."""
    id: UUID
    response_id: UUID
    question_id: UUID
    raw_answer: Optional[str] = None
    answer_bucket: Optional[str] = None
    score: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class IntakeResponseCreate(BaseSchema):
    """Schema for creating an intake response."""
    child_id: UUID


class IntakeResponseUpdate(BaseSchema):
    """Schema for updating an intake response status."""
    status: IntakeStatus
    completed_at: Optional[datetime] = None


class IntakeResponseResponse(BaseSchema):
    """Schema for intake response."""
    id: UUID
    child_id: UUID
    status: IntakeStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IntakeResponseWithAnswers(IntakeResponseResponse):
    """Schema for intake response with answers."""
    answers: List[IntakeAnswerResponse] = []
    
    class Config:
        from_attributes = True


# ============================================================================
# BULK OPERATIONS SCHEMAS
# ============================================================================

class BulkAnswerCreate(BaseSchema):
    """Schema for creating/updating multiple answers at once."""
    response_id: UUID
    answers: List[IntakeAnswerCreate]


class IntakeSectionWithQuestions(IntakeSectionResponse):
    """Schema for section with its questions."""
    questions: List[IntakeQuestionResponse] = []
    
    class Config:
        from_attributes = True


class IntakeFormStructure(BaseSchema):
    """Complete intake form structure with sections and questions."""
    sections: List[IntakeSectionWithQuestions]
