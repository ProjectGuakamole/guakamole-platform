import json

import pytest
from alembic.config import Config
from sqlalchemy import Engine

from alembic import command as alembic_command
from app.core import migrations


def _environment(**overrides: str) -> dict[str, str]:
    environment = {
        "APP_ENV": "test",
        "MIGRATION_DATABASE_URL": (
            "postgresql+psycopg://guakamole_migrator:private@postgres:5432/guakamole"
        ),
        "MIGRATION_ALLOWED_HOSTS": "postgres",
        "MIGRATION_ALLOWED_DATABASES": "guakamole",
        "MIGRATION_EXPECTED_DB_USER": "guakamole_migrator",
    }
    environment.update(overrides)
    return environment


@pytest.mark.test_unit
@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (("upgrade", "head"), ("upgrade", "head")),
        (("current",), ("current",)),
        (("check",), ("check",)),
    ],
)
def test_parse_command_accepts_only_safe_commands(
    arguments: tuple[str, ...], expected: tuple[str, ...]
) -> None:
    assert migrations.parse_command(arguments) == expected


@pytest.mark.test_unit
@pytest.mark.parametrize(
    "arguments",
    [("upgrade", "base"), ("downgrade", "-1"), ("history",), ()],
)
def test_parse_command_rejects_arbitrary_revisions(arguments: tuple[str, ...]) -> None:
    with pytest.raises(migrations.MigrationSafetyError):
        migrations.parse_command(arguments)


@pytest.mark.test_unit
@pytest.mark.parametrize(
    "overrides",
    [
        {"APP_ENV": "unsafe"},
        {"MIGRATION_DATABASE_URL": "sqlite:///unsafe.db"},
        {"MIGRATION_ALLOWED_HOSTS": "other-host"},
        {"MIGRATION_ALLOWED_DATABASES": "other-database"},
        {"MIGRATION_EXPECTED_DB_USER": "other-user"},
    ],
)
def test_target_rejects_unapproved_configuration(overrides: dict[str, str]) -> None:
    with pytest.raises(migrations.MigrationSafetyError):
        migrations.get_migration_target(_environment(**overrides))


@pytest.mark.test_unit
def test_cli_does_not_emit_the_database_secret(
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret_url = "postgresql+psycopg://user:" + "test-password" + "@host:5432/database"

    exit_code = migrations.main(("downgrade", secret_url))

    output = capsys.readouterr().out
    assert exit_code == 1
    assert secret_url not in output
    assert "top-secret" not in output
    assert json.loads(output) == {"event": "migration", "outcome": "failed"}


@pytest.mark.test_unit
def test_invalid_target_exits_with_controlled_json_without_creating_an_engine(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_if_called(_: migrations.MigrationTarget) -> Engine:
        raise AssertionError("No se debe crear el motor para un destino inválido")

    monkeypatch.setattr(migrations, "_make_engine", fail_if_called)

    exit_code = migrations.run_migration_command(
        ("upgrade", "head"), _environment(APP_ENV="unsafe")
    )

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out) == {
        "event": "migration",
        "outcome": "failed",
    }


@pytest.mark.test_unit
def test_operational_grants_are_limited_to_iam_data_access() -> None:
    assert migrations._iam_operational_grants() == (
        "GRANT USAGE ON SCHEMA sch_iam TO guakamole_app",
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
        "IN SCHEMA sch_iam TO guakamole_app",
        "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sch_iam TO guakamole_app",
        "ALTER DEFAULT PRIVILEGES FOR ROLE guakamole_migrator "
        "IN SCHEMA sch_iam GRANT SELECT, INSERT, UPDATE, DELETE "
        "ON TABLES TO guakamole_app",
        "ALTER DEFAULT PRIVILEGES FOR ROLE guakamole_migrator "
        "IN SCHEMA sch_iam GRANT USAGE, SELECT ON SEQUENCES "
        "TO guakamole_app",
        "GRANT SELECT ON TABLE public.alembic_version TO guakamole_app",
    )


@pytest.mark.test_unit
@pytest.mark.parametrize(
    ("command", "current", "head", "expected"),
    [
        (("check",), "revision_head", "revision_head", "check_ok"),
        (("check",), "revision_pending", "revision_head", "pending"),
        (("check",), None, "revision_head", "pending"),
        (("current",), "revision_head", "revision_head", "at_head"),
        (("current",), "revision_pending", "revision_head", "pending"),
    ],
)
def test_read_only_commands_compare_only_current_revision_to_single_head(
    command: tuple[str, ...],
    current: str | None,
    head: str,
    expected: str,
) -> None:
    assert migrations._run_read_only_command(command, current, head) == expected


@pytest.mark.test_unit
def test_check_does_not_run_alembic_autogenerate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(_: Config) -> None:
        raise AssertionError("No se debe ejecutar la comprobación de autogeneración")

    monkeypatch.setattr(alembic_command, "check", fail_if_called)

    assert (
        migrations._run_read_only_command(("check",), "revision_head", "revision_head")
        == "check_ok"
    )
