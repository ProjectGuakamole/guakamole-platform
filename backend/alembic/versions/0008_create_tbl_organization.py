"""create tbl_organization

Revision ID: 0008_create_tbl_organization
Revises: 0007_create_tbl_city
Create Date: 2026-10-02 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_create_tbl_organization"
down_revision: str | None = "0007_create_tbl_city"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_organization",
        sa.Column("id_organization", sa.BigInteger(), nullable=False),
        sa.Column("id_country", sa.BigInteger(), nullable=False),
        sa.Column("id_state", sa.BigInteger(), nullable=False),
        sa.Column("id_city", sa.BigInteger(), nullable=False),
        sa.Column("id_status", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("org_registered_name", sa.String(length=200), nullable=True),
        sa.Column("org_tax", sa.String(length=32), nullable=True),
        sa.Column("org_address", sa.String(length=255), nullable=False),
        sa.Column("org_zipcode", sa.String(length=20), nullable=False),
        sa.Column(
            "create_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("update_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id_organization", name="pk_tbl_organization"),
        sa.ForeignKeyConstraint(
            ["id_country"],
            ["sch_iam.tbl_country.id_country"],
            name="fk_tbl_organization_id_country",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_state"],
            ["sch_iam.tbl_state.id_state"],
            name="fk_tbl_organization_id_state",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_city"],
            ["sch_iam.tbl_city.id_city"],
            name="fk_tbl_organization_id_city",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_status"],
            ["sch_iam.tbl_status.id_status"],
            name="fk_tbl_organization_id_status",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint("name", name="uq_tbl_organization_name"),
        sa.UniqueConstraint("slug", name="uq_tbl_organization_slug"),
        sa.UniqueConstraint(
            "org_registered_name",
            name="uq_tbl_organization_org_registered_name",
        ),
        sa.UniqueConstraint("org_tax", name="uq_tbl_organization_org_tax"),
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_organization_id_country",
        "tbl_organization",
        ["id_country"],
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_organization_id_state",
        "tbl_organization",
        ["id_state"],
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_organization_id_city",
        "tbl_organization",
        ["id_city"],
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_organization_id_status",
        "tbl_organization",
        ["id_status"],
        schema="sch_iam",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tbl_organization_id_status",
        table_name="tbl_organization",
        schema="sch_iam",
    )
    op.drop_index(
        "ix_tbl_organization_id_city",
        table_name="tbl_organization",
        schema="sch_iam",
    )
    op.drop_index(
        "ix_tbl_organization_id_state",
        table_name="tbl_organization",
        schema="sch_iam",
    )
    op.drop_index(
        "ix_tbl_organization_id_country",
        table_name="tbl_organization",
        schema="sch_iam",
    )
    op.drop_table("tbl_organization", schema="sch_iam")
