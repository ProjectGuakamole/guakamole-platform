from sqlalchemy import (
    BigInteger,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.iam.constants import IAM_SCHEMA


class Country(Base):
    """País disponible en el catálogo geográfico IAM."""

    __tablename__ = "tbl_country"
    __table_args__ = (
        PrimaryKeyConstraint("id_country", name="pk_tbl_country"),
        {"schema": IAM_SCHEMA},
    )

    id_country: Mapped[int] = mapped_column(BigInteger)
    country_name: Mapped[str] = mapped_column(String(100), nullable=False)


class State(Base):
    """Provincia, estado o región disponible en el catálogo geográfico IAM."""

    __tablename__ = "tbl_state"
    __table_args__ = (
        PrimaryKeyConstraint("id_state", name="pk_tbl_state"),
        ForeignKeyConstraint(
            ["id_country"],
            [f"{IAM_SCHEMA}.tbl_country.id_country"],
            name="fk_tbl_state_id_country",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        Index("ix_tbl_state_id_country", "id_country"),
        {"schema": IAM_SCHEMA},
    )

    id_state: Mapped[int] = mapped_column(BigInteger)
    id_country: Mapped[int] = mapped_column(BigInteger, nullable=False)
    state_name: Mapped[str] = mapped_column(String(100), nullable=False)


class City(Base):
    """Ciudad disponible en el catálogo geográfico IAM."""

    __tablename__ = "tbl_city"
    __table_args__ = (
        PrimaryKeyConstraint("id_city", name="pk_tbl_city"),
        ForeignKeyConstraint(
            ["id_state"],
            [f"{IAM_SCHEMA}.tbl_state.id_state"],
            name="fk_tbl_city_id_state",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        Index("ix_tbl_city_id_state", "id_state"),
        {"schema": IAM_SCHEMA},
    )

    id_city: Mapped[int] = mapped_column(BigInteger)
    id_state: Mapped[int] = mapped_column(BigInteger, nullable=False)
    city_name: Mapped[str] = mapped_column(String(120), nullable=False)
