from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app_logging.logger import get_logger
from app.repositories.intake_repo import (
    IntakeSectionRepository,
    IntakeQuestionRepository,
    IntakeResponseRepository,
    IntakeAnswerRepository
)
from app.schemas.intake import (
    IntakeSectionCreate, IntakeSectionUpdate,
    IntakeQuestionCreate, IntakeQuestionUpdate,
    IntakeResponseCreate, IntakeResponseUpdate,
    IntakeAnswerCreate, IntakeAnswerUpdate
)
from db.models.intake import IntakeSection, IntakeQuestion, IntakeResponse, IntakeAnswer, IntakeStatus

logger = get_logger(__name__)


class IntakeService:
    """Service for intake operations."""
    
    def __init__(self):
        self.section_repo = IntakeSectionRepository()
        self.question_repo = IntakeQuestionRepository()
        self.response_repo = IntakeResponseRepository()
        self.answer_repo = IntakeAnswerRepository()
    
    # ========================================================================
    # SECTION OPERATIONS
    # ========================================================================
    
    async def create_section(
        self,
        db: AsyncSession,
        section_data: IntakeSectionCreate
    ) -> IntakeSection:
        """Create a new intake section."""
        section = IntakeSection(**section_data.model_dump())
        return await self.section_repo.create(db, section)
    
    async def get_section(
        self,
        db: AsyncSession,
        section_id: str
    ) -> IntakeSection:
        """Get section by ID."""
        section = await self.section_repo.get_by_id(db, section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        return section
    
    async def get_section_with_questions(
        self,
        db: AsyncSession,
        section_id: str
    ) -> IntakeSection:
        """Get section with its questions."""
        section = await self.section_repo.get_by_id_with_questions(db, section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        return section
    
    async def get_all_sections(
        self,
        db: AsyncSession,
        active_only: bool = False
    ) -> List[IntakeSection]:
        """Get all sections."""
        if active_only:
            return await self.section_repo.get_all_active_with_questions(db)
        return await self.section_repo.get_all(db)
    
    async def update_section(
        self,
        db: AsyncSession,
        section_id: str,
        section_data: IntakeSectionUpdate
    ) -> IntakeSection:
        """Update a section."""
        section = await self.get_section(db, section_id)
        update_data = section_data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(section, key, value)
        
        return await self.section_repo.update(db, section)
    
    async def delete_section(
        self,
        db: AsyncSession,
        section_id: str
    ) -> None:
        """Delete a section (soft delete by setting is_active=False)."""
        section = await self.get_section(db, section_id)
        section.is_active = False
        await self.section_repo.update(db, section)
    
    # ========================================================================
    # QUESTION OPERATIONS
    # ========================================================================
    
    async def create_question(
        self,
        db: AsyncSession,
        question_data: IntakeQuestionCreate
    ) -> IntakeQuestion:
        """Create a new intake question."""
        # Verify section exists
        await self.get_section(db, str(question_data.section_id))
        
        question = IntakeQuestion(**question_data.model_dump())
        return await self.question_repo.create(db, question)
    
    async def get_question(
        self,
        db: AsyncSession,
        question_id: str
    ) -> IntakeQuestion:
        """Get question by ID."""
        question = await self.question_repo.get_by_id(db, question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        return question
    
    async def get_questions_by_section(
        self,
        db: AsyncSession,
        section_id: str
    ) -> List[IntakeQuestion]:
        """Get all questions for a section."""
        return await self.question_repo.get_by_section(db, section_id)
    
    async def update_question(
        self,
        db: AsyncSession,
        question_id: str,
        question_data: IntakeQuestionUpdate
    ) -> IntakeQuestion:
        """Update a question."""
        question = await self.get_question(db, question_id)
        update_data = question_data.model_dump(exclude_unset=True)
        
        # Verify section exists if updating section_id
        if "section_id" in update_data:
            await self.get_section(db, update_data["section_id"])
        
        for key, value in update_data.items():
            setattr(question, key, value)
        
        return await self.question_repo.update(db, question)
    
    async def delete_question(
        self,
        db: AsyncSession,
        question_id: str
    ) -> None:
        """Delete a question."""
        question = await self.get_question(db, question_id)
        await self.question_repo.delete(db, str(question.id))
    
    # ========================================================================
    # RESPONSE OPERATIONS
    # ========================================================================
    
    async def create_response(
        self,
        db: AsyncSession,
        response_data: IntakeResponseCreate,
        tenant_id: str
    ) -> IntakeResponse:
        """Create a new intake response for a child."""
        # Check if there's already an in-progress response for this child
        existing = await self.response_repo.get_in_progress_by_child(
            db, str(response_data.child_id)
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An in-progress intake response already exists for this child"
            )
        
        response = IntakeResponse(
            child_id=str(response_data.child_id),
            status=IntakeStatus.IN_PROGRESS
        )
        return await self.response_repo.create(db, response)
    
    async def get_response(
        self,
        db: AsyncSession,
        response_id: str
    ) -> IntakeResponse:
        """Get response by ID."""
        response = await self.response_repo.get_by_id(db, response_id)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intake response not found"
            )
        return response
    
    async def get_response_with_answers(
        self,
        db: AsyncSession,
        response_id: str
    ) -> IntakeResponse:
        """Get response with all answers."""
        response = await self.response_repo.get_by_id_with_answers(db, response_id)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intake response not found"
            )
        return response
    
    async def get_responses_by_child(
        self,
        db: AsyncSession,
        child_id: str
    ) -> List[IntakeResponse]:
        """Get all responses for a child."""
        return await self.response_repo.get_by_child(db, child_id)
    
    async def update_response(
        self,
        db: AsyncSession,
        response_id: str,
        response_data: IntakeResponseUpdate
    ) -> IntakeResponse:
        """Update response status."""
        response = await self.get_response(db, response_id)
        
        if response_data.status:
            response.status = response_data.status
            
            # Set completed_at if status is COMPLETED
            if response_data.status == IntakeStatus.COMPLETED and not response.completed_at:
                response.completed_at = datetime.utcnow()
        
        if response_data.completed_at:
            response.completed_at = response_data.completed_at
        
        return await self.response_repo.update(db, response)
    
    # ========================================================================
    # ANSWER OPERATIONS
    # ========================================================================
    
    async def save_answer(
        self,
        db: AsyncSession,
        response_id: str,
        answer_data: IntakeAnswerCreate
    ) -> IntakeAnswer:
        """Save or update an answer."""
        # Verify response exists
        await self.get_response(db, response_id)
        
        # Verify question exists
        await self.get_question(db, str(answer_data.question_id))
        
        return await self.answer_repo.upsert_answer(
            db=db,
            response_id=response_id,
            question_id=str(answer_data.question_id),
            raw_answer=answer_data.raw_answer,
            answer_bucket=answer_data.answer_bucket,
            score=answer_data.score
        )
    
    async def save_bulk_answers(
        self,
        db: AsyncSession,
        response_id: str,
        answers: List[IntakeAnswerCreate]
    ) -> List[IntakeAnswer]:
        """Save or update multiple answers at once."""
        # Verify response exists
        await self.get_response(db, response_id)
        
        saved_answers = []
        for answer_data in answers:
            answer = await self.save_answer(db, response_id, answer_data)
            saved_answers.append(answer)
        
        return saved_answers
    
    async def get_answers_by_response(
        self,
        db: AsyncSession,
        response_id: str
    ) -> List[IntakeAnswer]:
        """Get all answers for a response."""
        return await self.answer_repo.get_by_response(db, response_id)
    
    # ========================================================================
    # FORM STRUCTURE
    # ========================================================================
    
    async def get_intake_form_structure(
        self,
        db: AsyncSession
    ) -> List[IntakeSection]:
        """Get complete intake form structure with all sections and questions."""
        return await self.section_repo.get_all_active_with_questions(db)
