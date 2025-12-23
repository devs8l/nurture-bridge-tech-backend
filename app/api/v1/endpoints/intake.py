from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app_logging.logger import get_logger
from app.api.deps import get_db, get_current_user
from app.services.intake_service import IntakeService
from app.schemas.intake import (
    IntakeSectionCreate, IntakeSectionUpdate, IntakeSectionResponse, IntakeSectionWithQuestions,
    IntakeQuestionCreate, IntakeQuestionUpdate, IntakeQuestionResponse,
    IntakeResponseCreate, IntakeResponseUpdate, IntakeResponseResponse, IntakeResponseWithAnswers,
    IntakeAnswerCreate, IntakeAnswerResponse, BulkAnswerCreate,
    IntakeFormStructure
)
from db.models.auth import User, UserRole

logger = get_logger(__name__)
router = APIRouter()



def caclucateAgeWithDOB(dob):
    # Calculate age in months with DOB
    today = date.today()
    age_in_months = (today.year - dob.year) * 12 + (today.month - dob.month)
    return age_in_months


# ============================================================================
# SECTION ENDPOINTS
# ============================================================================

@router.post("/sections", response_model=IntakeSectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    section_data: IntakeSectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new intake section.
    Role: TENANT_ADMIN.
    """
    if current_user.role not in [UserRole.TENANT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can create sections"
        )
    
    service = IntakeService()
    section = await service.create_section(db, section_data)
    return section


@router.get("/sections", response_model=List[IntakeSectionResponse])
async def get_all_sections(
    active_only: bool = Query(False, description="Return only active sections"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all intake sections.
    Role: All authenticated users.
    """
    service = IntakeService()
    sections = await service.get_all_sections(db, active_only=active_only)
    return sections


@router.get("/sections/{section_id}", response_model=IntakeSectionWithQuestions)
async def get_section(
    section_id: UUID,
    age_in_months: int = Query(None, description="Filter questions by child's age in months"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific section with its questions.
    Optionally filter questions by age using age_in_months parameter.
    Role: All authenticated users.
    """
    service = IntakeService()
    section = await service.get_section_with_questions(db, str(section_id), age_in_months=age_in_months)
    return section


@router.patch("/sections/{section_id}", response_model=IntakeSectionResponse)
async def update_section(
    section_id: UUID,
    section_data: IntakeSectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an intake section.
    Role: ADMIN, HOD only.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and HODs can update sections"
        )
    
    service = IntakeService()
    section = await service.update_section(db, str(section_id), section_data)
    return section


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (deactivate) an intake section.
    Role: ADMIN, HOD only.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and HODs can delete sections"
        )
    
    service = IntakeService()
    await service.delete_section(db, str(section_id))
    return None


# ============================================================================
# QUESTION ENDPOINTS
# ============================================================================

@router.post("/questions", response_model=IntakeQuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: IntakeQuestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new intake question.
    Role: ADMIN, HOD only.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and HODs can create questions"
        )
    
    service = IntakeService()
    question = await service.create_question(db, question_data)
    return question


@router.get("/sections/{section_id}/questions", response_model=List[IntakeQuestionResponse])
async def get_section_questions(
    section_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all questions for a section.
    Role: All authenticated users.
    """
    service = IntakeService()
    questions = await service.get_questions_by_section(db, str(section_id))
    return questions


@router.get("/questions/{question_id}", response_model=IntakeQuestionResponse)
async def get_question(
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific question.
    Role: All authenticated users.
    """
    service = IntakeService()
    question = await service.get_question(db, str(question_id))
    return question


@router.patch("/questions/{question_id}", response_model=IntakeQuestionResponse)
async def update_question(
    question_id: UUID,
    question_data: IntakeQuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an intake question.
    Role: ADMIN, HOD only.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and HODs can update questions"
        )
    
    service = IntakeService()
    question = await service.update_question(db, str(question_id), question_data)
    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an intake question.
    Role: ADMIN, HOD only.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and HODs can delete questions"
        )
    
    service = IntakeService()
    await service.delete_question(db, str(question_id))
    return None


# ============================================================================
# RESPONSE ENDPOINTS (for filling out intake forms)
# ============================================================================

@router.post("/responses", response_model=IntakeResponseResponse, status_code=status.HTTP_201_CREATED)
async def create_response(
    response_data: IntakeResponseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new intake response for a child.
    Role: DOCTOR, PARENT, RECEPTIONIST.
    """
    if current_user.role not in [UserRole.DOCTOR, UserRole.PARENT, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors, parents, and receptionists can create intake responses"
        )
    
    service = IntakeService()
    response = await service.create_response(db, response_data, str(current_user.tenant_id))
    return response


@router.get("/responses/{response_id}", response_model=IntakeResponseWithAnswers)
async def get_response(
    response_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get an intake response with all answers.
    Role: DOCTOR, PARENT, RECEPTIONIST, HOD.
    """
    if current_user.role not in [UserRole.DOCTOR, UserRole.PARENT, UserRole.RECEPTIONIST, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = IntakeService()
    response = await service.get_response_with_answers(db, str(response_id))
    return response


@router.get("/children/{child_id}/responses", response_model=List[IntakeResponseResponse])
async def get_child_responses(
    child_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all intake responses for a child.
    Role: DOCTOR, PARENT, RECEPTIONIST, HOD.
    """
    if current_user.role not in [UserRole.DOCTOR, UserRole.PARENT, UserRole.RECEPTIONIST, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = IntakeService()
    responses = await service.get_responses_by_child(db, str(child_id))
    return responses


@router.patch("/responses/{response_id}", response_model=IntakeResponseResponse)
async def update_response(
    response_id: UUID,
    response_data: IntakeResponseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an intake response (usually to mark as completed).
    Role: DOCTOR, PARENT, RECEPTIONIST.
    """
    if current_user.role not in [UserRole.DOCTOR, UserRole.PARENT, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors, parents, and receptionists can update responses"
        )
    
    service = IntakeService()
    response = await service.update_response(db, str(response_id), response_data)
    return response


# ============================================================================
# ANSWER ENDPOINTS
# ============================================================================

@router.post("/responses/{response_id}/answers", response_model=IntakeAnswerResponse, status_code=status.HTTP_201_CREATED)
async def save_answer(
    response_id: UUID,
    answer_data: IntakeAnswerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save or update a single answer.
    Role: DOCTOR, PARENT, RECEPTIONIST.
    """
    if current_user.role not in [UserRole.DOCTOR, UserRole.PARENT, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors, parents, and receptionists can save answers"
        )
    
    service = IntakeService()
    answer = await service.save_answer(db, str(response_id), answer_data)
    return answer


@router.post("/responses/{response_id}/answers/bulk", response_model=List[IntakeAnswerResponse])
async def save_bulk_answers(
    response_id: UUID,
    answers: List[IntakeAnswerCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save or update multiple answers at once.
    Role: DOCTOR, PARENT, RECEPTIONIST.
    """
    if current_user.role not in [UserRole.DOCTOR, UserRole.PARENT, UserRole.RECEPTIONIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors, parents, and receptionists can save answers"
        )
    
    service = IntakeService()
    saved_answers = await service.save_bulk_answers(db, str(response_id), answers)
    return saved_answers


@router.get("/responses/{response_id}/answers", response_model=List[IntakeAnswerResponse])
async def get_response_answers(
    response_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all answers for a response.
    Role: DOCTOR, PARENT, RECEPTIONIST, HOD.
    """
    if current_user.role not in [UserRole.DOCTOR, UserRole.PARENT, UserRole.RECEPTIONIST, UserRole.HOD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = IntakeService()
    answers = await service.get_answers_by_response(db, str(response_id))
    return answers


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/form-structure", response_model=List[IntakeSectionWithQuestions])
async def get_intake_form_structure(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete intake form structure with all sections and questions.
    This is useful for rendering the entire form on the frontend.
    Role: All authenticated users.
    """
    service = IntakeService()
    structure = await service.get_intake_form_structure(db)
    return structure
