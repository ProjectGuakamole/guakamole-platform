from collections.abc import Callable

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.health.schemas import (
    DependencyStatus,
    ReadinessDependencies,
    ReadinessResponse,
    ReadinessStatus,
)
from app.db.session import get_engine


def _probe_database() -> None:
    """Comprueba PostgreSQL y que su revisión coincide con el head empaquetado."""

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
            current = connection.execute(
                text("SELECT version_num FROM public.alembic_version")
            ).scalar_one_or_none()
        heads = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    except SQLAlchemyError as error:
        raise RuntimeError("base de datos no disponible") from error
    if len(heads) != 1 or current != heads[0]:
        raise RuntimeError("esquema no preparado")


def _check_dependency(probe: Callable[[], None]) -> DependencyStatus:
    try:
        probe()
    except Exception:
        return DependencyStatus.FAILED
    return DependencyStatus.OK


def check_database() -> DependencyStatus:
    return _check_dependency(_probe_database)


def get_readiness_status() -> ReadinessResponse:
    dependencies = ReadinessDependencies(database=check_database())
    status = (
        ReadinessStatus.READY
        if dependencies.database is DependencyStatus.OK
        else ReadinessStatus.NOT_READY
    )
    return ReadinessResponse(status=status, dependencies=dependencies)
