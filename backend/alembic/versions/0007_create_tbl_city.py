"""create tbl_city

Revision ID: 0007_create_tbl_city
Revises: 0006_create_tbl_state
Create Date: 2026-10-01 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0007_create_tbl_city"
down_revision: str | None = "0006_create_tbl_state"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_city",
        sa.Column("id_city", sa.BigInteger(), nullable=False),
        sa.Column("id_state", sa.BigInteger(), nullable=False),
        sa.Column("city_name", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id_city", name="pk_tbl_city"),
        sa.ForeignKeyConstraint(
            ["id_state"],
            ["sch_iam.tbl_state.id_state"],
            name="fk_tbl_city_id_state",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_city_id_state",
        "tbl_city",
        ["id_state"],
        schema="sch_iam",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tbl_city_id_state",
        table_name="tbl_city",
        schema="sch_iam",
    )
    op.drop_table("tbl_city", schema="sch_iam")
