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
from db.models.assessment import AssessmentPool, AssessmentSection, AssessmentResponse, AssessmentQuestionAnswer, AssessmentStatus
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

            total_sections = len(sections)
            section_ids = [s.id for s in sections]

            # Check completion status for all sections
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
                total_sections=total_sections,
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

            # Gather all data for AI summary
            summary_data = await self._gather_pool_data(
                child_id=child_id,
                pool=pool,
                sections=sections,
                responses=completed_responses,
                db=db
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
                total_sections=total_sections,
                completed_sections=completed_sections,
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

            # Get all active pools
            all_pools_result = await db.execute(
                select(AssessmentPool).where(AssessmentPool.is_active == True)
            )
            all_pools = all_pools_result.scalars().all()
            total_pools = len(all_pools)

            if total_pools == 0:
                logger.warning("no_active_pools")
                return None

            pool_ids = [p.id for p in all_pools]

            # Get all pool summaries for this child
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
                total_pools=total_pools,
                completed_pools=completed_pools
            )

            # Not all pools have summaries yet
            if completed_pools < total_pools:
                logger.info(
                    "not_all_pools_complete",
                    child_id=child_id,
                    progress=f"{completed_pools}/{total_pools}"
                )
                return None

            # All pools complete, generate final report
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
        db: AsyncSession
    ) -> FinalReport:
        """
        Mark report as reviewed by doctor.
        
        Args:
            report_id: Report ID
            doctor_id: Doctor ID performing review
            db: Database session
            
        Returns:
            Updated FinalReport
            
        Raises:
            HTTPException: If report not found or already reviewed
        """
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
        await db.commit()
        await db.refresh(report)

        logger.info(
            "doctor_reviewed_report",
            report_id=report_id,
            doctor_id=doctor_id,
            child_id=report.child_id
        )

        return report

    async def mark_hod_reviewed(
        self,
        report_id: str,
        hod_id: str,
        db: AsyncSession
    ) -> FinalReport:
        """
        Mark report as reviewed by HOD (final sign-off).
        
        Args:
            report_id: Report ID
            hod_id: HOD ID performing review
            db: Database session
            
        Returns:
            Updated FinalReport
            
        Raises:
            HTTPException: If report not found, not doctor-reviewed, or already HOD-reviewed
        """
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
        await db.commit()
        await db.refresh(report)

        logger.info(
            "hod_reviewed_report",
            report_id=report_id,
            hod_id=hod_id,
            child_id=report.child_id
        )

        return report

    # Helper methods
    async def _gather_pool_data(
        self,
        child_id: str,
        pool: AssessmentPool,
        sections: List[AssessmentSection],
        responses: List[AssessmentResponse],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Gather all data for pool summary generation."""
        from db.models.assessment import AssessmentQuestion
        
        pool_data = {
            "pool_id": str(pool.id),
            "pool_title": pool.title,
            "pool_description": pool.description,
            "sections": []
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
