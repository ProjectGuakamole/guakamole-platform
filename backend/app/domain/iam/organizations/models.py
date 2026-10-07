from sqlalchemy import (
    BigInteger,
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


class Organization(TimestampMixin, Base):
    """Organización cliente B2B registrada en IAM."""

    __tablename__ = "tbl_organization"
    __table_args__ = (
        PrimaryKeyConstraint("id_organization", name="pk_tbl_organization"),
        ForeignKeyConstraint(
            ["id_country"],
            [f"{IAM_SCHEMA}.tbl_country.id_country"],
            name="fk_tbl_organization_id_country",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_state"],
            [f"{IAM_SCHEMA}.tbl_state.id_state"],
            name="fk_tbl_organization_id_state",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_city"],
            [f"{IAM_SCHEMA}.tbl_city.id_city"],
            name="fk_tbl_organization_id_city",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        ForeignKeyConstraint(
            ["id_status"],
            [f"{IAM_SCHEMA}.tbl_status.id_status"],
            name="fk_tbl_organization_id_status",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        UniqueConstraint("name", name="uq_tbl_organization_name"),
        UniqueConstraint("slug", name="uq_tbl_organization_slug"),
        UniqueConstraint(
            "org_registered_name",
            name="uq_tbl_organization_org_registered_name",
        ),
        UniqueConstraint("org_tax", name="uq_tbl_organization_org_tax"),
        UniqueConstraint("public_id", name="uq_tbl_organization_public_id"),
        Index("ix_tbl_organization_id_country", "id_country"),
        Index("ix_tbl_organization_id_state", "id_state"),
        Index("ix_tbl_organization_id_city", "id_city"),
        Index("ix_tbl_organization_id_status", "id_status"),
        {"schema": IAM_SCHEMA},
    )

    id_organization: Mapped[int] = mapped_column(BigInteger, Identity())
    public_id: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=lambda: generate_public_id(PublicIdPrefix.ORGANIZATION),
    )
    id_country: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_state: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_city: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_status: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    org_registered_name: Mapped[str | None] = mapped_column(String(200))
    org_tax: Mapped[str | None] = mapped_column(String(32))
    org_address: Mapped[str] = mapped_column(String(255), nullable=False)
    org_zipcode: Mapped[str] = mapped_column(String(20), nullable=False)
