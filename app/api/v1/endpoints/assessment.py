"""
Assessment endpoints for handling assessment sections, questions, responses, and answers.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app_logging.logger import get_logger
from db.base import get_db
from db.models.assessment import (
    AssessmentSection,
    AssessmentQuestion,
    AssessmentResponse,
    AssessmentQuestionAnswer,
    AssessmentStatus
)
from app.schemas.assessment import (
    SectionCreate,
    SectionResponse,
    QuestionCreate,
    QuestionResponse,
    ResponseCreate,
    ResponseResponse,
    AnswerCreate,
    AnswerResponse
)

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# SECTION ENDPOINTS
# ============================================================================

@router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    section_data: SectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new assessment section."""
    section = AssessmentSection(**section_data.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


@router.get("/sections", response_model=List[SectionResponse])
async def get_sections(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all assessment sections."""
    query = select(AssessmentSection)
    
    if is_active is not None:
        query = query.where(AssessmentSection.is_active == is_active)
    
    query = query.order_by(AssessmentSection.order_number).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific assessment section by ID."""
    result = await db.execute(
        select(AssessmentSection).where(AssessmentSection.id == section_id)
    )
    section = result.scalar_one_or_none()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with id {section_id} not found"
        )
    
    return section


@router.put("/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: str,
    section_data: SectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update an assessment section."""
    result = await db.execute(
        select(AssessmentSection).where(AssessmentSection.id == section_id)
    )
    section = result.scalar_one_or_none()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with id {section_id} not found"
        )
    
    for key, value in section_data.model_dump().items():
        setattr(section, key, value)
    
    await db.commit()
    await db.refresh(section)
    return section


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an assessment section."""
    result = await db.execute(
        select(AssessmentSection).where(AssessmentSection.id == section_id)
    )
    section = result.scalar_one_or_none()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with id {section_id} not found"
        )
    
    await db.delete(section)
    await db.commit()


# ============================================================================
# QUESTION ENDPOINTS
# ============================================================================

@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: QuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new assessment question."""
    question = AssessmentQuestion(**question_data.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@router.get("/questions", response_model=List[QuestionResponse])
async def get_questions(
    section_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all assessment questions, optionally filtered by section."""
    query = select(AssessmentQuestion)
    
    if section_id:
        query = query.where(AssessmentQuestion.section_id == section_id)
    
    query = query.order_by(AssessmentQuestion.order_number).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific assessment question by ID."""
    result = await db.execute(
        select(AssessmentQuestion).where(AssessmentQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with id {question_id} not found"
        )
    
    return question


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    question_data: QuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update an assessment question."""
    result = await db.execute(
        select(AssessmentQuestion).where(AssessmentQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with id {question_id} not found"
        )
    
    for key, value in question_data.model_dump().items():
        setattr(question, key, value)
    
    await db.commit()
    await db.refresh(question)
    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an assessment question."""
    result = await db.execute(
        select(AssessmentQuestion).where(AssessmentQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with id {question_id} not found"
        )
    
    await db.delete(question)
    await db.commit()


# ============================================================================
# RESPONSE ENDPOINTS
# ============================================================================

@router.post("/responses", response_model=ResponseResponse, status_code=status.HTTP_201_CREATED)
async def create_response(
    response_data: ResponseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new assessment response (session)."""
    response = AssessmentResponse(**response_data.model_dump())
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return response


@router.get("/responses", response_model=List[ResponseResponse])
async def get_responses(
    child_id: str = None,
    section_id: str = None,
    status_filter: AssessmentStatus = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all assessment responses, optionally filtered."""
    query = select(AssessmentResponse).options(
        selectinload(AssessmentResponse.answers)
    )
    
    if child_id:
        query = query.where(AssessmentResponse.child_id == child_id)
    if section_id:
        query = query.where(AssessmentResponse.section_id == section_id)
    if status_filter:
        query = query.where(AssessmentResponse.status == status_filter)
    
    query = query.order_by(AssessmentResponse.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/responses/{response_id}", response_model=ResponseResponse)
async def get_response(
    response_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific assessment response by ID."""
    result = await db.execute(
        select(AssessmentResponse)
        .options(selectinload(AssessmentResponse.answers))
        .where(AssessmentResponse.id == response_id)
    )
    response = result.scalar_one_or_none()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response with id {response_id} not found"
        )
    
    return response


@router.patch("/responses/{response_id}/complete", response_model=ResponseResponse)
async def complete_response(
    response_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Mark an assessment response as completed."""
    result = await db.execute(
        select(AssessmentResponse).where(AssessmentResponse.id == response_id)
    )
    response = result.scalar_one_or_none()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response with id {response_id} not found"
        )
    
    from datetime import datetime
    response.status = AssessmentStatus.COMPLETED
    response.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(response)
    return response


# ============================================================================
# ANSWER ENDPOINTS
# ============================================================================

@router.post("/answers", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_answer(
    answer_data: AnswerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new assessment question answer."""
    answer = AssessmentQuestionAnswer(**answer_data.model_dump())
    db.add(answer)
    await db.commit()
    await db.refresh(answer)
    return answer


@router.get("/answers", response_model=List[AnswerResponse])
async def get_answers(
    response_id: str = None,
    question_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all assessment answers, optionally filtered."""
    query = select(AssessmentQuestionAnswer)
    
    if response_id:
        query = query.where(AssessmentQuestionAnswer.response_id == response_id)
    if question_id:
        query = query.where(AssessmentQuestionAnswer.question_id == question_id)
    
    query = query.order_by(AssessmentQuestionAnswer.answered_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/answers/{answer_id}", response_model=AnswerResponse)
async def get_answer(
    answer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific assessment answer by ID."""
    result = await db.execute(
        select(AssessmentQuestionAnswer).where(AssessmentQuestionAnswer.id == answer_id)
    )
    answer = result.scalar_one_or_none()
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Answer with id {answer_id} not found"
        )
    
    return answer
