"""create tbl_department_relations

Revision ID: 0011_create_tbl_department_relations
Revises: 0010_create_tbl_department
Create Date: 2026-10-02 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0011_create_tbl_department_relations"
down_revision: str | None = "0010_create_tbl_department"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_department_relations",
        sa.Column("id_department_relation", sa.BigInteger(), nullable=False),
        sa.Column("id_department", sa.BigInteger(), nullable=False),
        sa.Column("id_user", sa.BigInteger(), nullable=False),
        sa.Column(
            "create_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("update_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint(
            "id_department_relation",
            name="pk_tbl_department_relations",
        ),
        sa.ForeignKeyConstraint(
            ["id_department"],
            ["sch_iam.tbl_department.id_department"],
            name="fk_tbl_department_relations_id_department",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_user"],
            ["sch_iam.tbl_users.id_user"],
            name="fk_tbl_department_relations_id_user",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint(
            "id_department",
            "id_user",
            name="uq_tbl_department_relations_id_department_id_user",
        ),
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_department_relations_id_department",
        "tbl_department_relations",
        ["id_department"],
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_department_relations_id_user",
        "tbl_department_relations",
        ["id_user"],
        schema="sch_iam",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tbl_department_relations_id_user",
        table_name="tbl_department_relations",
        schema="sch_iam",
    )
    op.drop_index(
        "ix_tbl_department_relations_id_department",
        table_name="tbl_department_relations",
        schema="sch_iam",
    )
    op.drop_table("tbl_department_relations", schema="sch_iam")
