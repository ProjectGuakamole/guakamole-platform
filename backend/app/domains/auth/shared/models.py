"""Modelos ORM operacionales del dominio de autenticación."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Identity,
    Index,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domains.iam.constants import IAM_SCHEMA


class RevokedAccessToken(Base):
    """Identificador de un JWT invalidado antes de su expiración natural."""

    __tablename__ = "tbl_revoked_access_token"
    __table_args__ = (
        PrimaryKeyConstraint(
            "id_revoked_access_token", name="pk_tbl_revoked_access_token"
        ),
        Index("ix_tbl_revoked_access_token_jti", "jti", unique=True),
        {"schema": IAM_SCHEMA},
    )

    id_revoked_access_token: Mapped[int] = mapped_column(BigInteger, Identity())
    jti: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
