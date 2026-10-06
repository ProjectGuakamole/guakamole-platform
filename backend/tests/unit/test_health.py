import pytest
from fastapi.testclient import TestClient

from app.api import health as health_api
from app.core.health.schemas import (
    DependencyStatus,
    ReadinessDependencies,
    ReadinessResponse,
    ReadinessStatus,
)
from app.main import app

pytestmark = pytest.mark.test_unit


def test_versioned_health_check_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_operational_health_check_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_operational_health_check_does_not_call_readiness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called() -> ReadinessResponse:
        raise AssertionError("readiness must not be called by liveness")

    monkeypatch.setattr(health_api, "get_readiness_status", fail_if_called)
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_returns_ready_when_database_is_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def readiness_ok() -> ReadinessResponse:
        return ReadinessResponse(
            status=ReadinessStatus.READY,
            dependencies=ReadinessDependencies(database=DependencyStatus.OK),
        )

    monkeypatch.setattr(health_api, "get_readiness_status", readiness_ok)
    client = TestClient(app)

    response = client.get("/api/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": {"database": "ok"},
    }


def test_readiness_check_returns_service_unavailable_when_database_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def readiness_failed() -> ReadinessResponse:
        return ReadinessResponse(
            status=ReadinessStatus.NOT_READY,
            dependencies=ReadinessDependencies(database=DependencyStatus.FAILED),
        )

    monkeypatch.setattr(health_api, "get_readiness_status", readiness_failed)
    client = TestClient(app)

    response = client.get("/api/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "dependencies": {"database": "failed"},
    }
