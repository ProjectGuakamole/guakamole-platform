"""Fixtures compartidas para aislar estado mutable de tests."""

from collections.abc import Iterator

import pytest

from app.core.config import reset_settings_cache
from app.core.rate_limit import reset_rate_limiter_state


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
