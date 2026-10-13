"""Fixtures compartidas para aislar estado mutable de tests."""

import os
from collections.abc import Iterator

import pytest

from app.core.config import reset_settings_cache
from app.core.rate_limit import reset_rate_limiter_state

DATABASE_TEST_SKIP_REASON = (
    "Requiere TEST_DATABASE_URL explícita; los tests de DB e integración no usan "
    "una base de datos alternativa."
)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Omite DB e integración si no se ha configurado su destino explícito."""

    del config
    if os.environ.get("TEST_DATABASE_URL"):
        return
    skip_database_tests = pytest.mark.skip(reason=DATABASE_TEST_SKIP_REASON)
    for item in items:
        if item.get_closest_marker("db") or item.get_closest_marker("integration"):
            item.add_marker(skip_database_tests)


@pytest.fixture(autouse=True)
def reset_in_memory_rate_limiter(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Evita que el singleton de rate limiting acople tests por orden."""

    monkeypatch.setenv(
        "JWT_SECRET_KEY", "test-secret-not-for-production-with-safe-length"
    )
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://test:test@localhost/test_db"
    )
    monkeypatch.delenv("JWT_SECRET", raising=False)
    reset_settings_cache()
    reset_rate_limiter_state()
    yield
    reset_rate_limiter_state()
    reset_settings_cache()
