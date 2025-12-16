from typing import Optional
from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema

class LoginRequest(BaseSchema):
    """Schema for user login."""
    email: EmailStr
    password: str

class PasswordSetRequest(BaseSchema):
    """Schema for setting password during invitation acceptance."""
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
