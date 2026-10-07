"""add registration public ids and safe internal id defaults

Revision ID: 0013_registration_public_ids
Revises: 0012_seed_initial_iam_catalogs
Create Date: 2026-10-07 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0013_registration_public_ids"
down_revision = "0012_seed_initial_iam_catalogs"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    connection.execute(
        sa.text(
            """
            CREATE SEQUENCE IF NOT EXISTS sch_iam.tbl_organization_id_seq
            START WITH 1000000000
            """
        )
    )
    connection.execute(
        sa.text(
            """
            CREATE SEQUENCE IF NOT EXISTS sch_iam.tbl_users_id_seq
            START WITH 1000000000
            """
        )
    )
    # Reservamos un rango alto para IDs generados por la BD y evitamos depender de
    # cálculos sobre el mayor identificador existente, inseguros ante concurrencia
    # y fixtures MVP.
    op.alter_column(
        "tbl_organization",
        "id_organization",
        schema="sch_iam",
        server_default=sa.text("nextval('sch_iam.tbl_organization_id_seq'::regclass)"),
    )
    op.alter_column(
        "tbl_users",
        "id_user",
        schema="sch_iam",
        server_default=sa.text("nextval('sch_iam.tbl_users_id_seq'::regclass)"),
    )
    op.add_column(
        "tbl_organization",
        sa.Column("public_id", sa.String(40), nullable=True),
        schema="sch_iam",
    )
    op.add_column(
        "tbl_users",
        sa.Column("public_id", sa.String(40), nullable=True),
        schema="sch_iam",
    )
    connection.execute(
        sa.text(
            """
            UPDATE sch_iam.tbl_organization
            SET public_id = 'org_' || gen_random_uuid()
            WHERE public_id IS NULL
            """
        ),
    )
    connection.execute(
        sa.text(
            """
            UPDATE sch_iam.tbl_users
            SET public_id = 'usr_' || gen_random_uuid()
            WHERE public_id IS NULL
            """
        ),
    )
    op.alter_column("tbl_organization", "public_id", schema="sch_iam", nullable=False)
    op.alter_column("tbl_users", "public_id", schema="sch_iam", nullable=False)
    op.create_unique_constraint(
        "uq_tbl_organization_public_id",
        "tbl_organization",
        ["public_id"],
        schema="sch_iam",
    )
    op.create_unique_constraint(
        "uq_tbl_users_public_id", "tbl_users", ["public_id"], schema="sch_iam"
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_tbl_users_public_id", "tbl_users", schema="sch_iam", type_="unique"
    )
    op.drop_constraint(
        "uq_tbl_organization_public_id",
        "tbl_organization",
        schema="sch_iam",
        type_="unique",
    )
    op.drop_column("tbl_users", "public_id", schema="sch_iam")
    op.drop_column("tbl_organization", "public_id", schema="sch_iam")
    op.alter_column("tbl_users", "id_user", schema="sch_iam", server_default=None)
    op.alter_column(
        "tbl_organization", "id_organization", schema="sch_iam", server_default=None
    )
    op.execute("DROP SEQUENCE IF EXISTS sch_iam.tbl_users_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS sch_iam.tbl_organization_id_seq")
