from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Mixin reusable para entidades con marcas temporales de auditoría."""

    created_at: Mapped[datetime] = mapped_column(
        "create_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "update_at",
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
