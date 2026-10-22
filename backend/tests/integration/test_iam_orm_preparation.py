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


def test_alembic_env_requires_a_connection_validated_by_the_migrator() -> None:
    alembic_env_content = Path("alembic/env.py").read_text(encoding="utf-8")

    assert 'config.attributes.get("connection")' in alembic_env_content
    assert (
        "Alembic requiere una conexión validada por el migrador." in alembic_env_content
    )
    assert "engine_from_config" not in alembic_env_content


def test_makefile_centralizes_environment_file_selection() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")

    assert "ENV_FILE ?= .env" in makefile_content
    assert "ENV_FILE_PATH :=" in makefile_content
    assert (
        "COMPOSE_BASE := docker compose --env-file $(ENV_FILE) -f docker-compose.yml"
        in makefile_content
    )
    assert (
        "COMPOSE_LOCAL := $(COMPOSE_BASE) -f docker-compose.local.yml"
        in makefile_content
    )
    assert "docker compose --env-file .env.example" not in makefile_content


def test_makefile_exposes_restricted_compose_migration_targets() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")
    migrate_target = makefile_content.split("docker-db-migrate:", maxsplit=1)[1].split(
        "docker-db-current:", maxsplit=1
    )[0]
    current_target = makefile_content.split("docker-db-current:", maxsplit=1)[1].split(
        "docker-db-check:", maxsplit=1
    )[0]
    check_target = makefile_content.split("docker-db-check:", maxsplit=1)[1].split(
        "docker-deploy:", maxsplit=1
    )[0]

    assert "--profile migration run --build --rm migrate" in migrate_target
    assert "--profile migration run --build --rm migrate" in current_target
    assert "--profile migration run --build --rm migrate" in check_target
    assert "python -m scripts.migrate current" in current_target
    assert "python -m scripts.migrate check" in check_target
    assert "backend" not in migrate_target
    assert "backend" not in current_target
    assert "backend" not in check_target
    assert "uv run alembic" not in migrate_target
    assert "alembic history" not in makefile_content


def test_makefile_deprecates_unsupported_migration_targets() -> None:
    makefile_content = Path("../Makefile").read_text(encoding="utf-8")
    history_target = makefile_content.split("db-history:", maxsplit=1)[1].split(
        "db-downgrade:", maxsplit=1
    )[0]
    downgrade_target = makefile_content.split("db-downgrade:", maxsplit=1)[1].split(
        "health-check:", maxsplit=1
    )[0]

    assert "está obsoleto" in history_target
    assert "migrador seguro no admite histórico" in history_target
    assert "exit 1" in history_target
    assert "está obsoleto" in downgrade_target
    assert "migrador seguro rechaza downgrades" in downgrade_target
    assert "Docker de downgrade" in downgrade_target
    assert "exit 1" in downgrade_target


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
        "make docker-db-migrate",
        "make docker-db-current",
        "make docker-db-check",
        "make docker-deploy",
        "make docker-down",
        "make docker-logs",
        "make psql",
    }

    assert "ENV_FILE ?= .env" in help_block
    assert "API_BASE_URL ?= http://localhost:8000" in help_block
    assert "make db-history" not in help_block
    assert "make db-downgrade" not in help_block
    assert "Aplica upgrade head con el migrador aislado." in help_block
    assert "Consulta la revisión Alembic con el migrador aislado." in help_block
    assert (
        "Verifica que la revisión Alembic actual coincide con head mediante el "
        "migrador aislado."
    ) in help_block
    assert "Aplica migraciones y levanta el stack base de despliegue." in help_block

    for command in visible_commands:
        assert command in help_block

    for command in hidden_commands:
        assert command not in help_block
