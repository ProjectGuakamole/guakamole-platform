"""create tbl_users

Revision ID: 0009_create_tbl_users
Revises: 0008_create_tbl_organization
Create Date: 2026-10-02 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0009_create_tbl_users"
down_revision: str | None = "0008_create_tbl_organization"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_users",
        sa.Column("id_user", sa.BigInteger(), nullable=False),
        sa.Column("id_organization", sa.BigInteger(), nullable=False),
        sa.Column("id_platform_role", sa.BigInteger(), nullable=False),
        sa.Column("id_country", sa.BigInteger(), nullable=False),
        sa.Column("id_state", sa.BigInteger(), nullable=False),
        sa.Column("id_city", sa.BigInteger(), nullable=False),
        sa.Column("id_org_role", sa.BigInteger(), nullable=False),
        sa.Column("id_status", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=150), nullable=False),
        sa.Column("birthdate", sa.Date(), nullable=False),
        sa.Column("user_address", sa.String(length=255), nullable=False),
        sa.Column("user_zipcode", sa.String(length=20), nullable=False),
        sa.Column(
            "create_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("update_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id_user", name="pk_tbl_users"),
        sa.ForeignKeyConstraint(
            ["id_organization"],
            ["sch_iam.tbl_organization.id_organization"],
            name="fk_tbl_users_id_organization",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_platform_role"],
            ["sch_iam.tbl_platform_role.id_platform_role"],
            name="fk_tbl_users_id_platform_role",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_country"],
            ["sch_iam.tbl_country.id_country"],
            name="fk_tbl_users_id_country",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_state"],
            ["sch_iam.tbl_state.id_state"],
            name="fk_tbl_users_id_state",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_city"],
            ["sch_iam.tbl_city.id_city"],
            name="fk_tbl_users_id_city",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_org_role"],
            ["sch_iam.tbl_organization_role.id_org_role"],
            name="fk_tbl_users_id_org_role",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_status"],
            ["sch_iam.tbl_status.id_status"],
            name="fk_tbl_users_id_status",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint("email", name="uq_tbl_users_email"),
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_users_id_organization",
        "tbl_users",
        ["id_organization"],
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_users_id_platform_role",
        "tbl_users",
        ["id_platform_role"],
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_users_id_country", "tbl_users", ["id_country"], schema="sch_iam"
    )
    op.create_index(
        "ix_tbl_users_id_state", "tbl_users", ["id_state"], schema="sch_iam"
    )
    op.create_index("ix_tbl_users_id_city", "tbl_users", ["id_city"], schema="sch_iam")
    op.create_index(
        "ix_tbl_users_id_org_role", "tbl_users", ["id_org_role"], schema="sch_iam"
    )
    op.create_index(
        "ix_tbl_users_id_status", "tbl_users", ["id_status"], schema="sch_iam"
    )


def downgrade() -> None:
    op.drop_index("ix_tbl_users_id_status", table_name="tbl_users", schema="sch_iam")
    op.drop_index("ix_tbl_users_id_org_role", table_name="tbl_users", schema="sch_iam")
    op.drop_index("ix_tbl_users_id_city", table_name="tbl_users", schema="sch_iam")
    op.drop_index("ix_tbl_users_id_state", table_name="tbl_users", schema="sch_iam")
    op.drop_index("ix_tbl_users_id_country", table_name="tbl_users", schema="sch_iam")
    op.drop_index(
        "ix_tbl_users_id_platform_role",
        table_name="tbl_users",
        schema="sch_iam",
    )
    op.drop_index(
        "ix_tbl_users_id_organization",
        table_name="tbl_users",
        schema="sch_iam",
    )
    op.drop_table("tbl_users", schema="sch_iam")
