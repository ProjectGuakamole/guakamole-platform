from app.core.health.schemas import (
    DependencyStatus,
    HealthResponse,
    HealthStatus,
    ReadinessDependencies,
    ReadinessResponse,
    ReadinessStatus,
)


def test_health_response_serializes_status_ok() -> None:
    response = HealthResponse(status=HealthStatus.OK)

    assert response.model_dump(mode="json") == {"status": "ok"}


def test_readiness_response_serializes_ready_dependencies() -> None:
    response = ReadinessResponse(
        status=ReadinessStatus.READY,
        dependencies=ReadinessDependencies(
            database=DependencyStatus.OK,
        ),
    )

    assert response.model_dump(mode="json") == {
        "status": "ready",
        "dependencies": {
            "database": "ok",
        },
    }


def test_readiness_response_serializes_failed_dependency() -> None:
    response = ReadinessResponse(
        status=ReadinessStatus.NOT_READY,
        dependencies=ReadinessDependencies(
            database=DependencyStatus.FAILED,
        ),
    )

    assert response.model_dump(mode="json") == {
        "status": "not_ready",
        "dependencies": {
            "database": "failed",
        },
    }


def test_health_status_values_are_stable() -> None:
    assert HealthStatus.OK.value == "ok"


def test_readiness_status_values_are_stable() -> None:
    assert ReadinessStatus.READY.value == "ready"
    assert ReadinessStatus.NOT_READY.value == "not_ready"


def test_dependency_status_values_are_stable() -> None:
    assert DependencyStatus.OK.value == "ok"
    assert DependencyStatus.FAILED.value == "failed"
