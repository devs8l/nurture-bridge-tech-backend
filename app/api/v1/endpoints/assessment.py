"""
Assessment endpoints for handling assessment sections, questions, responses, and answers.
"""

from typing import List
from uuid import UUID
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app_logging.logger import get_logger
from db.base import get_db
from db.models.assessment import (
    AssessmentPool,
    AssessmentSection,
    AssessmentQuestion,
    AssessmentResponse,
    AssessmentQuestionAnswer,
    AssessmentStatus,
    ConversationLog
)
from db.models.clinical import Child
from app.schemas.assessment import (
    PoolCreate,
    PoolResponse,
    SectionCreate,
    SectionResponse,
    QuestionCreate,
    QuestionResponse,
    ResponseCreate,
    ResponseResponse,
    AnswerCreate,
    AnswerResponse,
    ConversationSubmitRequest,
    ConversationSubmitResponse,
    SectionProgress,
    AssessmentProgressResponse,
    DetailedResponseResponse,
    DetailedAnswerResponse
)

logger = get_logger(__name__)
router = APIRouter()

def calculate_age(dob):
    # Calculate age in months with DOB
    today = date.today()
    age_in_months = (today.year - dob.year) * 12 + (today.month - dob.month)
    return age_in_months



# ============================================================================
# POOL ENDPOINTS
# ============================================================================

