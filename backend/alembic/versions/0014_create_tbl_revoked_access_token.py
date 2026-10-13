"""create revoked access token table

Revision ID: 0014_create_tbl_revoked_access_token
Revises: 0013_registration_public_ids
"""

import sqlalchemy as sa

from alembic import op

revision = "0014_create_tbl_revoked_access_token"
down_revision = "0013_registration_public_ids"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tbl_revoked_access_token",
        sa.Column(
            "id_revoked_access_token", sa.BigInteger(), sa.Identity(), nullable=False
        ),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "id_revoked_access_token", name="pk_tbl_revoked_access_token"
        ),
        schema="sch_iam",
    )
    op.create_index(
        "ix_tbl_revoked_access_token_jti",
        "tbl_revoked_access_token",
        ["jti"],
        unique=True,
        schema="sch_iam",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tbl_revoked_access_token_jti",
        table_name="tbl_revoked_access_token",
        schema="sch_iam",
    )
    op.drop_table("tbl_revoked_access_token", schema="sch_iam")
