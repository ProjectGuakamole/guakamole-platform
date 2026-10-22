"""Crea el esquema IAM contractual desde una línea base limpia."""

from datetime import datetime

import sqlalchemy as sa

from alembic import op

revision = "iam_baseline"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None

SCHEMA = "sch_iam"


def _timestamp_columns() -> tuple[sa.Column[datetime], sa.Column[datetime]]:
    return (
        sa.Column(
            "create_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("update_at", sa.DateTime(timezone=True), nullable=True),
    )


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA {SCHEMA}")
    op.create_table(
        "tbl_country",
        sa.Column("id_country", sa.BigInteger(), nullable=False),
        sa.Column("country_name", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id_country", name="pk_tbl_country"),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_status",
        sa.Column("id_status", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id_status", name="pk_tbl_status"),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_platform_role",
        sa.Column("id_platform_role", sa.BigInteger(), nullable=False),
        sa.Column("platform_role_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id_platform_role", name="pk_tbl_platform_role"),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_organization_role",
        sa.Column("id_org_role", sa.BigInteger(), nullable=False),
        sa.Column("org_role_type", sa.String(50), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id_org_role", name="pk_tbl_organization_role"),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_state",
        sa.Column("id_state", sa.BigInteger(), nullable=False),
        sa.Column("id_country", sa.BigInteger(), nullable=False),
        sa.Column("state_name", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id_state", name="pk_tbl_state"),
        sa.ForeignKeyConstraint(
            ["id_country"],
            [f"{SCHEMA}.tbl_country.id_country"],
            name="fk_tbl_state_id_country",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint(
            "id_state", "id_country", name="uq_tbl_state_id_state_id_country"
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_city",
        sa.Column("id_city", sa.BigInteger(), nullable=False),
        sa.Column("id_state", sa.BigInteger(), nullable=False),
        sa.Column("id_country", sa.BigInteger(), nullable=False),
        sa.Column("city_name", sa.String(120), nullable=False),
        sa.PrimaryKeyConstraint("id_city", name="pk_tbl_city"),
        sa.ForeignKeyConstraint(
            ["id_state", "id_country"],
            [f"{SCHEMA}.tbl_state.id_state", f"{SCHEMA}.tbl_state.id_country"],
            name="fk_tbl_city_id_state_country",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint(
            "id_city", "id_state", "id_country", name="uq_tbl_city_geo_hierarchy"
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_organization",
        sa.Column(
            "id_organization", sa.BigInteger(), sa.Identity(start=1), nullable=False
        ),
        sa.Column("public_id", sa.String(40), nullable=False),
        sa.Column("id_country", sa.BigInteger(), nullable=False),
        sa.Column("id_state", sa.BigInteger(), nullable=False),
        sa.Column("id_city", sa.BigInteger(), nullable=False),
        sa.Column("id_status", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("org_registered_name", sa.String(200), nullable=True),
        sa.Column("org_tax", sa.String(32), nullable=True),
        sa.Column("org_address", sa.String(255), nullable=False),
        sa.Column("org_zipcode", sa.String(20), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id_organization", name="pk_tbl_organization"),
        sa.ForeignKeyConstraint(
            ["id_city", "id_state", "id_country"],
            [
                f"{SCHEMA}.tbl_city.id_city",
                f"{SCHEMA}.tbl_city.id_state",
                f"{SCHEMA}.tbl_city.id_country",
            ],
            name="fk_tbl_organization_geo_hierarchy",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_status"],
            [f"{SCHEMA}.tbl_status.id_status"],
            name="fk_tbl_organization_id_status",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint("name", name="uq_tbl_organization_name"),
        sa.UniqueConstraint("slug", name="uq_tbl_organization_slug"),
        sa.UniqueConstraint(
            "org_registered_name", name="uq_tbl_organization_org_registered_name"
        ),
        sa.UniqueConstraint("org_tax", name="uq_tbl_organization_org_tax"),
        sa.UniqueConstraint("public_id", name="uq_tbl_organization_public_id"),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_users",
        sa.Column("id_user", sa.BigInteger(), sa.Identity(start=1), nullable=False),
        sa.Column("public_id", sa.String(40), nullable=False),
        sa.Column("id_organization", sa.BigInteger(), nullable=False),
        sa.Column("id_platform_role", sa.BigInteger(), nullable=False),
        sa.Column("id_country", sa.BigInteger(), nullable=False),
        sa.Column("id_state", sa.BigInteger(), nullable=False),
        sa.Column("id_city", sa.BigInteger(), nullable=False),
        sa.Column("id_org_role", sa.BigInteger(), nullable=False),
        sa.Column("id_status", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(150), nullable=False),
        sa.Column("birthdate", sa.Date(), nullable=False),
        sa.Column("user_address", sa.String(255), nullable=False),
        sa.Column("user_zipcode", sa.String(20), nullable=False),
        *_timestamp_columns(),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id_user", name="pk_tbl_users"),
        sa.ForeignKeyConstraint(
            ["id_organization"],
            [f"{SCHEMA}.tbl_organization.id_organization"],
            name="fk_tbl_users_id_organization",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_platform_role"],
            [f"{SCHEMA}.tbl_platform_role.id_platform_role"],
            name="fk_tbl_users_id_platform_role",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_city", "id_state", "id_country"],
            [
                f"{SCHEMA}.tbl_city.id_city",
                f"{SCHEMA}.tbl_city.id_state",
                f"{SCHEMA}.tbl_city.id_country",
            ],
            name="fk_tbl_users_geo_hierarchy",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_org_role"],
            [f"{SCHEMA}.tbl_organization_role.id_org_role"],
            name="fk_tbl_users_id_org_role",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_status"],
            [f"{SCHEMA}.tbl_status.id_status"],
            name="fk_tbl_users_id_status",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint("email", name="uq_tbl_users_email"),
        sa.UniqueConstraint("public_id", name="uq_tbl_users_public_id"),
        sa.UniqueConstraint(
            "id_user", "id_organization", name="uq_tbl_users_id_user_id_organization"
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_department",
        sa.Column("id_department", sa.BigInteger(), nullable=False),
        sa.Column("id_organization", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id_department", name="pk_tbl_department"),
        sa.ForeignKeyConstraint(
            ["id_organization"],
            [f"{SCHEMA}.tbl_organization.id_organization"],
            name="fk_tbl_department_id_organization",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint(
            "id_department",
            "id_organization",
            name="uq_tbl_department_id_department_id_organization",
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_department_relations",
        sa.Column("id_department_relation", sa.BigInteger(), nullable=False),
        sa.Column("id_department", sa.BigInteger(), nullable=False),
        sa.Column("id_user", sa.BigInteger(), nullable=False),
        sa.Column("id_organization", sa.BigInteger(), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint(
            "id_department_relation", name="pk_tbl_department_relations"
        ),
        sa.ForeignKeyConstraint(
            ["id_department", "id_organization"],
            [
                f"{SCHEMA}.tbl_department.id_department",
                f"{SCHEMA}.tbl_department.id_organization",
            ],
            name="fk_tbl_department_relations_department_organization",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_user", "id_organization"],
            [f"{SCHEMA}.tbl_users.id_user", f"{SCHEMA}.tbl_users.id_organization"],
            name="fk_tbl_department_relations_user_organization",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint(
            "id_department",
            "id_user",
            name="uq_tbl_department_relations_id_department_id_user",
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "tbl_revoked_access_token",
        sa.Column(
            "id_revoked_access_token", sa.BigInteger(), sa.Identity(), nullable=False
        ),
        sa.Column("jti", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "id_revoked_access_token", name="pk_tbl_revoked_access_token"
        ),
        schema=SCHEMA,
    )
    _create_indexes()


def _create_indexes() -> None:
    for table, column in (
        ("tbl_state", "id_country"),
        ("tbl_city", "id_state"),
        ("tbl_organization", "id_country"),
        ("tbl_organization", "id_state"),
        ("tbl_organization", "id_city"),
        ("tbl_organization", "id_status"),
        ("tbl_users", "id_organization"),
        ("tbl_users", "id_platform_role"),
        ("tbl_users", "id_country"),
        ("tbl_users", "id_state"),
        ("tbl_users", "id_city"),
        ("tbl_users", "id_org_role"),
        ("tbl_users", "id_status"),
        ("tbl_department", "id_organization"),
        ("tbl_department_relations", "id_department"),
        ("tbl_department_relations", "id_user"),
    ):
        op.create_index(f"ix_{table}_{column}", table, [column], schema=SCHEMA)
    op.create_index(
        "uq_tbl_country_country_name_ci",
        "tbl_country",
        [sa.text("lower(country_name)")],
        unique=True,
        schema=SCHEMA,
    )
    op.create_index(
        "uq_tbl_status_status_ci",
        "tbl_status",
        [sa.text("lower(status)")],
        unique=True,
        schema=SCHEMA,
    )
    op.create_index(
        "uq_tbl_platform_role_type_ci",
        "tbl_platform_role",
        [sa.text("lower(platform_role_type)")],
        unique=True,
        schema=SCHEMA,
    )
    op.create_index(
        "uq_tbl_organization_role_type_ci",
        "tbl_organization_role",
        [sa.text("lower(org_role_type)")],
        unique=True,
        schema=SCHEMA,
    )
    op.create_index(
        "uq_tbl_state_country_name_ci",
        "tbl_state",
        ["id_country", sa.text("lower(state_name)")],
        unique=True,
        schema=SCHEMA,
    )
    op.create_index(
        "uq_tbl_city_state_name_ci",
        "tbl_city",
        ["id_state", sa.text("lower(city_name)")],
        unique=True,
        schema=SCHEMA,
    )
    op.create_index(
        "uq_tbl_department_organization_name_ci",
        "tbl_department",
        ["id_organization", sa.text("lower(name)")],
        unique=True,
        schema=SCHEMA,
    )
    op.create_index(
        "ix_tbl_revoked_access_token_jti",
        "tbl_revoked_access_token",
        ["jti"],
        unique=True,
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.execute(f"DROP SCHEMA {SCHEMA} CASCADE")
