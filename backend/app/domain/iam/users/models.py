from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Identity,
    Index,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.domain.auth.public_ids import PublicIdPrefix, generate_public_id
from app.domain.iam.constants import IAM_SCHEMA


class User(TimestampMixin, Base):
    """Usuario IAM perteneciente a una organización."""

    __tablename__ = "tbl_users"
    __table_args__ = (
        PrimaryKeyConstraint("id_user", name="pk_tbl_users"),
        ForeignKeyConstraint(
            ["id_organization"],
            [f"{IAM_SCHEMA}.tbl_organization.id_organization"],
            name="fk_tbl_users_id_organization",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_platform_role"],
            [f"{IAM_SCHEMA}.tbl_platform_role.id_platform_role"],
            name="fk_tbl_users_id_platform_role",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_country"],
            [f"{IAM_SCHEMA}.tbl_country.id_country"],
            name="fk_tbl_users_id_country",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_state"],
            [f"{IAM_SCHEMA}.tbl_state.id_state"],
            name="fk_tbl_users_id_state",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_city"],
            [f"{IAM_SCHEMA}.tbl_city.id_city"],
            name="fk_tbl_users_id_city",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_org_role"],
            [f"{IAM_SCHEMA}.tbl_organization_role.id_org_role"],
            name="fk_tbl_users_id_org_role",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_status"],
            [f"{IAM_SCHEMA}.tbl_status.id_status"],
            name="fk_tbl_users_id_status",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        UniqueConstraint("email", name="uq_tbl_users_email"),
        UniqueConstraint("public_id", name="uq_tbl_users_public_id"),
        Index("ix_tbl_users_id_organization", "id_organization"),
        Index("ix_tbl_users_id_platform_role", "id_platform_role"),
        Index("ix_tbl_users_id_country", "id_country"),
        Index("ix_tbl_users_id_state", "id_state"),
        Index("ix_tbl_users_id_city", "id_city"),
        Index("ix_tbl_users_id_org_role", "id_org_role"),
        Index("ix_tbl_users_id_status", "id_status"),
        {"schema": IAM_SCHEMA},
    )

    id_user: Mapped[int] = mapped_column(BigInteger, Identity())
    public_id: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=lambda: generate_public_id(PublicIdPrefix.USER),
    )
    id_organization: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_platform_role: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_country: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_state: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_city: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_org_role: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_status: Mapped[int] = mapped_column(BigInteger, nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), nullable=False)
    birthdate: Mapped[date] = mapped_column(Date, nullable=False)
    user_address: Mapped[str] = mapped_column(String(255), nullable=False)
    user_zipcode: Mapped[str] = mapped_column(String(20), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
