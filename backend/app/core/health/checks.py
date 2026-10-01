from collections.abc import Callable

from app.core.health.schemas import (
    DependencyStatus,
    ReadinessDependencies,
    ReadinessResponse,
    ReadinessStatus,
)


class _DatabaseProbeNotConfiguredError(RuntimeError):
    """Raised when the database probe cannot run safely yet."""


def _probe_database() -> None:
    """Run the database probe.

    There is no centralized database configuration or shared engine/session yet.
    Failing closed prevents readiness from reporting OK without verifying
    PostgreSQL. When that configuration exists, this function must execute a
    short-timeout query equivalent to SELECT 1.
    """
    raise _DatabaseProbeNotConfiguredError


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
