"""Fixtures compartidas para aislar estado mutable de tests."""

from collections.abc import Iterator

import pytest

from app.core.rate_limit import reset_rate_limiter_state


@pytest.fixture(autouse=True)
def reset_in_memory_rate_limiter() -> Iterator[None]:
    """Evita que el singleton de rate limiting acople tests por orden."""

    reset_rate_limiter_state()
    yield
    reset_rate_limiter_state()
