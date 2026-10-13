"""Operación explícita y destructiva para reconstruir la línea base IAM."""

from __future__ import annotations

from collections.abc import Mapping

from alembic.config import Config
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

from alembic import command
from app.core.test_database import uses_local_database_host

ALLOWED_ENVIRONMENTS = frozenset({"development", "test"})
CONFIRMATION_TOKEN = "REBASELINE_IAM"  # noqa: S105 - frase de confirmación, no secreto.
TEST_DATABASE_URL_ENV_VAR = "TEST_DATABASE_URL"
DEVELOPMENT_DATABASE_URL_ENV_VAR = "REBASELINE_DEVELOPMENT_DATABASE_URL"
DEVELOPMENT_DATABASE_SUFFIXES = ("_dev", "_development")


def validate_rebaseline_request(
    environment: Mapping[str, str], confirmation: str
) -> URL:
    """Valida que una reconstrucción destructiva sea inequívocamente segura."""

    if confirmation != CONFIRMATION_TOKEN:
        raise ValueError(
            "Confirmación destructiva inválida; usa exactamente REBASELINE_IAM."
        )
    app_env = environment.get("APP_ENV")
    if app_env not in ALLOWED_ENVIRONMENTS:
        raise ValueError(
            "La reconstrucción IAM sólo se permite con APP_ENV=development o test."
        )
    if app_env == "test":
        return _validate_test_database_url(environment)
    return _validate_development_database_url(environment)


def _parse_postgresql_url(raw_url: str, variable_name: str) -> URL:
    """Convierte una URL sin incluir sus posibles credenciales en los errores."""

    try:
        url = make_url(raw_url)
    except ArgumentError as error:
        message = f"{variable_name} debe apuntar a una base PostgreSQL concreta."
        raise ValueError(message) from error
    if url.get_backend_name() != "postgresql" or not url.database:
        message = f"{variable_name} debe apuntar a una base PostgreSQL concreta."
        raise ValueError(message)
    return url


def _validate_test_database_url(environment: Mapping[str, str]) -> URL:
    """Acepta exclusivamente la base aislada configurada para pruebas."""

    raw_url = environment.get(TEST_DATABASE_URL_ENV_VAR)
    if not raw_url:
        raise ValueError(
            "TEST_DATABASE_URL es obligatoria con APP_ENV=test; "
            "DATABASE_URL no se usa. "
            "Debe ser PostgreSQL y terminar en _test."
        )
    url = _parse_postgresql_url(raw_url, TEST_DATABASE_URL_ENV_VAR)
    database_name = url.database
    if database_name is None or not database_name.endswith("_test"):
        raise ValueError(
            "TEST_DATABASE_URL debe usar una base dedicada terminada en _test."
        )
    if not uses_local_database_host(url):
        raise ValueError(
            "TEST_DATABASE_URL debe usar localhost, 127.0.0.1, ::1 o un socket "
            "Unix local."
        )
    return url


def _validate_development_database_url(environment: Mapping[str, str]) -> URL:
    """Acepta sólo una base local dedicada para la operación destructiva."""

    raw_url = environment.get(DEVELOPMENT_DATABASE_URL_ENV_VAR)
    if not raw_url:
        raise ValueError(
            "REBASELINE_DEVELOPMENT_DATABASE_URL es obligatoria con "
            "APP_ENV=development; DATABASE_URL no se usa. Debe ser PostgreSQL "
            "local (localhost, 127.0.0.1, ::1 o socket Unix) y terminar en "
            "_dev o _development."
        )
    url = _parse_postgresql_url(raw_url, DEVELOPMENT_DATABASE_URL_ENV_VAR)
    database_name = url.database
    if database_name is None or not database_name.endswith(
        DEVELOPMENT_DATABASE_SUFFIXES
    ):
        raise ValueError(
            "REBASELINE_DEVELOPMENT_DATABASE_URL debe usar una base dedicada "
            "terminada en _dev o _development."
        )
    if not uses_local_database_host(url):
        raise ValueError(
            "REBASELINE_DEVELOPMENT_DATABASE_URL debe usar localhost, 127.0.0.1, "
            "::1 o un socket Unix local."
        )
    return url


def rebuild_iam_baseline(engine: Engine, alembic_config: Config) -> None:
    """Elimina IAM y el estado Alembic para aplicar la única línea base actual."""

    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS sch_iam CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS public.alembic_version"))
        _upgrade_with_connection(alembic_config, connection)


def _upgrade_with_connection(alembic_config: Config, connection: Connection) -> None:
    """Ejecuta Alembic con la misma conexión del destino ya validado.

    ``alembic.env`` reconoce este atributo estándar. Conservar la conexión dentro
    de la transacción también evita que Alembic resuelva ``DATABASE_URL``.
    """

    connection_key = "connection"
    previous_connection = alembic_config.attributes.get(connection_key)
    had_previous_connection = connection_key in alembic_config.attributes
    alembic_config.attributes[connection_key] = connection
    try:
        command.upgrade(alembic_config, "head")
    finally:
        if had_previous_connection:
            alembic_config.attributes[connection_key] = previous_connection
        else:
            alembic_config.attributes.pop(connection_key, None)


def rebaseline_configured_database(
    environment: Mapping[str, str], confirmation: str, alembic_config: Config
) -> None:
    """Reconstruye la base configurada tras validar entorno y confirmación."""

    url = validate_rebaseline_request(environment, confirmation)
    engine = create_engine(url, hide_parameters=True)
    try:
        rebuild_iam_baseline(engine, alembic_config)
    finally:
        engine.dispose()
