"""seed initial IAM catalogs

Revision ID: 0012_seed_initial_iam_catalogs
Revises: 0011_create_tbl_department_relations
Create Date: 2026-10-02 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0012_seed_initial_iam_catalogs"
down_revision = "0011_create_tbl_department_relations"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            INSERT INTO sch_iam.tbl_status (status)
            VALUES ('ACTIVE'), ('INACTIVE'), ('DISABLED')
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO sch_iam.tbl_platform_role (
                platform_role_type,
                description
            )
            VALUES
                ('PLATFORM_ADMIN', 'Administrador global de la plataforma.'),
                ('USER', 'Usuario estándar de la plataforma.')
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO sch_iam.tbl_organization_role (org_role_type)
            VALUES ('COMPANY_ADMIN'), ('GROUP_MANAGER'), ('EMPLOYEE')
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO sch_iam.tbl_country (country_name)
            VALUES ('España'), ('Portugal'), ('Francia')
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO sch_iam.tbl_state (state_name, id_country)
            VALUES
                (
                    'Catalunya',
                    (
                        SELECT id_country
                        FROM sch_iam.tbl_country
                        WHERE country_name = 'España'
                    )
                ),
                (
                    'Madrid',
                    (
                        SELECT id_country
                        FROM sch_iam.tbl_country
                        WHERE country_name = 'España'
                    )
                ),
                (
                    'Lisboa',
                    (
                        SELECT id_country
                        FROM sch_iam.tbl_country
                        WHERE country_name = 'Portugal'
                    )
                )
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO sch_iam.tbl_city (city_name, id_state)
            VALUES
                (
                    'Barcelona',
                    (
                        SELECT id_state
                        FROM sch_iam.tbl_state
                        WHERE state_name = 'Catalunya'
                    )
                ),
                (
                    'Madrid',
                    (
                        SELECT id_state
                        FROM sch_iam.tbl_state
                        WHERE state_name = 'Madrid'
                    )
                ),
                (
                    'Lisboa',
                    (
                        SELECT id_state
                        FROM sch_iam.tbl_state
                        WHERE state_name = 'Lisboa'
                    )
                )
            """,
        ),
    )


def downgrade() -> None:
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            DELETE FROM sch_iam.tbl_city
            WHERE city_name = 'Barcelona'
               OR city_name = 'Madrid'
               OR city_name = 'Lisboa'
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM sch_iam.tbl_state
            WHERE state_name = 'Catalunya'
               OR state_name = 'Madrid'
               OR state_name = 'Lisboa'
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM sch_iam.tbl_country
            WHERE country_name = 'España'
               OR country_name = 'Portugal'
               OR country_name = 'Francia'
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM sch_iam.tbl_organization_role
            WHERE org_role_type = 'COMPANY_ADMIN'
               OR org_role_type = 'GROUP_MANAGER'
               OR org_role_type = 'EMPLOYEE'
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM sch_iam.tbl_platform_role
            WHERE platform_role_type = 'PLATFORM_ADMIN'
               OR platform_role_type = 'USER'
            """,
        ),
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM sch_iam.tbl_status
            WHERE status = 'ACTIVE'
               OR status = 'INACTIVE'
               OR status = 'DISABLED'
            """,
        ),
    )
