"""create tbl_state

Revision ID: 0006_create_tbl_state
Revises: 0005
Create Date: 2026-10-01 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0006_create_tbl_state"
down_revision: str | None = "0005_create_tbl_organization_role"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_state",
        sa.Column("id_state", sa.BigInteger(), nullable=False),
        sa.Column("id_country", sa.BigInteger(), nullable=False),
        sa.Column("state_name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id_state", name="pk_tbl_state"),
        sa.ForeignKeyConstraint(
            ["id_country"],
            ["sch_iam.tbl_country.id_country"],
            name="fk_tbl_state_id_country",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_state_id_country",
        "tbl_state",
        ["id_country"],
        schema="sch_iam",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tbl_state_id_country",
        table_name="tbl_state",
        schema="sch_iam",
    )
    op.drop_table("tbl_state", schema="sch_iam")
