# ruff: noqa: I001

from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection

import app.db.model_registry as model_registry
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


_ = model_registry

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Prohíbe SQL offline: el wrapper debe validar el destino real."""

    raise RuntimeError("Las migraciones offline no están permitidas.")


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo online."""

    connection = config.attributes.get("connection")
    if connection is not None:
        if not isinstance(connection, Connection):
            raise RuntimeError("La conexión inyectada para Alembic no es válida.")
        _run_migrations_with_connection(connection)
        return

    raise RuntimeError("Alembic requiere una conexión validada por el migrador.")


def _run_migrations_with_connection(connection: Connection) -> None:
    """Configura y ejecuta Alembic sobre una conexión ya seleccionada."""

    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
