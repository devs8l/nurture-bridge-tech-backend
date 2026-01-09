"""
Report Service - AI Summary Generation and Management

Handles pool summary and final report generation logic.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from db.models.report import PoolSummary, FinalReport
from db.models.assessment import AssessmentPool, AssessmentSection, AssessmentResponse, AssessmentQuestionAnswer, AssessmentStatus, AssessmentQuestion
from db.models.clinical import Child
from app_logging.logger import get_logger

logger = get_logger(__name__)


class ReportService:
    """Service for managing AI-generated reports and summaries."""

    def __init__(self, ai_service):
        """
        Initialize report service with AI service dependency.
        
        Args:
            ai_service: Instance of GeminiService for AI operations
        """
        self.ai_service = ai_service

    async def check_and_generate_pool_summary(
        self,
        child_id: str,
        pool_id: str,
        db: AsyncSession
    ) -> Optional[PoolSummary]:
        """
        Check if all sections within a pool are completed and generate summary if needed.
        Filters sections to only those with applicable questions for the child's age.
        
        Args:
            child_id: Child ID
            pool_id: Pool ID
            db: Database session
            
        Returns:
            PoolSummary if generated, None if pool not complete or summary already exists
        """
        logger.info(
            "check_pool_summary_generation",
            child_id=child_id,
            pool_id=pool_id
        )

        try:
            # Check if summary already exists
            existing_summary_result = await db.execute(
                select(PoolSummary).where(
                    PoolSummary.child_id == child_id,
                    PoolSummary.pool_id == pool_id
                )
            )
            existing_summary = existing_summary_result.scalar_one_or_none()

            if existing_summary:
                logger.info(
                    "pool_summary_already_exists",
                    child_id=child_id,
                    pool_id=pool_id,
                    summary_id=existing_summary.id
                )
                return None

            # Get child to calculate age
            child = await db.get(Child, child_id)
            if not child:
                logger.warning("child_not_found", child_id=child_id)
                return None
            
            # Calculate child's age in months
            from datetime import date
            today = date.today()
            child_age_months = (today.year - child.date_of_birth.year) * 12 + (today.month - child.date_of_birth.month)

            # Get pool information
            pool_result = await db.execute(
                select(AssessmentPool).where(AssessmentPool.id == pool_id)
            )
            pool = pool_result.scalar_one_or_none()

            if not pool:
                logger.warning("pool_not_found", pool_id=pool_id)
                return None

            # Get all sections in this pool
            sections_result = await db.execute(
                select(AssessmentSection).where(
                    AssessmentSection.pool_id == pool_id,
                    AssessmentSection.is_active == True
                )
            )
            sections = sections_result.scalars().all()

            if not sections:
                logger.warning(
                    "no_sections_in_pool",
                    pool_id=pool_id
                )
                return None

            # NEW: Filter sections to only those with applicable questions for child's age
            applicable_sections = []
            non_applicable_sections = []
            
            for section in sections:
                question_count_result = await db.execute(
                    select(func.count(AssessmentQuestion.id))
                    .where(
                        AssessmentQuestion.section_id == section.id,
                        AssessmentQuestion.min_age_months <= child_age_months,
                        AssessmentQuestion.max_age_months >= child_age_months
                    )
                )
                question_count = question_count_result.scalar() or 0
                
                if question_count > 0:
                    applicable_sections.append(section)
                else:
                    non_applicable_sections.append(section)
            
            logger.info(
                "pool_applicability_check",
                child_id=child_id,
                pool_id=pool_id,
                child_age_months=child_age_months,
                total_sections=len(sections),
                applicable_sections=len(applicable_sections),
                non_applicable_sections=len(non_applicable_sections)
            )

            # Use applicable_sections for completion check
            # If NO applicable sections, generate a "not applicable" summary
            if len(applicable_sections) == 0:
                logger.info(
                    "generating_non_applicable_pool_summary",
                    child_id=child_id,
                    pool_id=pool_id,
                    child_age_months=child_age_months
                )
                
                # Gather minimal data for non-applicable pool
                summary_data = {
                    "pool_id": str(pool.id),
                    "pool_title": pool.title,
                    "pool_description": pool.description,
                    "sections": [],
                    "is_applicable": False,
                    "child_age_months": child_age_months,
                    "total_sections": len(sections),
                    "applicable_sections": 0
                }
                
                # Call AI to generate non-applicable summary
                ai_result = await self.ai_service.generate_pool_summary(
                    pool_data=summary_data,
                    actor=f"system:pool_summary:{pool_id}"
                )
                
                if not ai_result.get("success"):
                    logger.error(
                        "ai_non_applicable_pool_summary_failed",
                        child_id=child_id,
                        pool_id=pool_id,
                        error=ai_result.get("error")
                    )
                    return None
                
                summary_content = ai_result.get("summary", {})
                
                # Create pool summary with zero scores
                pool_summary = PoolSummary(
                    child_id=child_id,
                    pool_id=pool_id,
                    pool_title=pool.title,
                    summary_content=summary_content,
                    total_sections=len(sections),
                    completed_sections=0,  # No sections completed since none applicable
                    total_score=0,
                    max_possible_score=0
                )
                
                db.add(pool_summary)
                await db.commit()
                await db.refresh(pool_summary)
                
                logger.info(
                    "non_applicable_pool_summary_generated",
                    child_id=child_id,
                    pool_id=pool_id,
                    summary_id=pool_summary.id
                )
                
                return pool_summary

            # If there ARE applicable sections, check completion
            total_sections = len(applicable_sections)
            section_ids = [s.id for s in applicable_sections]

            # Check completion status for applicable sections only
            completed_responses_result = await db.execute(
                select(AssessmentResponse).where(
                    AssessmentResponse.child_id == child_id,
                    AssessmentResponse.section_id.in_(section_ids),
                    AssessmentResponse.status == AssessmentStatus.COMPLETED
                )
            )
            completed_responses = completed_responses_result.scalars().all()
            completed_sections = len(completed_responses)

            logger.info(
                "pool_completion_check",
                child_id=child_id,
                pool_id=pool_id,
                total_applicable_sections=total_sections,
                completed_sections=completed_sections
            )

            # Pool not complete yet
            if completed_sections < total_sections:
                logger.info(
                    "pool_not_complete",
                    child_id=child_id,
                    pool_id=pool_id,
                    progress=f"{completed_sections}/{total_sections}"
                )
                return None

            # Pool is complete, generate summary
            logger.info(
                "generating_pool_summary",
                child_id=child_id,
                pool_id=pool_id
            )

            # Gather all data for AI summary (only applicable sections)
            summary_data = await self._gather_pool_data(
                child_id=child_id,
                pool=pool,
                sections=applicable_sections,  # Pass only applicable sections
                responses=completed_responses,
                db=db,
                child_age_months=child_age_months,
                total_sections_in_pool=len(sections),
                non_applicable_sections_count=len(non_applicable_sections)
            )

            # Call AI service to generate pool summary
            ai_result = await self.ai_service.generate_pool_summary(
                pool_data=summary_data,
                actor=f"system:pool_summary:{pool_id}"
            )

            if not ai_result.get("success"):
                logger.error(
                    "ai_pool_summary_failed",
                    child_id=child_id,
                    pool_id=pool_id,
                    error=ai_result.get("error")
                )
                return None

            summary_content = ai_result.get("summary", {})

            # Calculate total scores
            total_score = sum(r.total_score or 0 for r in completed_responses)
            max_possible_score = sum(r.max_possible_score or 0 for r in completed_responses)

            # Create pool summary record
            pool_summary = PoolSummary(
                child_id=child_id,
                pool_id=pool_id,
                pool_title=pool.title,
                summary_content=summary_content,
                total_sections=len(sections),  # Total sections in pool
                completed_sections=completed_sections,  # Completed applicable sections
                total_score=total_score if total_score > 0 else None,
                max_possible_score=max_possible_score if max_possible_score > 0 else None
            )

            db.add(pool_summary)
            await db.commit()
            await db.refresh(pool_summary)

            logger.info(
                "pool_summary_generated",
                child_id=child_id,
                pool_id=pool_id,
                summary_id=pool_summary.id
            )

            return pool_summary

        except Exception as e:
            logger.error(
                "pool_summary_generation_error",
                child_id=child_id,
                pool_id=pool_id,
                error=str(e)
            )
            await db.rollback()
            return None

    async def check_and_generate_final_report(
        self,
        child_id: str,
        db: AsyncSession
    ) -> Optional[FinalReport]:
        """
        Check if all pools have summaries and generate final report if needed.
        
        Args:
            child_id: Child ID
            db: Database session
            
        Returns:
            FinalReport if generated, None if not all pools complete or report already exists
        """
        logger.info(
            "check_final_report_generation",
            child_id=child_id
        )

        try:
            # Check if final report already exists
            existing_report_result = await db.execute(
                select(FinalReport).where(FinalReport.child_id == child_id)
            )
            existing_report = existing_report_result.scalar_one_or_none()

            if existing_report:
                logger.info(
                    "final_report_already_exists",
                    child_id=child_id,
                    report_id=existing_report.id
                )
                return None

            # Get child to calculate age for filtering
            child = await db.get(Child, child_id)
            if not child:
                logger.error("child_not_found", child_id=child_id)
                return None
            
            from datetime import date
            today = date.today()
            child_age_months = (today.year - child.date_of_birth.year) * 12 + (today.month - child.date_of_birth.month)

            # Get all active pools
            all_pools_result = await db.execute(
                select(AssessmentPool).where(AssessmentPool.is_active == True)
            )
            all_pools = all_pools_result.scalars().all()

            # Filter pools to only those with applicable sections for this child's age
            applicable_pools = []
            for pool in all_pools:
                # Get sections in this pool
                sections_result = await db.execute(
                    select(AssessmentSection).where(
                        AssessmentSection.pool_id == pool.id,
                        AssessmentSection.is_active == True
                    )
                )
                pool_sections = sections_result.scalars().all()
                
                # Check if pool has any sections with applicable questions
                has_applicable_section = False
                for section in pool_sections:
                    question_count_result = await db.execute(
                        select(func.count(AssessmentQuestion.id))
                        .where(
                            AssessmentQuestion.section_id == section.id,
                            AssessmentQuestion.min_age_months <= child_age_months,
                            AssessmentQuestion.max_age_months >= child_age_months
                        )
                    )
                    if question_count_result.scalar() > 0:
                        has_applicable_section = True
                        break
                
                if has_applicable_section:
                    applicable_pools.append(pool)
            
            total_pools = len(applicable_pools)

            if total_pools == 0:
                logger.warning("no_applicable_pools_for_child_age", child_age_months=child_age_months)
                return None

            pool_ids = [p.id for p in applicable_pools]

            # Get all pool summaries for this child (only for applicable pools)
            pool_summaries_result = await db.execute(
                select(PoolSummary).where(
                    PoolSummary.child_id == child_id,
                    PoolSummary.pool_id.in_(pool_ids)
                )
            )
            pool_summaries = pool_summaries_result.scalars().all()
            completed_pools = len(pool_summaries)

            logger.info(
                "final_report_completion_check",
                child_id=child_id,
                child_age_months=child_age_months,
                total_pools=total_pools,
                completed_pools=completed_pools,
                pool_ids=pool_ids,
                summary_pool_ids=[ps.pool_id for ps in pool_summaries]
            )

            # Not all applicable pools have summaries yet
            if completed_pools < total_pools:
                logger.warning(
                    "not_all_applicable_pools_complete",
                    child_id=child_id,
                    progress=f"{completed_pools}/{total_pools}",
                    missing_pools=[pid for pid in pool_ids if pid not in [ps.pool_id for ps in pool_summaries]]
                )
                return None

            # All applicable pools complete, generate final report
            logger.info(
                "generating_final_report",
                child_id=child_id
            )

            # Get child info
            child = await db.get(Child, child_id)
            if not child:
                logger.error("child_not_found", child_id=child_id)
                return None

            # Prepare data for AI
            final_report_data = await self._gather_final_report_data(
                child=child,
                pool_summaries=pool_summaries,
                pools=all_pools,
                db=db
            )

            # Calculate child's age in months for clinical context (don't send DOB)
            from datetime import date
            today = date.today()
            age_months = (today.year - child.date_of_birth.year) * 12 + (today.month - child.date_of_birth.month)
            
            # Call AI service to generate final report
            ai_result = await self.ai_service.generate_final_report(
                pool_summaries=[
                    {
                        "pool_title": ps.pool_title,
                        "summary": ps.summary_content,
                        "score_earned": ps.total_score,
                        "max_possible_score": ps.max_possible_score
                    }
                    for ps in pool_summaries
                ],
                child_info={
                    # DO NOT SEND PHI - no names, no DOB
                    "age_months": age_months,  # Only age for clinical context
                    "gender": child.gender.value  # Only gender for clinical context
                },
                actor=f"system:final_report:{child_id}"
            )

            if not ai_result.get("success"):
                logger.error(
                    "ai_final_report_failed",
                    child_id=child_id,
                    error=ai_result.get("error")
                )
                return None

            overall_summary = ai_result.get("summary", {})

            # Calculate overall scores
            overall_score = sum(ps.total_score or 0 for ps in pool_summaries)
            overall_max_score = sum(ps.max_possible_score or 0 for ps in pool_summaries)

            # Create final report record
            final_report = FinalReport(
                child_id=child_id,
                overall_summary=overall_summary,
                total_pools=total_pools,
                completed_pools=completed_pools,
                overall_score=overall_score if overall_score > 0 else None,
                overall_max_score=overall_max_score if overall_max_score > 0 else None
            )

            db.add(final_report)
            await db.commit()
            await db.refresh(final_report)

            logger.info(
                "final_report_generated",
                child_id=child_id,
                report_id=final_report.id
            )

            return final_report

        except Exception as e:
            logger.error(
                "final_report_generation_error",
                child_id=child_id,
                error=str(e)
            )
            await db.rollback()
            return None

    async def get_pool_summary(
        self,
        child_id: str,
        pool_id: str,
        db: AsyncSession
    ) -> Optional[PoolSummary]:
        """Retrieve existing pool summary."""
        result = await db.execute(
            select(PoolSummary).where(
                PoolSummary.child_id == child_id,
                PoolSummary.pool_id == pool_id
            )
        )
        return result.scalar_one_or_none()

    async def get_final_report(
        self,
        child_id: str,
        current_user_role: str,
        db: AsyncSession
    ) -> Optional[FinalReport]:
        """
        Retrieve existing final report with RBAC checks.
        
        Args:
            child_id: Child ID
            current_user_role: Role of current user (DOCTOR or HOD)
            db: Database session
            
        Returns:
            FinalReport if authorized, None otherwise
            
        Raises:
            HTTPException: If report exists but user not authorized to view
        """
        result = await db.execute(
            select(FinalReport).where(FinalReport.child_id == child_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            return None

        # RBAC: Doctors can see any generated report
        if current_user_role == "DOCTOR":
            return report

        # RBAC: HODs can only see doctor-reviewed reports
        if current_user_role == "HOD":
            if report.doctor_reviewed_at is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Report must be reviewed by a doctor before HOD can access it"
                )
            return report

        # Other roles not allowed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view report"
        )

    async def regenerate_pool_summary(
        self,
        child_id: str,
        pool_id: str,
        db: AsyncSession
    ) -> PoolSummary:
        """
        Force regenerate pool summary (overwrites existing).
        
        Args:
            child_id: Child ID
            pool_id: Pool ID
            db: Database session
            
        Returns:
            New PoolSummary
            
        Raises:
            HTTPException: If pool not complete or generation fails
        """
        logger.info(
            "regenerating_pool_summary",
            child_id=child_id,
            pool_id=pool_id
        )

        # Delete existing summary if exists
        await db.execute(
            select(PoolSummary).where(
                PoolSummary.child_id == child_id,
                PoolSummary.pool_id == pool_id
            )
        )
        existing = (await db.execute(
            select(PoolSummary).where(
                PoolSummary.child_id == child_id,
                PoolSummary.pool_id == pool_id
            )
        )).scalar_one_or_none()

        if existing:
            await db.delete(existing)
            await db.commit()

        # Generate new summary
        new_summary = await self.check_and_generate_pool_summary(
            child_id=child_id,
            pool_id=pool_id,
            db=db
        )

        if not new_summary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to regenerate pool summary. Pool may not be complete."
            )

        return new_summary

    async def regenerate_final_report(
        self,
        child_id: str,
        db: AsyncSession
    ) -> FinalReport:
        """
        Force regenerate final report (overwrites existing, resets review timestamps).
        
        Args:
            child_id: Child ID
            db: Database session
            
        Returns:
            New FinalReport
            
        Raises:
            HTTPException: If not all pools complete or generation fails
        """
        logger.info(
            "regenerating_final_report",
            child_id=child_id
        )

        # Delete existing report if exists
        existing = (await db.execute(
            select(FinalReport).where(FinalReport.child_id == child_id)
        )).scalar_one_or_none()

        if existing:
            await db.delete(existing)
            await db.commit()

        # Generate new report
        new_report = await self.check_and_generate_final_report(
            child_id=child_id,
            db=db
        )

        if not new_report:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to regenerate final report. Not all pools may be complete."
            )

        return new_report

    async def mark_doctor_reviewed(
        self,
        report_id: str,
        doctor_id: str,
        notes: Optional[str],
        db: AsyncSession
    ) -> FinalReport:
        """
        Mark report as reviewed by doctor.
        
        Args:
            report_id: Report ID
            doctor_id: Doctor ID performing review
            notes: Optional review notes from doctor
            db: Database session
            
        Returns:
            Updated FinalReport
            
        Raises:
            HTTPException: If report not found or already reviewed
        """
        from app_logging.id_hasher import hash_id
        
        report = await db.get(FinalReport, report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )

        if report.doctor_reviewed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report has already been reviewed by a doctor"
            )

        report.doctor_reviewed_at = datetime.utcnow()
        report.doctor_notes = notes  # Store the notes
        await db.commit()
        await db.refresh(report)

        logger.info(
            "doctor_reviewed_report",
            report_id_hash=hash_id(report_id),
            doctor_id_hash=hash_id(doctor_id),
            child_id_hash=hash_id(report.child_id),
            has_notes=bool(notes)
        )

        return report

    async def mark_hod_reviewed(
        self,
        report_id: str,
        hod_id: str,
        notes: Optional[str],
        db: AsyncSession
    ) -> FinalReport:
        """
        Mark report as reviewed by HOD (final sign-off).
        
        Args:
            report_id: Report ID
            hod_id: HOD ID performing review
            notes: Optional review notes from HOD
            db: Database session
            
        Returns:
            Updated FinalReport
            
        Raises:
            HTTPException: If report not found, not doctor-reviewed, or already HOD-reviewed
        """
        from app_logging.id_hasher import hash_id
        
        report = await db.get(FinalReport, report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )

        if report.doctor_reviewed_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report must be reviewed by a doctor before HOD review"
            )

        if report.hod_reviewed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report has already been reviewed by an HOD"
            )

        report.hod_reviewed_at = datetime.utcnow()
        report.hod_notes = notes  # Store the notes
        await db.commit()
        await db.refresh(report)

        logger.info(
            "hod_reviewed_report",
            report_id_hash=hash_id(report_id),
            hod_id_hash=hash_id(hod_id),
            child_id_hash=hash_id(report.child_id),
            has_notes=bool(notes)
        )

        return report

    async def get_pending_hod_reviews(
        self,
        tenant_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Get all reports that are doctor-reviewed but not HOD-reviewed for a tenant.
        
        Args:
            tenant_id: Tenant ID to filter reports
            db: Database session
            
        Returns:
            List of pending review data with child, parent, and doctor info
        """
        from db.models.clinical import Child, Parent, Doctor
        
        # Query for reports that are doctor-reviewed but not HOD-reviewed
        # Join with child, parent, and doctor to get complete information
        query = (
            select(FinalReport, Child, Parent, Doctor)
            .join(Child, FinalReport.child_id == Child.id)
            .join(Parent, Child.parent_id == Parent.id)
            .join(Doctor, Parent.assigned_doctor_id == Doctor.id)
            .where(
                Child.tenant_id == tenant_id,
                FinalReport.doctor_reviewed_at.isnot(None),
                FinalReport.hod_reviewed_at.is_(None)
            )
            .order_by(FinalReport.doctor_reviewed_at.desc())
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        pending_reviews = []
        for report, child, parent, doctor in rows:
            pending_reviews.append({
                "report_id": str(report.id),
                "child_id": str(child.id),
                "child_first_name": child.first_name,
                "child_last_name": child.last_name,
                "child_date_of_birth": child.date_of_birth.isoformat(),
                "parent_id": str(parent.id),
                "parent_first_name": parent.first_name,
                "parent_last_name": parent.last_name,
                "generated_at": report.generated_at,
                "doctor_reviewed_at": report.doctor_reviewed_at,
                "doctor_id": str(doctor.id),
                "doctor_first_name": doctor.first_name,
                "doctor_last_name": doctor.last_name
            })
        
        logger.info(
            "pending_hod_reviews_fetched",
            tenant_id=tenant_id,
            count=len(pending_reviews)
        )
        
        return pending_reviews

    # Helper methods
    async def _gather_pool_data(
        self,
        child_id: str,
        pool: AssessmentPool,
        sections: List[AssessmentSection],
        responses: List[AssessmentResponse],
        db: AsyncSession,
        child_age_months: int = None,
        total_sections_in_pool: int = None,
        non_applicable_sections_count: int = 0
    ) -> Dict[str, Any]:
        """
        Gather all data for pool summary generation.
        
        TODO: PHI-LEAK-FIX (H-001) - Redact child names and identifying information
        from assessment answers before sending to AI. Currently sends raw answers
        which may contain child names mentioned during conversations.
        """
        from db.models.assessment import AssessmentQuestion
        
        pool_data = {
            "pool_id": str(pool.id),
            "pool_title": pool.title,
            "pool_description": pool.description,
            "sections": [],
            "is_applicable": True,  # Default to True, will be False only if explicitly set
            "child_age_months": child_age_months,
            "total_sections_in_pool": total_sections_in_pool or len(sections),
            "applicable_sections_count": len(sections),
            "non_applicable_sections_count": non_applicable_sections_count
        }

        for section in sections:
            # Find corresponding response
            response = next((r for r in responses if r.section_id == section.id), None)
            if not response:
                continue

            # Get all answers for this response with question details
            answers_result = await db.execute(
                select(AssessmentQuestionAnswer, AssessmentQuestion)
                .join(AssessmentQuestion, AssessmentQuestionAnswer.question_id == AssessmentQuestion.id)
                .where(AssessmentQuestionAnswer.response_id == response.id)
            )
            answer_question_pairs = answers_result.all()

            section_data = {
                "section_id": str(section.id),
                "section_title": section.title,
                "section_description": section.description,
                "total_score": response.total_score,
                "max_possible_score": response.max_possible_score,
                "answers": [
                    {
                        "question": question.text,  # Include question text for context
                        "answer": ans.translated_answer or ans.raw_answer,  # Only translated answer
                        "answer_bucket": ans.answer_bucket,
                        "score": ans.score
                    }
                    for ans, question in answer_question_pairs
                ]
            }
            pool_data["sections"].append(section_data)

        return pool_data

    async def _gather_final_report_data(
        self,
        child: Child,
        pool_summaries: List[PoolSummary],
        pools: List[AssessmentPool],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Gather all data for final report generation."""
        return {
            "child": {
                "id": str(child.id),
                "first_name": child.first_name,
                "last_name": child.last_name,
                "date_of_birth": str(child.date_of_birth),
                "gender": child.gender.value
            },
            "pool_summaries": [
                {
                    "pool_id": str(ps.pool_id),
                    "pool_title": ps.pool_title,
                    "summary_content": ps.summary_content,
                    "total_score": ps.total_score,
                    "max_possible_score": ps.max_possible_score
                }
                for ps in pool_summaries
            ]
        }
