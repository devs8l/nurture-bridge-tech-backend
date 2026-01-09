from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import Field, model_validator

from app.schemas.base import BaseSchema
from db.models.clinical import Gender
from db.models.auth import UserStatus

# ============================================================================
# DOCTOR SCHEMAS
# ============================================================================

class DoctorUpdate(BaseSchema):
    """
    Schema for updating doctor profile.
    Doctor can update their department and license number.
    License number is optional and can be set later by HOD/Admin.
    """
    department: Optional[str] = Field(None, max_length=255)
    license_number: Optional[str] = Field(None, max_length=100)

class DoctorResponse(BaseSchema):
    """
    Schema for doctor profile response.
    """
    id: UUID
    user_id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    license_number: Optional[str] = None
    department: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# HOD SCHEMAS
# ============================================================================

class HODUpdate(BaseSchema):
    """
    Schema for updating HOD profile.
    HOD can update their department.
    """
    department: Optional[str] = Field(None, max_length=255)

class HODResponse(BaseSchema):
    """
    Schema for HOD profile response.
    """
    id: UUID
    user_id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    department: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# RECEPTIONIST SCHEMAS
# ============================================================================

class ReceptionistUpdate(BaseSchema):
    """
    Schema for updating receptionist profile.
    Receptionist can update their department.
    """
    department: Optional[str] = Field(None, max_length=255)

class ReceptionistResponse(BaseSchema):
    """
    Schema for receptionist profile response.
    """
    id: UUID
    user_id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    department: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# PARENT SCHEMAS
# ============================================================================

class ParentUpdate(BaseSchema):
    """
    Schema for updating parent profile.
    Parents can only update their phone number.
    NOTE: assigned_doctor_id is IMMUTABLE - set during invitation only.
    """
    phone_number: Optional[str] = Field(None, max_length=50)

class AssignDoctorToParent(BaseSchema):
    """
    Schema for assigning a doctor to a parent.
    Used by receptionist to set/update parent's assigned doctor.
    """
    doctor_id: UUID


class ParentResponse(BaseSchema):
    """
    Schema for parent profile response.
    """
    id: UUID
    user_id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    assigned_doctor_id: Optional[UUID] = None
    phone_number: Optional[str] = None
    email: str
    status: UserStatus
    children: List["ChildResponse"] = []
    created_at: datetime
    updated_at: datetime
    
    @model_validator(mode='before')
    @classmethod
    def extract_user_fields(cls, data):
        """Extract email and status from the user relationship."""
        if hasattr(data, 'user') and data.user:
            # Set email and status from the user object
            if not hasattr(data, 'email'):
                data.email = data.user.email
            if not hasattr(data, 'status'):
                data.status = data.user.status
        return data
    
    class Config:
        from_attributes = True

# ============================================================================
# CHILD SCHEMAS
# ============================================================================

class ChildCreate(BaseSchema):
    """
    Schema for creating a child.
    This is the ONLY clinical entity parents can create directly.
    """
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender

class ChildUpdate(BaseSchema):
    """
    Schema for updating child information.
    All fields are optional.
    """
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None

class ChildResponse(BaseSchema):
    """
    Schema for child profile response.
    """
    id: UUID
    parent_id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# STAFF SCHEMAS (Combined)
# ============================================================================

class StaffMemberResponse(BaseSchema):
    """
    Unified schema for staff member response.
    Represents doctors, HODs, or receptionists with their role type.
    """
    id: UUID
    user_id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    department: str
    role: str  # "DOCTOR", "HOD", or "RECEPTIONIST"
    license_number: Optional[str] = None  # Only for doctors
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChildWithReportStatus(ChildResponse):
    """
    Extended child response with report status information.
    Used for doctor's view of children with their report progress.
    """
    has_report: bool = Field(default=False, description="Whether a final report has been generated")
    is_doctor_reviewed: bool = Field(default=False, description="Whether doctor has reviewed the report")
    is_hod_reviewed: bool = Field(default=False, description="Whether HOD has reviewed the report")
    report_id: Optional[UUID] = Field(None, description="Final report ID if exists")
    report_generated_at: Optional[datetime] = Field(None, description="When report was generated")
    
    class Config:
        from_attributes = True


# ============================================================================
# PARENT WITH REPORTS SCHEMAS
# ============================================================================

class ParentWithReportsResponse(BaseSchema):
    """
    Schema for parent with children and their report status.
    Used by doctors to see their assigned parents and report progress.
    """
    id: UUID
    user_id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    email: str
    status: UserStatus
    children: List[ChildWithReportStatus] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

