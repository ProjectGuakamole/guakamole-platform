from sqlalchemy import BigInteger, PrimaryKeyConstraint, String, Text
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


class PlatformRole(TimestampMixin, Base):
    """Rol global disponible en la plataforma."""

    __tablename__ = "tbl_platform_role"
    __table_args__ = (
        PrimaryKeyConstraint("id_platform_role", name="pk_tbl_platform_role"),
        {"schema": IAM_SCHEMA},
    )

    id_platform_role: Mapped[int] = mapped_column(BigInteger)
    platform_role_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class OrganizationRole(TimestampMixin, Base):
    """Rol disponible dentro del ámbito de una organización."""

    __tablename__ = "tbl_organization_role"
    __table_args__ = (
        PrimaryKeyConstraint("id_org_role", name="pk_tbl_organization_role"),
        {"schema": IAM_SCHEMA},
    )

    id_org_role: Mapped[int] = mapped_column(BigInteger)
    org_role_type: Mapped[str] = mapped_column(String(50), nullable=False)
