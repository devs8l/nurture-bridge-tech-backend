from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.schemas.base import BaseSchema
from db.models.auth import UserRole, UserStatus

class UserResponse(BaseSchema):
    """
    Schema for User Response.
    Read-only view of the user.
    """
    id: UUID
    email: str
    name: str
    role: UserRole
    tenant_id: Optional[UUID] = None
    status: UserStatus
    # We do NOT include hashed_password here
