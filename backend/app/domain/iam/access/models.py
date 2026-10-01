from sqlalchemy import BigInteger, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.domain.iam.constants import IAM_SCHEMA


class Status(TimestampMixin, Base):
    """Estado disponible para entidades IAM."""

    __tablename__ = "tbl_status"
    __table_args__ = (
        PrimaryKeyConstraint("id_status", name="pk_tbl_status"),
        {"schema": IAM_SCHEMA},
    )

    id_status: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
