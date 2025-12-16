from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

class TimestampMixin:
    """Add created_at and updated_at timestamps to models"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class SoftDeleteMixin:
    """Add soft delete capability to models"""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        index=True
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    def soft_delete(self):
        """Mark record as deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
