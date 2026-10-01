"""create tbl_status

Revision ID: 0003_create_tbl_status
Revises: 0002_create_tbl_country
Create Date: 2026-10-01 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_create_tbl_status"
down_revision: str | None = "0002_create_tbl_country"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_status",
        sa.Column("id_status", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "create_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("update_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id_status", name="pk_tbl_status"),
        schema="sch_iam",
    )


def downgrade() -> None:
    op.drop_table("tbl_status", schema="sch_iam")
