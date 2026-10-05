"""create tbl_organization_role

Revision ID: 0005_create_tbl_organization_role
Revises: 0004_create_tbl_platform_role
Create Date: 2026-10-01 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0005_create_tbl_organization_role"
down_revision: str | None = "0004_create_tbl_platform_role"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_organization_role",
        sa.Column("id_org_role", sa.BigInteger(), nullable=False),
        sa.Column("org_role_type", sa.String(length=50), nullable=False),
        sa.Column(
            "create_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("update_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id_org_role", name="pk_tbl_organization_role"),
        schema="sch_iam",
    )


def downgrade() -> None:
    op.drop_table("tbl_organization_role", schema="sch_iam")
