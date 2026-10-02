"""create schema iam

Revision ID: 0001_create_schema_iam
Revises:
Create Date: 2026-10-01 00:00:00.000000
"""

from alembic import op

revision = "0001_create_schema_iam"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")
    op.execute("CREATE SCHEMA IF NOT EXISTS sch_iam")
    op.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")


def downgrade() -> None:
    # No se reduce alembic_version.version_num a VARCHAR(32) porque podría
    # truncar revision IDs descriptivas ya aplicadas y romper el histórico.
    op.execute("GRANT CREATE ON SCHEMA public TO PUBLIC")
    op.execute("DROP SCHEMA IF EXISTS sch_iam")
