"""Verifica el camino real migrador/aplicación contra PostgreSQL de integración."""

import os

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ProgrammingError

from app.core import migrations
from app.core.config import reset_settings_cache
from app.core.health import checks
from app.core.health.schemas import DependencyStatus
from app.db.session import get_engine

pytestmark = [pytest.mark.integration, pytest.mark.db]

ROLE_ENVIRONMENT_VARIABLES = (
    "MIGRATION_DATABASE_URL",
    "MIGRATION_ALLOWED_HOSTS",
    "MIGRATION_ALLOWED_DATABASES",
    "MIGRATION_EXPECTED_DB_USER",
    "APP_DB_PASSWORD",
)


def _alembic_head_revision() -> str:
    """Obtiene la única revisión cabeza configurada para este proyecto."""
    revisions = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    assert len(revisions) == 1, (
        "El historial de migraciones debe tener una única cabeza."
    )
    return revisions[0]


def _localhost_url(url: str) -> URL:
    """Adapta el destino de Compose para la conexión desde el host."""
    return make_url(url).set(host="localhost")


def _application_url(migration_url: URL, app_password: str) -> URL:
    """Reutiliza el destino del migrador con credenciales de aplicación."""
    return migration_url.set(username="guakamole_app", password=app_password)


def _require_compose_role_environment(environment: dict[str, str]) -> None:
    """Omite esta comprobación fuera del entorno de roles de Compose."""
    missing_variables = [
        variable
        for variable in ROLE_ENVIRONMENT_VARIABLES
        if not environment.get(variable)
    ]
    if missing_variables:
        variables = ", ".join(missing_variables)
        pytest.skip(
            "Requiere el entorno de roles de Compose; faltan variables dedicadas: "
            f"{variables}."
        )


def test_migrator_and_application_roles_have_separate_operational_access() -> None:
    environment = dict(os.environ)
    _require_compose_role_environment(environment)
    migration_url = _localhost_url(environment["MIGRATION_DATABASE_URL"])
    environment["MIGRATION_DATABASE_URL"] = migration_url.render_as_string(
        hide_password=False
    )
    environment["MIGRATION_ALLOWED_HOSTS"] = "postgres,localhost"

    assert migrations.run_migration_command(("upgrade", "head"), environment) == 0

    app_url = _application_url(
        migration_url,
        environment["APP_DB_PASSWORD"],
    )
    expected_revision = _alembic_head_revision()
    engine = create_engine(app_url, hide_parameters=True)
    try:
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT version_num FROM public.alembic_version")
                ).scalar_one()
                == expected_revision
            )
            assert (
                connection.execute(
                    text("SELECT 1 FROM sch_iam.tbl_status LIMIT 1")
                ).all()
                == []
            )
            with pytest.raises(ProgrammingError):
                connection.execute(text("CREATE SCHEMA prohibited_for_application"))
    finally:
        engine.dispose()

    previous_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = app_url.render_as_string(hide_password=False)
    reset_settings_cache()
    get_engine.cache_clear()
    try:
        assert checks.check_database() is DependencyStatus.OK
    finally:
        get_engine.cache_clear()
        reset_settings_cache()
        if previous_url is None:
            del os.environ["DATABASE_URL"]
        else:
            os.environ["DATABASE_URL"] = previous_url
