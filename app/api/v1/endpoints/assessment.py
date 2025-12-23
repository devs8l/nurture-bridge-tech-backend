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
    AnswerResponse,
    ConversationSubmitRequest,
    ConversationSubmitResponse
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
    #TODO: Add age filter
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


# ============================================================================
# CONVERSATION SUBMIT ENDPOINT
# ============================================================================

@router.post("/submit", response_model=ConversationSubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_conversation_answers(
    submit_data: ConversationSubmitRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit conversation-based assessment answers.
    
    This endpoint:
    1. Uses AI to map questions to answers from conversation
    2. Uploads answers to question_answers table
    3. Checks if all applicable questions for the section are answered
    4. Returns completion status
    """
    from app.main import get_gemini_service
    from sqlalchemy import func
    
    logger.info(
        "conversation_submit_request",
        response_id=submit_data.response_id,
        question_count=len(submit_data.questions),
        section_id=submit_data.section_id
    )
    
    # Verify response exists
    result = await db.execute(
        select(AssessmentResponse).where(AssessmentResponse.id == submit_data.response_id)
    )
    response = result.scalar_one_or_none()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response with id {submit_data.response_id} not found"
        )
    
    # Get AI service
    ai_service = get_gemini_service() 
    
    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not available. Please configure GEMINI_API_KEY."
        )
    
    try:
        # Use AI to map questions to answers
        logger.info(
            "calling_ai_map_questions",
            response_id=submit_data.response_id,
            question_count=len(submit_data.questions)
        )
        
        ai_result = await ai_service.map_questions_to_answers(
            conversation=submit_data.conversation,
            questions=submit_data.questions,
            actor=f"system:assessment_submit"
        )
        
        if not ai_result.get("success"):
            logger.error(
                "ai_mapping_failed",
                response_id=submit_data.response_id,
                error=ai_result.get("error")
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI mapping failed: {ai_result.get('error', 'Unknown error')}"
            )
        
        mapped_data = ai_result.get("result", {})
        answers = mapped_data.get("answers", [])
        unmapped_question_ids = mapped_data.get("meta", {}).get("unanswered_question_ids", [])
        
        logger.info(
            "ai_mapping_success",
            response_id=submit_data.response_id,
            mapped_count=len(answers),
            unmapped_count=len(unmapped_question_ids)
        )
        
        # Upload answers to question_answers table
        answers_created = 0
        for answer_data in answers:
            try:
                # Create answer record
                answer = AssessmentQuestionAnswer(
                    response_id=submit_data.response_id,
                    question_id=answer_data.get("question_id"),
                    raw_answer=answer_data.get("raw_answer", ""),
                    answer_bucket=answer_data.get("answer_bucket", "NOT_OBSERVED"),
                    score=answer_data.get("score", 0)
                )
                db.add(answer)
                answers_created += 1
                
            except Exception as e:
                logger.warning(
                    "answer_creation_failed",
                    response_id=submit_data.response_id,
                    question_id=answer_data.get("question_id"),
                    error=str(e)
                )
        
        # Commit all answer
        await db.commit()
        
        logger.info(
            "answers_uploaded",
            response_id=submit_data.response_id,
            answers_created=answers_created
        )
        
        # Check section completion
        # Get total applicable questions for this section and child age
        applicable_questions_result = await db.execute(
            select(func.count(AssessmentQuestion.id))
            .where(
                AssessmentQuestion.section_id == submit_data.section_id,
                AssessmentQuestion.min_age_months <= submit_data.child_age_months,
                AssessmentQuestion.max_age_months >= submit_data.child_age_months
            )
        )
        total_applicable_questions = applicable_questions_result.scalar() or 0
        
        # Get count of answered questions for this response
        answered_questions_result = await db.execute(
            select(func.count(AssessmentQuestionAnswer.id))
            .where(AssessmentQuestionAnswer.response_id == submit_data.response_id)
        )
        answered_questions_count = answered_questions_result.scalar() or 0
        
        # Calculate completion
        section_complete = answered_questions_count >= total_applicable_questions
        completion_percentage = (
            (answered_questions_count / total_applicable_questions * 100)
            if total_applicable_questions > 0
            else 0.0
        )
        
        logger.info(
            "section_completion_check",
            response_id=submit_data.response_id,
            section_id=submit_data.section_id,
            answered=answered_questions_count,
            total_applicable=total_applicable_questions,
            complete=section_complete,
            percentage=completion_percentage
        )
        
        # Update response status if section is complete
        if section_complete and response.status != AssessmentStatus.COMPLETED:
            from datetime import datetime
            response.status = AssessmentStatus.COMPLETED
            response.completed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(
                "response_marked_complete",
                response_id=submit_data.response_id
            )
        
        return ConversationSubmitResponse(
            success=True,
            response_id=submit_data.response_id,
            section_id=submit_data.section_id,
            child_id=submit_data.child_id,
            answers_created=answers_created,
            total_questions=total_applicable_questions,
            section_complete=section_complete,
            completion_percentage=round(completion_percentage, 2),
            unmapped_questions=unmapped_question_ids,
            message=f"Successfully created {answers_created} answers. Section {'complete' if section_complete else 'in progress'}."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "conversation_submit_error",
            response_id=submit_data.response_id,
            error=str(e),
            error_type=type(e).__name__
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process conversation: {str(e)}"
        )
