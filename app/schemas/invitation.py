from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema
from db.models.auth import UserRole, InvitationStatus

class InvitationCreate(BaseSchema):
    """
    Schema for creating an invitation.
    
    IMPORTANT: department is REQUIRED for staff roles (HOD, DOCTOR, RECEPTIONIST).
    This is enforced at the endpoint level.
    """
    email: EmailStr
    role: UserRole
    tenant_id: UUID
    doctor_id: Optional[UUID] = None  # Required for PARENT role only
    department: Optional[str] = Field(
        None, 
        max_length=255,
        description="REQUIRED for HOD/DOCTOR/RECEPTIONIST, not used for PARENT"
    )

class InvitationResponse(BaseSchema):
    """
    Schema for invitation response.
    """
    id: UUID
    email: str
    role_to_assign: UserRole
    tenant_id: UUID
    doctor_id: Optional[UUID] = None
    department: Optional[str] = None  # For staff roles
    status: InvitationStatus
    expires_at: datetime
    # We generally do NOT return the token in the API response for security (it's sent via email).
    # But for development/MVP where email isn't set up, we return it to allow copy-pasting.
    token: str 
