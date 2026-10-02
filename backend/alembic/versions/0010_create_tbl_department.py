"""create tbl_department

Revision ID: 0010_create_tbl_department
Revises: 0009_create_tbl_users
Create Date: 2026-10-02 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0010_create_tbl_department"
down_revision: str | None = "0009_create_tbl_users"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_department",
        sa.Column("id_department", sa.BigInteger(), nullable=False),
        sa.Column("id_organization", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "create_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("update_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id_department", name="pk_tbl_department"),
        sa.ForeignKeyConstraint(
            ["id_organization"],
            ["sch_iam.tbl_organization.id_organization"],
            name="fk_tbl_department_id_organization",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_department_id_organization",
        "tbl_department",
        ["id_organization"],
        schema="sch_iam",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tbl_department_id_organization",
        table_name="tbl_department",
        schema="sch_iam",
    )
    op.drop_table("tbl_department", schema="sch_iam")
