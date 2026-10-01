"""create tbl_country

Revision ID: 0002_create_tbl_country
Revises: 0001_create_schema_iam
Create Date: 2026-10-01 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_create_tbl_country"
down_revision: str | None = "0001_create_schema_iam"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_country",
        sa.Column("id_country", sa.BigInteger(), nullable=False),
        sa.Column("country_name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id_country", name="pk_tbl_country"),
        schema="sch_iam",
    )


def downgrade() -> None:
    op.drop_table("tbl_country", schema="sch_iam")
