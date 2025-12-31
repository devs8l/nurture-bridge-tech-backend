"""
Report schemas for AI-generated summaries and final reports.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Pool Summary Schemas
# ============================================================================

class PoolSummaryResponse(BaseModel):
    """Response model for pool summary."""
    id: str
    child_id: str
    pool_id: str
    pool_title: str
    summary_content: dict
    total_sections: int
    completed_sections: int
    total_score: Optional[int] = None
    max_possible_score: Optional[int] = None
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Final Report Schemas
# ============================================================================

class FinalReportResponse(BaseModel):
    """Response model for final report with review status."""
    id: str
    child_id: str
    overall_summary: dict
    total_pools: int
    completed_pools: int
    overall_score: Optional[int] = None
    overall_max_score: Optional[int] = None
    doctor_reviewed_at: Optional[datetime] = None
    hod_reviewed_at: Optional[datetime] = None
    generated_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    is_doctor_reviewed: bool = Field(default=False)
    is_hod_reviewed: bool = Field(default=False)
    is_fully_approved: bool = Field(default=False)

    model_config = {"from_attributes": True}

    def __init__(self, **data):
        super().__init__(**data)
        # Set computed fields based on review timestamps
        self.is_doctor_reviewed = self.doctor_reviewed_at is not None
        self.is_hod_reviewed = self.hod_reviewed_at is not None
        self.is_fully_approved = self.is_doctor_reviewed and self.is_hod_reviewed


class DoctorReviewRequest(BaseModel):
    """Request model for doctor review."""
    notes: Optional[str] = Field(None, description="Optional review notes from doctor")


class HODReviewRequest(BaseModel):
    """Request model for HOD review."""
    notes: Optional[str] = Field(None, description="Optional review notes from HOD")


# ============================================================================
# Report Status Schemas
# ============================================================================

class PoolStatus(BaseModel):
    """Status of a single pool including completion and summary generation."""
    pool_id: str
    pool_title: str
    total_sections: int
    completed_sections: int
    is_complete: bool
    has_summary: bool
    summary_id: Optional[str] = None
    summary_generated_at: Optional[datetime] = None


class ReviewStatus(BaseModel):
    """Review workflow status for final reports."""
    is_generated: bool
    is_doctor_reviewed: bool
    is_hod_reviewed: bool
    is_fully_approved: bool
    doctor_reviewed_at: Optional[datetime] = None
    hod_reviewed_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None


class ReportStatusResponse(BaseModel):
    """Overall report generation status for a child."""
    child_id: str
    pools: List[PoolStatus]
    final_report_status: ReviewStatus
    overall_completion_percentage: float = Field(
        description="Overall assessment completion percentage"
    )
    all_pools_complete: bool
    final_report_id: Optional[str] = None
