from collections.abc import Callable

from app.core.health.schemas import (
    DependencyStatus,
    ReadinessDependencies,
    ReadinessResponse,
    ReadinessStatus,
)


def _probe_database() -> None:
    """Placeholder for the future lightweight database probe.

    When centralized database configuration exists, this function will execute a
    short-timeout query equivalent to SELECT 1 without exposing infrastructure
    details to API responses.
    """


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
