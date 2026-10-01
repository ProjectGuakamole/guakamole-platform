from pathlib import Path

from sqlalchemy import Integer, inspect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.sqltypes import DateTime

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.domain.iam.constants import IAM_SCHEMA


class _TimestampModel(TimestampMixin, Base):
    __tablename__ = "timestamp_model_for_test"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


def test_iam_schema_constant() -> None:
    assert IAM_SCHEMA == "sch_iam"


def test_timestamp_mixin_maps_expected_columns() -> None:
    mapper = inspect(_TimestampModel)
    created_column = mapper.columns["created_at"]
    updated_column = mapper.columns["updated_at"]

    assert isinstance(created_column, Column)
    assert isinstance(updated_column, Column)
    assert created_column.name == "create_at"
    assert updated_column.name == "update_at"
    assert isinstance(created_column.type, DateTime)
    assert isinstance(updated_column.type, DateTime)
    assert created_column.type.timezone is True
    assert updated_column.type.timezone is True
    assert created_column.nullable is False
    assert updated_column.nullable is True
    assert created_column.server_default is not None
    assert updated_column.onupdate is not None


def test_base_metadata_is_available() -> None:
    model_table = _TimestampModel.__table__

    assert Base.metadata is not None
    assert isinstance(model_table, Table)
    assert model_table.metadata is Base.metadata


def test_initial_iam_migration_creates_schema_without_tables() -> None:
    migration_path = Path("alembic/versions/0001_create_schema_iam.py")
    migration_content = migration_path.read_text(encoding="utf-8")

    assert "CREATE SCHEMA IF NOT EXISTS" in migration_content
    assert "sch_iam" in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "REVOKE CREATE ON SCHEMA public FROM PUBLIC" in migration_content
    assert "DROP SCHEMA IF EXISTS" in migration_content
    assert "op.create_table" not in migration_content
    assert "DROP SCHEMA public" not in migration_content


def test_alembic_ini_does_not_store_operational_database_credentials() -> None:
    alembic_ini_content = Path("alembic.ini").read_text(encoding="utf-8")
    previous_credentials = "guakamole" + ":" + "guakamole"
    previous_sync_url = "postgresql://" + "guakamole"
    previous_async_url = "postgresql+psycopg://" + "guakamole"

    assert previous_credentials not in alembic_ini_content
    assert previous_sync_url not in alembic_ini_content
    assert previous_async_url not in alembic_ini_content
    assert "driver://user:pass@localhost/dbname" in alembic_ini_content


def test_alembic_env_reads_database_url_from_environment() -> None:
    alembic_env_content = Path("alembic/env.py").read_text(encoding="utf-8")

    assert 'DATABASE_URL_ENV_VAR = "DATABASE_URL"' in alembic_env_content
    assert "os.environ.get(DATABASE_URL_ENV_VAR)" in alembic_env_content
    assert 'config.set_main_option("sqlalchemy.url", get_required_database_url())' in (
        alembic_env_content
    )
