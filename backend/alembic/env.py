import os
from importlib import import_module
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def import_models() -> None:
    """Importa modelos ORM para registrarlos en Base.metadata."""

    import_module("app.domain.iam.access.models")
    import_module("app.domain.iam.geography.models")
    import_module("app.domain.iam.organizations.models")
    import_module("app.domain.iam.users.models")


import_models()

target_metadata = Base.metadata

DATABASE_URL_ENV_VAR = "DATABASE_URL"
SQLALCHEMY_URL_OPTION = "sqlalchemy.url"
MISSING_DATABASE_URL_ERROR = (
    f"La variable de entorno {DATABASE_URL_ENV_VAR} debe estar definida "
    "para ejecutar migraciones Alembic online."
)


def get_database_url() -> str | None:
    """Obtiene la URL de base de datos desde el entorno."""

    return os.environ.get(DATABASE_URL_ENV_VAR)


def get_required_database_url() -> str:
    """Obtiene la URL de base de datos para migraciones online."""

    database_url = get_database_url()
    if database_url is None or database_url == "":
        raise RuntimeError(MISSING_DATABASE_URL_ERROR)
    return database_url


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline."""

    url = get_database_url() or config.get_main_option(SQLALCHEMY_URL_OPTION)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo online."""

    config.set_main_option(SQLALCHEMY_URL_OPTION, get_required_database_url())
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
