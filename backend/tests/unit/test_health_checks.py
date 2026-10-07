import pytest

from app.core.health import checks
from app.core.health.schemas import DependencyStatus, ReadinessStatus

pytestmark = pytest.mark.test_unit


def _successful_probe() -> None:
    return None


def _failing_probe() -> None:
    msg = "simulated dependency failure"
    raise RuntimeError(msg)


def test_check_database_returns_ok_when_probe_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checks, "_probe_database", _successful_probe)

    assert checks.check_database() is DependencyStatus.OK


def test_check_database_returns_failed_when_probe_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checks, "_probe_database", _failing_probe)

    assert checks.check_database() is DependencyStatus.FAILED


def test_check_database_returns_failed_when_probe_is_not_configured_by_default() -> (
    None
):
    assert checks.check_database() is DependencyStatus.FAILED


def test_get_readiness_status_returns_ready_when_database_is_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checks, "_probe_database", _successful_probe)

    response = checks.get_readiness_status()

    assert response.status is ReadinessStatus.READY
    assert response.dependencies.database is DependencyStatus.OK


def test_get_readiness_status_returns_not_ready_when_database_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checks, "_probe_database", _failing_probe)

    response = checks.get_readiness_status()

    assert response.status is ReadinessStatus.NOT_READY
    assert response.dependencies.database is DependencyStatus.FAILED
