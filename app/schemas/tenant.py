from typing import Optional
from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema
from db.models.tenant import TenantStatus

class TenantCreate(BaseSchema):
    """
    Schema for creating a new tenant.
    """
    name: str
    code: str
    registration_number: Optional[str] = None
    registration_authority: Optional[str] = None
    accreditation_type: Optional[str] = None

class TenantUpdate(BaseSchema):
    """
    Schema for updating a tenant.
    All fields optional for PATCH.
    """
    name: Optional[str] = None
    registration_number: Optional[str] = None
    registration_authority: Optional[str] = None
    accreditation_type: Optional[str] = None
    status: Optional[TenantStatus] = None
    # Code is usually immutable or handled with strict care, omitting from basic update for now to be safe.

class TenantResponse(BaseSchema):
    """
    Tenant response schema.
    """
    id: UUID
    name: str
    code: str
    status: TenantStatus
    created_at: datetime
    registration_number: Optional[str] = None
    registration_authority: Optional[str] = None
    accreditation_type: Optional[str] = None
