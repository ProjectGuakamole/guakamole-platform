from sqlalchemy import BigInteger, PrimaryKeyConstraint, String
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
