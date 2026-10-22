"""Operaciones seguras y explícitas para el estado de Alembic."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.pool import NullPool

from alembic import command

_ALLOWED_COMMANDS = {("upgrade", "head"), ("current",), ("check",)}
_ALLOWED_ENVIRONMENTS = {"development", "test", "staging", "production"}
_LOCK_KEY = 721_403_119
_APPLICATION_ROLE = "guakamole_app"
_IAM_SCHEMA = "sch_iam"


class MigrationSafetyError(Exception):
    """Error controlado que no debe revelar detalles de infraestructura."""


@dataclass(frozen=True)
class MigrationTarget:
    url: str
    host: str
    database: str
    username: str


def emit_event(event: str, outcome: str) -> None:
    """Emite un evento estructurado sin incluir configuración sensible."""

    print(json.dumps({"event": event, "outcome": outcome}, sort_keys=True))


def parse_command(arguments: Sequence[str]) -> tuple[str, ...]:
    command_arguments = tuple(arguments)
    if command_arguments not in _ALLOWED_COMMANDS:
        raise MigrationSafetyError("comando no permitido")
    return command_arguments


def _csv_value(environment: Mapping[str, str], name: str) -> set[str]:
    values = {value.strip() for value in environment.get(name, "").split(",")}
    values.discard("")
    if not values:
        raise MigrationSafetyError("configuración de destino incompleta")
    return values


def get_migration_target(environment: Mapping[str, str]) -> MigrationTarget:
    """Valida el único destino permitido para el proceso migrador."""

    if environment.get("APP_ENV") not in _ALLOWED_ENVIRONMENTS:
        raise MigrationSafetyError("entorno no permitido")
    raw_url = environment.get("MIGRATION_DATABASE_URL")
    if not raw_url:
        raise MigrationSafetyError("configuración de migración incompleta")
    try:
        url = make_url(raw_url)
    except (ArgumentError, ValueError) as error:
        raise MigrationSafetyError("URL de migración inválida") from error
    if url.drivername not in {"postgresql", "postgresql+psycopg"}:
        raise MigrationSafetyError("dialecto de migración no permitido")
    host, database, username = url.host, url.database, url.username
    if not host or not database or not username:
        raise MigrationSafetyError("URL de migración incompleta")
    if host not in _csv_value(environment, "MIGRATION_ALLOWED_HOSTS"):
        raise MigrationSafetyError("destino de migración no autorizado")
    if database not in _csv_value(environment, "MIGRATION_ALLOWED_DATABASES"):
        raise MigrationSafetyError("destino de migración no autorizado")
    if username != environment.get("MIGRATION_EXPECTED_DB_USER"):
        raise MigrationSafetyError("usuario de migración no autorizado")
    return MigrationTarget(raw_url, host, database, username)


def _make_engine(target: MigrationTarget) -> Engine:
    return create_engine(target.url, hide_parameters=True, poolclass=NullPool)


def _head_revision(config: Config) -> str:
    heads = ScriptDirectory.from_config(config).get_heads()
    if len(heads) != 1:
        raise MigrationSafetyError("historial de migraciones no lineal")
    return heads[0]


def _current_revision(connection: Connection) -> str | None:
    return MigrationContext.configure(connection).get_current_revision()


def _validate_database_identity(
    connection: Connection, target: MigrationTarget
) -> None:
    row = connection.execute(text("SELECT current_database(), current_user")).one()
    if row[0] != target.database or row[1] != target.username:
        raise MigrationSafetyError("identidad de destino no autorizada")


def _validate_revision(current: str | None, script: ScriptDirectory) -> None:
    if current is None:
        return
    if script.get_revision(current) is None:
        raise MigrationSafetyError("revisión de base de datos desconocida")


def _alembic_config(connection: Connection) -> Config:
    config = Config("alembic.ini")
    config.attributes["connection"] = connection
    return config


def _grant_iam_operational_access(connection: Connection) -> None:
    """Concede al rol de aplicación sólo el acceso operativo al esquema IAM."""

    schema_exists = connection.execute(
        text("SELECT to_regnamespace(:schema) IS NOT NULL"),
        {"schema": _IAM_SCHEMA},
    ).scalar_one()
    if not schema_exists:
        return
    for statement in _iam_operational_grants():
        connection.execute(text(statement))


def _iam_operational_grants() -> tuple[str, ...]:
    return (
        f"GRANT USAGE ON SCHEMA {_IAM_SCHEMA} TO {_APPLICATION_ROLE}",
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
        f"IN SCHEMA {_IAM_SCHEMA} TO {_APPLICATION_ROLE}",
        "GRANT USAGE, SELECT ON ALL SEQUENCES "
        f"IN SCHEMA {_IAM_SCHEMA} TO {_APPLICATION_ROLE}",
        "ALTER DEFAULT PRIVILEGES FOR ROLE guakamole_migrator "
        f"IN SCHEMA {_IAM_SCHEMA} GRANT SELECT, INSERT, UPDATE, DELETE "
        f"ON TABLES TO {_APPLICATION_ROLE}",
        "ALTER DEFAULT PRIVILEGES FOR ROLE guakamole_migrator "
        f"IN SCHEMA {_IAM_SCHEMA} GRANT USAGE, SELECT ON SEQUENCES "
        f"TO {_APPLICATION_ROLE}",
        f"GRANT SELECT ON TABLE public.alembic_version TO {_APPLICATION_ROLE}",
    )


def _run_upgrade(connection: Connection, config: Config, head: str) -> str:
    connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _LOCK_KEY})
    current = _current_revision(connection)
    _validate_revision(current, ScriptDirectory.from_config(config))
    if current == head:
        _grant_iam_operational_access(connection)
        return "already_at_head"
    command.upgrade(config, "head")
    _grant_iam_operational_access(connection)
    return "upgraded"


def _run_read_only_command(
    selected: tuple[str, ...],
    current: str | None,
    head: str,
) -> str:
    """Informa del estado de revisión sin inspeccionar los metadatos ORM.

    ``alembic check`` ejecuta la comparación de autogeneración contra
    ``target_metadata``. El migrador sólo debe comprobar si la revisión de la
    base de datos coincide con la única cabeza empaquetada.
    """

    if selected == ("current",):
        return "at_head" if current == head else "pending"
    return "check_ok" if current == head else "pending"


def run_migration_command(
    arguments: Sequence[str], environment: Mapping[str, str]
) -> int:
    """Ejecuta solamente comandos Alembic permitidos bajo bloqueo PostgreSQL."""

    engine: Engine | None = None
    try:
        selected = parse_command(arguments)
        target = get_migration_target(environment)
        engine = _make_engine(target)
        with engine.connect() as connection, connection.begin():
            if selected != ("upgrade", "head"):
                connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL lock_timeout = '5s'"))
            connection.execute(text("SET LOCAL statement_timeout = '60s'"))
            _validate_database_identity(connection, target)
            config = _alembic_config(connection)
            script = ScriptDirectory.from_config(config)
            current = _current_revision(connection)
            _validate_revision(current, script)
            head = _head_revision(config)
            if selected == ("upgrade", "head"):
                outcome = _run_upgrade(connection, config, head)
            else:
                outcome = _run_read_only_command(selected, current, head)
        emit_event("migration", outcome)
    except Exception:
        # Frontera del proceso privilegiado: nunca se propagan detalles del destino.
        emit_event("migration", "failed")
        return 1
    finally:
        if engine is not None:
            engine.dispose()
    return 0


def main(arguments: Sequence[str] | None = None) -> int:
    """Punto de entrada silencioso y seguro para el contenedor migrador."""

    return run_migration_command(arguments or sys.argv[1:], os.environ)
