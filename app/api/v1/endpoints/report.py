"""
Report API endpoints for AI-generated summaries and final reports.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.report import (
    PoolSummaryResponse,
    FinalReportResponse,
    DoctorReviewRequest,
    HODReviewRequest,
    ReportStatusResponse,
    PoolStatus,
    ReviewStatus
)
from db.models.report import PoolSummary, FinalReport
from db.models.assessment import AssessmentPool, AssessmentSection, AssessmentResponse, AssessmentStatus
from db.base import get_db
from app.services.report_service import ReportService
from app_logging.logger import get_logger
from sqlalchemy import select, func

logger = get_logger(__name__)
router = APIRouter()


# Dependency to get report service
def get_report_service():
    """Get report service with AI service dependency."""
    from app.main import get_gemini_service
    ai_service = get_gemini_service()
    return ReportService(ai_service)


# ============================================================================
# POOL SUMMARY ENDPOINTS
# ============================================================================

@router.get("/pool/{child_id}/{pool_id}", response_model=PoolSummaryResponse)
async def get_pool_summary(
    child_id: str,
    pool_id: str,
    db: AsyncSession = Depends(get_db),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Get pool summary for a child and pool.
    
    RBAC: Doctor, HOD
    """
    logger.info("get_pool_summary_request", child_id=child_id, pool_id=pool_id)
    
    summary = await report_service.get_pool_summary(
        child_id=child_id,
        pool_id=pool_id,
        db=db
    )
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pool summary not found for child {child_id} and pool {pool_id}"
        )
    
    return summary


