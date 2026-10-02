from sqlalchemy import (
    BigInteger,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.domain.iam.constants import IAM_SCHEMA


class Department(TimestampMixin, Base):
    """Departamento IAM perteneciente a una organización."""

    __tablename__ = "tbl_department"
    __table_args__ = (
        PrimaryKeyConstraint("id_department", name="pk_tbl_department"),
        ForeignKeyConstraint(
            ["id_organization"],
            [f"{IAM_SCHEMA}.tbl_organization.id_organization"],
            name="fk_tbl_department_id_organization",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        Index("ix_tbl_department_id_organization", "id_organization"),
        {"schema": IAM_SCHEMA},
    )

    id_department: Mapped[int] = mapped_column(BigInteger)
    id_organization: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
