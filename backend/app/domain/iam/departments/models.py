from sqlalchemy import (
    BigInteger,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
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


class DepartmentRelation(TimestampMixin, Base):
    """Relación entre un departamento IAM y un usuario IAM."""

    __tablename__ = "tbl_department_relations"
    __table_args__ = (
        PrimaryKeyConstraint(
            "id_department_relation",
            name="pk_tbl_department_relations",
        ),
        ForeignKeyConstraint(
            ["id_department"],
            [f"{IAM_SCHEMA}.tbl_department.id_department"],
            name="fk_tbl_department_relations_id_department",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_user"],
            [f"{IAM_SCHEMA}.tbl_users.id_user"],
            name="fk_tbl_department_relations_id_user",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        UniqueConstraint(
            "id_department",
            "id_user",
            name="uq_tbl_department_relations_id_department_id_user",
        ),
        Index("ix_tbl_department_relations_id_department", "id_department"),
        Index("ix_tbl_department_relations_id_user", "id_user"),
        {"schema": IAM_SCHEMA},
    )

    id_department_relation: Mapped[int] = mapped_column(BigInteger)
    id_department: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_user: Mapped[int] = mapped_column(BigInteger, nullable=False)