@router.post("/pool/{child_id}/{pool_id}/regenerate", response_model=PoolSummaryResponse)
async def regenerate_pool_summary(
    child_id: str,
    pool_id: str,
    db: AsyncSession = Depends(get_db),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Force regenerate pool summary (overwrites existing).
    
    RBAC: Admin, Doctor only
    """
    logger.info("regenerate_pool_summary_request", child_id=child_id, pool_id=pool_id)
    
    summary = await report_service.regenerate_pool_summary(
        child_id=child_id,
        pool_id=pool_id,
        db=db
    )
    
    return summary


# ============================================================================
# FINAL REPORT ENDPOINTS
# ============================================================================

@router.get("/final/{child_id}", response_model=FinalReportResponse)
async def get_final_report(
    child_id: str,
    current_user_role: str = "DOCTOR",  # TODO: Get from auth context
    db: AsyncSession = Depends(get_db),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Get final report for a child.
    
    RBAC:
    - Doctors can see any generated report
    - HODs can only see doctor-reviewed reports
    """
    logger.info("get_final_report_request", child_id=child_id, role=current_user_role)
    
    report = await report_service.get_final_report(
        child_id=child_id,
        current_user_role=current_user_role,
        db=db
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Final report not found for child {child_id}"
        )
    
    return report


@router.post("/final/{child_id}/regenerate", response_model=FinalReportResponse)
async def regenerate_final_report(
    child_id: str,
    db: AsyncSession = Depends(get_db),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Force regenerate final report (overwrites existing, resets review timestamps).
    
    RBAC: Admin, Doctor only
    """
    logger.info("regenerate_final_report_request", child_id=child_id)
    
    report = await report_service.regenerate_final_report(
        child_id=child_id,
        db=db
    )
    
    return report


@router.post("/final/{report_id}/doctor-review", response_model=FinalReportResponse)
async def doctor_review_report(
    report_id: str,
    review_request: DoctorReviewRequest,
    doctor_id: str = "current_doctor_id",  # TODO: Get from auth context
    db: AsyncSession = Depends(get_db),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Doctor marks report as reviewed.
    
    RBAC: Doctor only
    """
    logger.info(
        "doctor_review_request",
        report_id=report_id,
        doctor_id=doctor_id,
        has_notes=bool(review_request.notes)
    )
    
    report = await report_service.mark_doctor_reviewed(
        report_id=report_id,
        doctor_id=doctor_id,
        db=db
    )
    
    return report


@router.post("/final/{report_id}/hod-review", response_model=FinalReportResponse)
async def hod_review_report(
    report_id: str,
    review_request: HODReviewRequest,
    hod_id: str = "current_hod_id",  # TODO: Get from auth context
    db: AsyncSession = Depends(get_db),
    report_service: ReportService = Depends(get_report_service)
):
    """
    HOD marks report as reviewed (final sign-off).
    
    RBAC: HOD only
    Requires doctor review to be complete.
    """
    logger.info(
        "hod_review_request",
        report_id=report_id,
        hod_id=hod_id,
        has_notes=bool(review_request.notes)
    )
    
    report = await report_service.mark_hod_reviewed(
        report_id=report_id,
        hod_id=hod_id,
        db=db
    )
    
    return report


# ============================================================================
# REPORT STATUS ENDPOINT
# ============================================================================

@router.get("/status/{child_id}", response_model=ReportStatusResponse)
async def get_report_status(
    child_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall report generation status for a child.
    
    Returns:
    - List of pools with completion status and summary status
    - Final report status (generated, doctor reviewed, HOD reviewed)
    - Overall completion percentage
    
    RBAC: Doctor, HOD
    """
    logger.info("get_report_status_request", child_id=child_id)
    
    try:
        # Get all active pools
        all_pools_result = await db.execute(
            select(AssessmentPool).where(AssessmentPool.is_active == True)
            .order_by(AssessmentPool.order_number)
        )
        all_pools = all_pools_result.scalars().all()
        
        # Get pool summaries for this child
        pool_summaries_result = await db.execute(
            select(PoolSummary).where(PoolSummary.child_id == child_id)
        )
        pool_summaries = pool_summaries_result.scalars().all()
        pool_summaries_map = {ps.pool_id: ps for ps in pool_summaries}
        
        # Build pool status list
        pool_status_list = []
        total_completion = 0.0
        
        for pool in all_pools:
            # Get sections in this pool
            sections_result = await db.execute(
                select(AssessmentSection).where(
                    AssessmentSection.pool_id == pool.id,
                    AssessmentSection.is_active == True
                )
            )
            sections = sections_result.scalars().all()
            total_sections = len(sections)
            
            if total_sections == 0:
                continue
            
            section_ids = [s.id for s in sections]
            
            # Get completed responses for this pool
            completed_responses_result = await db.execute(
                select(AssessmentResponse).where(
                    AssessmentResponse.child_id == child_id,
                    AssessmentResponse.section_id.in_(section_ids),
                    AssessmentResponse.status == AssessmentStatus.COMPLETED
                )
            )
            completed_responses = completed_responses_result.scalars().all()
            completed_sections = len(completed_responses)
            
            is_complete = completed_sections == total_sections
            pool_summary = pool_summaries_map.get(pool.id)
            
            pool_status_list.append(PoolStatus(
                pool_id=pool.id,
                pool_title=pool.title,
                total_sections=total_sections,
                completed_sections=completed_sections,
                is_complete=is_complete,
                has_summary=pool_summary is not None,
                summary_id=str(pool_summary.id) if pool_summary else None,
                summary_generated_at=pool_summary.generated_at if pool_summary else None
            ))
            
            # Calculate completion percentage
            if total_sections > 0:
                total_completion += (completed_sections / total_sections) * 100
        
        # Calculate overall completion
        overall_completion = (
            total_completion / len(all_pools) if len(all_pools) > 0 else 0.0
        )
        
        # Check if all pools have summaries
        all_pools_complete = all(ps.has_summary for ps in pool_status_list)
        
        # Get final report
        final_report_result = await db.execute(
            select(FinalReport).where(FinalReport.child_id == child_id)
        )
        final_report = final_report_result.scalar_one_or_none()
        
        # Build review status
        if final_report:
            review_status = ReviewStatus(
                is_generated=True,
                is_doctor_reviewed=final_report.doctor_reviewed_at is not None,
                is_hod_reviewed=final_report.hod_reviewed_at is not None,
                is_fully_approved=(
                    final_report.doctor_reviewed_at is not None and
                    final_report.hod_reviewed_at is not None
                ),
                doctor_reviewed_at=final_report.doctor_reviewed_at,
                hod_reviewed_at=final_report.hod_reviewed_at,
                generated_at=final_report.generated_at
            )
        else:
            review_status = ReviewStatus(
                is_generated=False,
                is_doctor_reviewed=False,
                is_hod_reviewed=False,
                is_fully_approved=False
            )
        
        logger.info(
            "report_status_calculated",
            child_id=child_id,
            total_pools=len(all_pools),
            pools_with_summaries=len(pool_summaries),
            all_pools_complete=all_pools_complete,
            final_report_exists=final_report is not None
        )
        
        return ReportStatusResponse(
            child_id=child_id,
            pools=pool_status_list,
            final_report_status=review_status,
            overall_completion_percentage=round(overall_completion, 2),
            all_pools_complete=all_pools_complete,
            final_report_id=str(final_report.id) if final_report else None
        )
        
    except Exception as e:
        logger.error(
            "report_status_error",
            child_id=child_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report status: {str(e)}"
        )