@router.post("/pools", response_model=PoolResponse, status_code=status.HTTP_201_CREATED)
async def create_pool(
    pool_data: PoolCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new assessment pool."""
    pool = AssessmentPool(**pool_data.model_dump())
    db.add(pool)
    await db.commit()
    await db.refresh(pool)
    return pool


@router.get("/pools", response_model=List[PoolResponse])
async def get_pools(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all assessment pools."""
    query = select(AssessmentPool)
    
    if is_active is not None:
        query = query.where(AssessmentPool.is_active == is_active)
    
    query = query.order_by(AssessmentPool.order_number).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/pools/{pool_id}", response_model=PoolResponse)
async def get_pool(
    pool_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific assessment pool by ID."""
    result = await db.execute(
        select(AssessmentPool).where(AssessmentPool.id == pool_id)
    )
    pool = result.scalar_one_or_none()
    
    if not pool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pool with id {pool_id} not found"
        )
    
    return pool


@router.put("/pools/{pool_id}", response_model=PoolResponse)
async def update_pool(
    pool_id: str,
    pool_data: PoolCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update an assessment pool."""
    result = await db.execute(
        select(AssessmentPool).where(AssessmentPool.id == pool_id)
    )
    pool = result.scalar_one_or_none()
    
    if not pool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pool with id {pool_id} not found"
        )
    
    for key, value in pool_data.model_dump().items():
        setattr(pool, key, value)
    
    await db.commit()
    await db.refresh(pool)
    return pool


@router.delete("/pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pool(
    pool_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an assessment pool."""
    result = await db.execute(
        select(AssessmentPool).where(AssessmentPool.id == pool_id)
    )
    pool = result.scalar_one_or_none()
    
    if not pool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pool with id {pool_id} not found"
        )
    
    await db.delete(pool)
    await db.commit()


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
    pool_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all assessment sections, optionally filtered by pool_id."""
    query = select(AssessmentSection)
    
    if is_active is not None:
        query = query.where(AssessmentSection.is_active == is_active)
    
    if pool_id is not None:
        query = query.where(AssessmentSection.pool_id == pool_id)
    
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
    age_in_months: int = Query(None, description="Filter questions by child's age in months"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all assessment questions, optionally filtered by section and age."""
    query = select(AssessmentQuestion)
    
    if section_id:
        query = query.where(AssessmentQuestion.section_id == section_id)
    
    if age_in_months is not None:
        query = query.where(
            AssessmentQuestion.min_age_months <= age_in_months,
            AssessmentQuestion.max_age_months >= age_in_months
        )
    
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
    """
    Create a new assessment response (session).
    Automatically fetches and stores applicable questions based on child's age.
    """
    # Get child to calculate age
    child = await db.get(Child, response_data.child_id)
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Child with id {response_data.child_id} not found"
        )
    
    # Calculate child's age in months
    child_age_months = calculate_age(child.date_of_birth)
    
    # Check if a response already exists for this child and section
    existing_response_result = await db.execute(
        select(AssessmentResponse).where(
            AssessmentResponse.child_id == response_data.child_id,
            AssessmentResponse.section_id == response_data.section_id
        )
    )
    existing_response = existing_response_result.scalar_one_or_none()
    
    if existing_response:
        logger.info(
            "response_already_exists",
            child_id=response_data.child_id,
            section_id=response_data.section_id,
            existing_response_id=existing_response.id
        )
        return existing_response
    
    logger.info(
        "creating_response",
        child_id=response_data.child_id,
        section_id=response_data.section_id
    )
    
    # Fetch applicable questions for this section and child's age
    questions_result = await db.execute(
        select(AssessmentQuestion)
        .where(
            AssessmentQuestion.section_id == response_data.section_id,
            AssessmentQuestion.min_age_months <= child_age_months,
            AssessmentQuestion.max_age_months >= child_age_months
        )
        .order_by(AssessmentQuestion.order_number)
    )
    applicable_questions = questions_result.scalars().all()
    
    # Convert questions to JSON format for storage
    unanswered_questions_list = [
        {
            "id": str(q.id),
            "text": q.text,
            "age_protocol": q.age_protocol,
            "order_number": q.order_number
        }
        for q in applicable_questions
    ]
    
    logger.info(
        "applicable_questions_fetched_for_new_response",
        section_id=response_data.section_id,
        child_age_months=child_age_months,
        question_count=len(unanswered_questions_list)
    )
    
    # Create response with unanswered questions
    response = AssessmentResponse(
        **response_data.model_dump(),
        unanswered_questions=unanswered_questions_list
    )
    
    db.add(response)
    await db.commit()
    await db.refresh(response)
    
    logger.info(
        "response_created",
        response_id=response.id,
        initial_question_count=len(unanswered_questions_list)
    )
    
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


@router.get("/responses/detail", response_model=DetailedResponseResponse)
async def get_response_detail(
    child_id: str,
    section_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed assessment response by child_id and section_id.
    Returns response details with all question-answer mappings and total score.
    """
    logger.info(
        "fetching_detailed_response",
        child_id=child_id,
        section_id=section_id
    )
    
    # Fetch response with answers and questions eagerly loaded
    result = await db.execute(
        select(AssessmentResponse)
        .options(
            selectinload(AssessmentResponse.answers).selectinload(AssessmentQuestionAnswer.question),
            selectinload(AssessmentResponse.section)
        )
        .where(
            AssessmentResponse.child_id == child_id,
            AssessmentResponse.section_id == section_id
        )
    )
    response = result.scalar_one_or_none()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response not found for child_id={child_id} and section_id={section_id}"
        )
    
    # Calculate total score from all answers
    total_score = sum(answer.score for answer in response.answers)
    
    # Build detailed answer list with question information
    detailed_answers = [
        DetailedAnswerResponse(
            id=str(answer.id),
            question_id=str(answer.question_id),
            question_text=answer.question.text,
            raw_answer=answer.raw_answer,
            translated_answer=answer.translated_answer,
            answer_bucket=answer.answer_bucket,
            score=answer.score,
            answered_at=answer.answered_at
        )
        for answer in response.answers
    ]
    
    logger.info(
        "detailed_response_fetched",
        response_id=response.id,
        total_answers=len(detailed_answers),
        total_score=total_score
    )
    
    return DetailedResponseResponse(
        id=str(response.id),
        child_id=str(response.child_id),
        section_id=str(response.section_id),
        section_title=response.section.title,
        status=response.status.value,
        assessment_language=response.assessment_language,
        total_score=total_score,
        max_possible_score=response.max_possible_score,
        completed_at=response.completed_at,
        answers=detailed_answers,
        created_at=response.created_at,
        updated_at=response.updated_at
    )


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
    1. Fetches response and its unanswered questions
    2. Uses AI to map questions to answers from conversation (with child age context)
    3. Uploads answers to question_answers table
    4. Updates unanswered_questions list by removing answered questions
    5. Checks completion status and returns results
    """
    from app.main import get_gemini_service
    
    logger.info(
        "conversation_submit_request",
        response_id=submit_data.response_id
    )
    
    try:
        # Fetch response with all needed data
        result = await db.execute(
            select(AssessmentResponse).where(AssessmentResponse.id == submit_data.response_id)
        )
        response = result.scalar_one_or_none()
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Response with id {submit_data.response_id} not found"
            )
        
        # Extract child_id and section_id from response
        child_id = response.child_id
        section_id = response.section_id
        
        # Get unanswered questions from response
        unanswered_questions = response.unanswered_questions or []
        
        if not unanswered_questions:
            logger.warning(
                "no_unanswered_questions",
                response_id=submit_data.response_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No unanswered questions found for this response. Assessment may already be complete."
            )
        
        # Get child to calculate age for AI context
        child = await db.get(Child, child_id)
        
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Child with id {child_id} not found"
            )
        
        # Calculate child's age in months for AI context
        child_age_months = calculate_age(child.date_of_birth)
        
        logger.info(
            "processing_submission",
            response_id=submit_data.response_id,
            child_id=child_id,
            section_id=section_id,
            child_age_months=child_age_months,
            unanswered_question_count=len(unanswered_questions)
        )
        
        # STEP 1: Store raw conversation in conversation_logs table
        from db.models.assessment import ConversationLog
        
        conversation_log = ConversationLog(
            response_id=submit_data.response_id,
            conversation=submit_data.conversation
        )
        db.add(conversation_log)
        await db.flush()  # Flush to get the ID
        
        logger.info(
            "conversation_log_created",
            response_id=submit_data.response_id,
            conversation_log_id=conversation_log.id
        )
        
        # STEP 2: Update response's last_conversation_id (overwrites if exists)
        response.last_conversation_id = conversation_log.id
        await db.commit()
        
        logger.info(
            "conversation_log_stored",
            response_id=submit_data.response_id,
            conversation_log_id=conversation_log.id
        )
        
        # Get AI service
        ai_service = get_gemini_service() 

        
        if not ai_service.is_available():
            # Set PROCESSING status on error
            response.status = AssessmentStatus.PROCESSING
            await db.commit()
            logger.error(
                "ai_service_unavailable",
                response_id=submit_data.response_id
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not available. Please configure GEMINI_API_KEY."
            )
        
        # Use AI to map questions to answers (passing age for context)
        logger.info(
            "calling_ai_map_questions",
            response_id=submit_data.response_id,
            question_count=len(unanswered_questions)
        )
        
        ai_result = await ai_service.map_questions_to_answers(
            conversation=submit_data.conversation,
            questions=unanswered_questions,
            child_age_months=child_age_months,
            actor=f"system:assessment_submit"
        )
        
        if not ai_result.get("success"):
            # Set PROCESSING status on AI mapping failure
            response.status = AssessmentStatus.PROCESSING
            await db.commit()
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
        failed_answers = 0
        
        for answer_data in answers:
            try:
                # Create answer record
                answer = AssessmentQuestionAnswer(
                    response_id=submit_data.response_id,
                    question_id=answer_data.get("question_id"),
                    raw_answer=answer_data.get("raw_answer", ""),
                    translated_answer=answer_data.get("eng_translated_answer"),
                    answer_bucket=answer_data.get("answer_bucket", "NOT_OBSERVED"),
                    score=answer_data.get("score", 0)
                )
                db.add(answer)
                answers_created += 1
                
            except Exception as e:
                failed_answers += 1
                logger.warning(
                    "answer_creation_failed",
                    response_id=submit_data.response_id,
                    question_id=answer_data.get("question_id"),
                    error=str(e)
                )
        
        # Commit all answers
        await db.commit()
        
        logger.info(
            "answers_uploaded",
            response_id=submit_data.response_id,
            answers_created=answers_created,
            failed_answers=failed_answers
        )
        
        # Update unanswered questions list by removing answered questions
        answered_question_ids = {answer_data.get("question_id") for answer_data in answers}
        
        updated_unanswered = [
            q for q in unanswered_questions 
            if q.get("id") not in answered_question_ids
        ]
        
        response.unanswered_questions = updated_unanswered
        
        # Get total count of all questions that were initially assigned
        # This is the original count from when response was created
        total_questions_result = await db.execute(
            select(func.count(AssessmentQuestion.id))
            .where(
                AssessmentQuestion.section_id == section_id,
                AssessmentQuestion.min_age_months <= child_age_months,
                AssessmentQuestion.max_age_months >= child_age_months
            )
        )
        total_applicable_questions = total_questions_result.scalar() or 0
        
        # Get count of answered questions for this response
        answered_questions_result = await db.execute(
            select(func.count(AssessmentQuestionAnswer.id))
            .where(AssessmentQuestionAnswer.response_id == submit_data.response_id)
        )
        answered_questions_count = answered_questions_result.scalar() or 0
        
        # Calculate completion
        section_complete = len(updated_unanswered) == 0
        completion_percentage = (
            (answered_questions_count / total_applicable_questions * 100)
            if total_applicable_questions > 0
            else 0.0
        )
        
        logger.info(
            "section_completion_check",
            response_id=submit_data.response_id,
            section_id=section_id,
            answered=answered_questions_count,
            total_applicable=total_applicable_questions,
            still_unanswered=len(updated_unanswered),
            complete=section_complete,
            percentage=completion_percentage
        )
        
        # Update response status based on progress
        if section_complete and response.status != AssessmentStatus.COMPLETED:
            response.status = AssessmentStatus.COMPLETED
            response.completed_at = datetime.utcnow()
        elif answers_created > 0 and response.status in (AssessmentStatus.NOT_STARTED, AssessmentStatus.PROCESSING):
            # Transition from NOT_STARTED or PROCESSING (error recovery) to IN_PROGRESS
            response.status = AssessmentStatus.IN_PROGRESS
        
        await db.commit()
        
        if section_complete:
            logger.info(
                "response_marked_complete",
                response_id=submit_data.response_id
            )
        
        # Build simplified mapped answers for response (question + answer only)
        mapped_answers_simplified = [
            {
                "question_id": ans.get("question_id"),
                "question_text": next(
                    (q.get("text") for q in unanswered_questions if q.get("id") == ans.get("question_id")),
                    None
                ),
                "answer": ans.get("raw_answer")
            }
            for ans in answers
        ]
        
        return ConversationSubmitResponse(
            success=True,
            response_id=submit_data.response_id,
            section_id=section_id,
            child_id=child_id,
            conversation_log_id=conversation_log.id,
            answers_created=answers_created,
            total_questions=total_applicable_questions,
            section_complete=section_complete,
            completion_percentage=round(completion_percentage, 2),
            unmapped_questions=unmapped_question_ids,
            mapped_answers=mapped_answers_simplified,
            message=f"Successfully created {answers_created} answers. Section {'complete' if section_complete else 'in progress'}."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Set PROCESSING status on any unexpected error during AI processing
        try:
            response.status = AssessmentStatus.PROCESSING
            await db.commit()
        except:
            pass  # If commit fails, at least log the error
        
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

# ============================================================================
# PROGRESS ENDPOINT
# ============================================================================

@router.get("/progress/{child_id}", response_model=AssessmentProgressResponse)
async def get_assessment_progress(
    child_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive assessment progress for a child.
    
    Returns:
    - Overall completion percentage
    - Per-section progress with status
    - Count of sections by status (not started, in progress, completed)
    """
    logger.info(
        "assessment_progress_request",
        child_id=child_id
    )
    
    try:
        # Verify child exists
        child = await db.get(Child, child_id)
        
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Child with id {child_id} not found"
            )
        
        # Calculate child's age in months
        child_age_months = calculate_age(child.date_of_birth)
        
        # Get all active sections
        sections_result = await db.execute(
            select(AssessmentSection)
            .where(AssessmentSection.is_active == True)
            .order_by(AssessmentSection.order_number)
        )
        all_sections = sections_result.scalars().all()
        
        # Get all responses for this child
        responses_result = await db.execute(
            select(AssessmentResponse)
            .where(AssessmentResponse.child_id == child_id)
        )
        responses = responses_result.scalars().all()
        
        # Create a map of section_id to response
        response_map = {r.section_id: r for r in responses}
        
        # Build section progress list
        section_progress_list = []
        sections_not_started = 0
        sections_in_progress = 0
        sections_completed = 0
        total_completion = 0.0
        
        for section in all_sections:
            response = response_map.get(section.id)
            
            if not response:
                # Section not started
                # Get total questions for this section and age
                questions_result = await db.execute(
                    select(func.count(AssessmentQuestion.id))
                    .where(
                        AssessmentQuestion.section_id == section.id,
                        AssessmentQuestion.min_age_months <= child_age_months,
                        AssessmentQuestion.max_age_months >= child_age_months
                    )
                )
                total_questions = questions_result.scalar() or 0
                
                section_progress_list.append(SectionProgress(
                    section_id=section.id,
                    section_title=section.title,
                    pool_id=section.pool_id,
                    response_id=None,
                    status="NOT_STARTED",
                    total_questions=total_questions,
                    answered_questions=0,
                    unanswered_questions=total_questions,
                    completion_percentage=0.0,
                    assessment_language="ENGLISH",
                    created_at=None,
                    completed_at=None
                ))
                sections_not_started += 1
            else:
                # Section has a response
                # Get total questions for this section and age
                questions_result = await db.execute(
                    select(func.count(AssessmentQuestion.id))
                    .where(
                        AssessmentQuestion.section_id == section.id,
                        AssessmentQuestion.min_age_months <= child_age_months,
                        AssessmentQuestion.max_age_months >= child_age_months
                    )
                )
                total_questions = questions_result.scalar() or 0
                
                # Get count of answered questions
                answered_result = await db.execute(
                    select(func.count(AssessmentQuestionAnswer.id))
                    .where(AssessmentQuestionAnswer.response_id == response.id)
                )
                answered_questions = answered_result.scalar() or 0
                
                # Calculate unanswered from the stored list
                unanswered_questions = len(response.unanswered_questions or [])
                
                # Calculate completion percentage
                completion_pct = (
                    (answered_questions / total_questions * 100)
                    if total_questions > 0
                    else 0.0
                )
                
                section_progress_list.append(SectionProgress(
                    section_id=section.id,
                    section_title=section.title,
                    pool_id=section.pool_id,
                    response_id=response.id,
                    status=response.status.value,
                    total_questions=total_questions,
                    answered_questions=answered_questions,
                    unanswered_questions=unanswered_questions,
                    completion_percentage=round(completion_pct, 2),
                    assessment_language=response.assessment_language,
                    created_at=response.created_at,
                    completed_at=response.completed_at
                ))
                
                # Count by status
                if response.status == AssessmentStatus.NOT_STARTED:
                    sections_not_started += 1
                elif response.status == AssessmentStatus.IN_PROGRESS:
                    sections_in_progress += 1
                elif response.status == AssessmentStatus.COMPLETED:
                    sections_completed += 1
                
                # Add to total completion
                total_completion += completion_pct
        
        # Calculate overall completion percentage
        overall_completion = (
            total_completion / len(all_sections)
            if len(all_sections) > 0
            else 0.0
        )
        
        logger.info(
            "assessment_progress_calculated",
            child_id=child_id,
            total_sections=len(all_sections),
            not_started=sections_not_started,
            in_progress=sections_in_progress,
            completed=sections_completed,
            overall_completion=round(overall_completion, 2)
        )
        
        return AssessmentProgressResponse(
            child_id=child_id,
            total_sections=len(all_sections),
            sections_not_started=sections_not_started,
            sections_in_progress=sections_in_progress,
            sections_completed=sections_completed,
            overall_completion_percentage=round(overall_completion, 2),
            section_progress=section_progress_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "assessment_progress_error",
            child_id=child_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch assessment progress: {str(e)}"
        )
