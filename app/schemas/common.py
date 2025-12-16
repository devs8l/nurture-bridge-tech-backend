from datetime import datetime
from typing import Any, Dict, Optional

from app.schemas.base import BaseSchema


class MessageResponse(BaseSchema):
    """
    Generic message response schema.
    Used for simple success messages or error details.
    """
    message: str
    data: Optional[Any] = None


class HealthResponse(BaseSchema):
    """
    Health check response schema.
    """
    status: str
    timestamp: datetime
    version: str
    dependencies: Dict[str, str]
