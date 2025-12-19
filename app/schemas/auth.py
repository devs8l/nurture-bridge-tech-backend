from typing import Optional
from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema

class LoginRequest(BaseSchema):
    """Schema for user login."""
    email: EmailStr
    password: str

class PasswordSetRequest(BaseSchema):
    """Schema for setting password during invitation acceptance."""
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

    def model_post_init(self, __context):
        if self.password != self.confirm_password:
             raise ValueError("Passwords do not match")

class TokenResponse(BaseSchema):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    name: str  # User's name
    role: str  # User's role
    tenant_id: Optional[str] = None  # User's tenant ID (None for SUPER_ADMIN)
    email: str  # User's email
