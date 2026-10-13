from pathlib import Path

import pytest
from sqlalchemy import Integer, inspect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.sqltypes import DateTime

import app.db.model_registry as model_registry
from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.domains.iam.constants import IAM_SCHEMA

pytestmark = pytest.mark.integration


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


def test_model_registry_loads_current_iam_models() -> None:
    expected_tables = {
        "sch_iam.tbl_city",
        "sch_iam.tbl_country",
        "sch_iam.tbl_department",
        "sch_iam.tbl_department_relations",
        "sch_iam.tbl_organization",
        "sch_iam.tbl_organization_role",
        "sch_iam.tbl_platform_role",
        "sch_iam.tbl_state",
        "sch_iam.tbl_status",
        "sch_iam.tbl_users",
    }

    assert model_registry.access_models.Status.__tablename__ == "tbl_status"
    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_iam_baseline_creates_the_complete_schema() -> None:
    migration_path = Path("alembic/versions/iam_baseline.py")
    migration_content = migration_path.read_text(encoding="utf-8")

    assert "CREATE SCHEMA" in migration_content
    assert "sch_iam" in migration_content
    assert migration_content.count("op.create_table(") == 11
    assert "REVOKE" not in migration_content
    assert "DROP SCHEMA public" not in migration_content


def test_iam_baseline_does_not_change_alembic_metadata() -> None:
    migration_path = Path("alembic/versions/iam_baseline.py")
    migration_content = migration_path.read_text(encoding="utf-8")

    assert "alembic_version" not in migration_content


def test_alembic_ini_does_not_store_operational_database_credentials() -> None:
    alembic_ini_content = Path("alembic.ini").read_text(encoding="utf-8")
    previous_credentials = "guakamole" + ":" + "guakamole"
    previous_sync_url = "postgresql://" + "guakamole"
    previous_async_url = "postgresql+psycopg://" + "guakamole"

    assert previous_credentials not in alembic_ini_content
    assert previous_sync_url not in alembic_ini_content
    assert previous_async_url not in alembic_ini_content
    assert "driver://user:pass@localhost/dbname" in alembic_ini_content


def test_env_example_exposes_only_nonoperational_database_placeholders() -> None:
    env_example_content = Path("../.env.example").read_text(encoding="utf-8")
    assert "DATABASE_URL=postgresql+psycopg://<usuario>" in env_example_content
    assert "TEST_DATABASE_URL=" in env_example_content
    assert "guakamole_user" not in env_example_content


def test_alembic_env_reads_database_url_from_environment() -> None:
    alembic_env_content = Path("alembic/env.py").read_text(encoding="utf-8")

    assert 'DATABASE_URL_ENV_VAR = "DATABASE_URL"' in alembic_env_content
    assert 'SQLALCHEMY_URL_OPTION = "sqlalchemy.url"' in alembic_env_content
    assert "MISSING_DATABASE_URL_ERROR" in alembic_env_content
    assert "os.environ.get(DATABASE_URL_ENV_VAR)" in alembic_env_content
    expected_set_main_option = (
        "config.set_main_option(SQLALCHEMY_URL_OPTION, get_required_database_url())"
    )

    assert expected_set_main_option in alembic_env_content


def test_makefile_centralizes_environment_file_selection() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")

    assert "ENV_FILE ?= .env" in makefile_content
    assert "ENV_FILE_PATH :=" in makefile_content
    assert "COMPOSE := docker compose --env-file $(ENV_FILE)" in makefile_content
    assert "docker compose --env-file .env.example" not in makefile_content


def test_makefile_exposes_alembic_database_targets_with_env_file() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")
    expected_targets = {
        "db-upgrade:": "uv run alembic upgrade head",
        "db-current:": "uv run alembic current",
        "db-history:": "uv run alembic history",
        "db-downgrade:": "uv run alembic downgrade $(REVISION)",
    }

    for target, command in expected_targets.items():
        assert target in makefile_content
        assert command in makefile_content

    assert 'case "$$APP_ENV" in development|test)' in makefile_content
    assert "REVISION ?= -1" in makefile_content


def test_makefile_blocks_downgrade_outside_explicit_local_environments() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")

    assert "development|test" in makefile_content
    assert "sólo se permite en development/test" in makefile_content


def test_backend_dockerignore_excludes_environment_files() -> None:
    dockerignore_content = Path(".dockerignore").read_text(encoding="utf-8")

    assert ".env" in dockerignore_content
    assert ".env.*" in dockerignore_content
    assert "app" not in dockerignore_content
    assert "alembic" not in dockerignore_content


def test_makefile_groups_backend_quality_targets() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")
    expected_targets = {
        "backend-quality: backend-lint backend-format-check backend-mypy",
        (
            "backend-test: backend-quality backend-test-unit "
            "backend-test-db backend-test-security"
        ),
        'cd $(BACKEND_DIR) && uv run pytest -m "test_unit or architecture"',
        'TEST_DATABASE_URL="$$TEST_DATABASE_URL" uv run pytest -m "db or integration"',
        'cd $(BACKEND_DIR) && uv run pytest -m "security and not db"',
    }

    for expected_target in expected_targets:
        assert expected_target in makefile_content


def test_makefile_keeps_hidden_install_aliases() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")

    assert "setup: install" in makefile_content
    assert "backend-install: install" in makefile_content


def test_makefile_keeps_hidden_docker_and_postgres_targets() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")
    expected_targets = {
        "docker-config:",
        "docker-ps:",
        "postgres-up:",
        "postgres-logs:",
        "postgres-down:",
    }

    for target in expected_targets:
        assert target in makefile_content


def test_makefile_backend_check_validates_running_service() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")

    assert "backend-check: health-check ready-check" in makefile_content
    assert "curl -i $(API_BASE_URL)/api/health" in makefile_content
    assert "curl -i $(API_BASE_URL)/api/ready" in makefile_content


def test_makefile_exposes_psql_target() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")
    phony_line = makefile_content.splitlines()[0]

    assert phony_line.startswith(".PHONY:")
    assert "psql" in phony_line
    assert "psql:" in makefile_content
    assert "$(COMPOSE) up -d postgres" in makefile_content
    expected_psql_command = (
        "$(COMPOSE) exec postgres sh -c "
        '\'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"\''
    )

    assert expected_psql_command in makefile_content


def test_makefile_help_documents_primary_commands_only() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")
    help_block = makefile_content.split("install:", maxsplit=1)[0]
    hidden_commands = {
        "make setup",
        "make backend-install",
        "make backend-lint",
        "make backend-format-check",
        "make backend-mypy",
        "make backend-pytest",
        "make health-check",
        "make ready-check",
        "make docker-config",
        "make docker-ps",
        "make postgres-up",
        "make postgres-logs",
        "make postgres-down",
    }
    visible_commands = {
        "make install",
        "make backend-test",
        "make backend-check",
        "make backend-run",
        "make docker-up",
        "make docker-down",
        "make docker-logs",
        "make psql",
        "make db-upgrade",
        "make db-current",
        "make db-history",
        "make db-downgrade",
    }

    assert "ENV_FILE ?= .env" in makefile_content
    assert "REVISION ?= -1" in makefile_content
    assert "API_BASE_URL ?= http://localhost:8000" in makefile_content

    for command in visible_commands:
        assert command in help_block

    for command in hidden_commands:
        assert command not in help_block
