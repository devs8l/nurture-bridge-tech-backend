from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.intake import IntakeSection, IntakeQuestion, IntakeResponse, IntakeAnswer, IntakeStatus


class IntakeSectionRepository:
    """Repository for intake sections."""
    
    def __init__(self):
        self.model = IntakeSection
    
    async def create(self, db: AsyncSession, obj: IntakeSection) -> IntakeSection:
        """Create a new section."""
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def get_by_id(self, db: AsyncSession, section_id: str) -> Optional[IntakeSection]:
        """Get section by ID."""
        result = await db.get(IntakeSection, section_id)
        return result
    
    async def get_all(self, db: AsyncSession) -> List[IntakeSection]:
        """Get all sections."""
        stmt = select(IntakeSection).order_by(IntakeSection.order_number)
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, db: AsyncSession, obj: IntakeSection) -> IntakeSection:
        """Update a section."""
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def delete(self, db: AsyncSession, section_id: str) -> None:
        """Delete a section."""
        section = await self.get_by_id(db, section_id)
        if section:
            await db.delete(section)
            await db.commit()
    
    async def get_all_active_with_questions(
        self, 
        db: AsyncSession
    ) -> List[IntakeSection]:
        """Get all active sections with their questions, ordered."""
        stmt = (
            select(IntakeSection)
            .where(IntakeSection.is_active == True)
            .options(selectinload(IntakeSection.questions))
            .order_by(IntakeSection.order_number)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_id_with_questions(
        self,
        db: AsyncSession,
        section_id: str,
        age_in_months: Optional[int] = None
    ) -> Optional[IntakeSection]:
        """Get section by ID with questions, optionally filtered by age."""
        
        stmt = (
            select(IntakeSection)
            .where(IntakeSection.id == section_id)
            .options(selectinload(IntakeSection.questions))
        )
        result = await db.execute(stmt)
        section = result.scalar_one_or_none()
        
        if not section:
            return None
        
        # If no age filter, return as-is
        if age_in_months is None:
            return section
        
        # If age filter is provided, we need to filter questions
        # To avoid SQLAlchemy tracking issues, we'll expunge everything first
        if section.questions:
            # Store the original questions before expunging
            all_questions = list(section.questions)
            
            # Expunge the section and all questions from the session
            db.expunge(section)
            for question in all_questions:
                db.expunge(question)
            
            # Now filter the questions
            filtered_questions = []
            for question in all_questions:
                # Check if question has age_group in options
                if question.options and 'age_group' in question.options:
                    age_group = question.options['age_group']
                    min_age = age_group.get('min_age')
                    max_age = age_group.get('max_age')
                    
                    # Check if age_in_months is within the range
                    if min_age is not None and max_age is not None:
                        if min_age <= age_in_months <= max_age:
                            filtered_questions.append(question)
                    elif min_age is not None and min_age <= age_in_months:
                        filtered_questions.append(question)
                    elif max_age is not None and age_in_months <= max_age:
                        filtered_questions.append(question)
                else:
                    # Include questions without age restrictions
                    filtered_questions.append(question)
            
            # Replace questions with filtered list (safe now that everything is expunged)
            section.questions = filtered_questions
        
        return section


class IntakeQuestionRepository:
    """Repository for intake questions."""
    
    def __init__(self):
        self.model = IntakeQuestion
    
    async def create(self, db: AsyncSession, obj: IntakeQuestion) -> IntakeQuestion:
        """Create a new question."""
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def get_by_id(self, db: AsyncSession, question_id: str) -> Optional[IntakeQuestion]:
        """Get question by ID."""
        result = await db.get(IntakeQuestion, question_id)
        return result
    
    async def update(self, db: AsyncSession, obj: IntakeQuestion) -> IntakeQuestion:
        """Update a question."""
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def delete(self, db: AsyncSession, question_id: str) -> None:
        """Delete a question."""
        question = await self.get_by_id(db, question_id)
        if question:
            await db.delete(question)
            await db.commit()
    
    async def get_by_section(
        self,
        db: AsyncSession,
        section_id: str
    ) -> List[IntakeQuestion]:
        """Get all questions for a section, ordered."""
        stmt = (
            select(IntakeQuestion)
            .where(IntakeQuestion.section_id == section_id)
            .order_by(IntakeQuestion.order_number)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class IntakeResponseRepository:
    """Repository for intake responses."""
    
    def __init__(self):
        self.model = IntakeResponse
    
    async def create(self, db: AsyncSession, obj: IntakeResponse) -> IntakeResponse:
        """Create a new response."""
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def get_by_id(self, db: AsyncSession, response_id: str) -> Optional[IntakeResponse]:
        """Get response by ID."""
        result = await db.get(IntakeResponse, response_id)
        return result
    
    async def update(self, db: AsyncSession, obj: IntakeResponse) -> IntakeResponse:
        """Update a response."""
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def get_by_child(
        self,
        db: AsyncSession,
        child_id: str
    ) -> List[IntakeResponse]:
        """Get all intake responses for a child."""
        stmt = (
            select(IntakeResponse)
            .where(IntakeResponse.child_id == child_id)
            .order_by(IntakeResponse.started_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_id_with_answers(
        self,
        db: AsyncSession,
        response_id: str
    ) -> Optional[IntakeResponse]:
        """Get intake response with all answers."""
        stmt = (
            select(IntakeResponse)
            .where(IntakeResponse.id == response_id)
            .options(selectinload(IntakeResponse.answers))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_in_progress_by_child(
        self,
        db: AsyncSession,
        child_id: str
    ) -> Optional[IntakeResponse]:
        """Get in-progress intake response for a child."""
        stmt = (
            select(IntakeResponse)
            .where(
                IntakeResponse.child_id == child_id,
                IntakeResponse.status == IntakeStatus.IN_PROGRESS
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


class IntakeAnswerRepository:
    """Repository for intake answers."""
    
    def __init__(self):
        self.model = IntakeAnswer
    
    async def create(self, db: AsyncSession, obj: IntakeAnswer) -> IntakeAnswer:
        """Create a new answer."""
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def get_by_id(self, db: AsyncSession, answer_id: str) -> Optional[IntakeAnswer]:
        """Get answer by ID."""
        result = await db.get(IntakeAnswer, answer_id)
        return result
    
    async def get_by_response(
        self,
        db: AsyncSession,
        response_id: str
    ) -> List[IntakeAnswer]:
        """Get all answers for a response."""
        stmt = (
            select(IntakeAnswer)
            .where(IntakeAnswer.response_id == response_id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_response_and_question(
        self,
        db: AsyncSession,
        response_id: str,
        question_id: str
    ) -> Optional[IntakeAnswer]:
        """Get specific answer for a response and question."""
        stmt = (
            select(IntakeAnswer)
            .where(
                IntakeAnswer.response_id == response_id,
                IntakeAnswer.question_id == question_id
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def upsert_answer(
        self,
        db: AsyncSession,
        response_id: str,
        question_id: str,
        raw_answer: Optional[str] = None,
        answer_bucket: Optional[str] = None,
        score: Optional[int] = None
    ) -> IntakeAnswer:
        """Create or update an answer."""
        existing = await self.get_by_response_and_question(db, response_id, question_id)
        
        if existing:
            # Update existing answer
            if raw_answer is not None:
                existing.raw_answer = raw_answer
            if answer_bucket is not None:
                existing.answer_bucket = answer_bucket
            if score is not None:
                existing.score = score
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new answer
            answer = IntakeAnswer(
                response_id=response_id,
                question_id=question_id,
                raw_answer=raw_answer,
                answer_bucket=answer_bucket,
                score=score
            )
            db.add(answer)
            await db.commit()
            await db.refresh(answer)
            return answer
