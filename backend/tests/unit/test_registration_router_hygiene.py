"""Tests de higiene del router de registro inicial."""

from pathlib import Path

import pytest

REGISTRATION_ROUTER_PATH = (
    Path(__file__).parents[2]
    / "app"
    / "domain"
    / "iam"
    / "organizations"
    / "registration_routers.py"
)


@pytest.mark.test_unit
def test_registration_router_does_not_use_unsafe_secret_fallbacks() -> None:
    router_source = REGISTRATION_ROUTER_PATH.read_text(encoding="utf-8")

    assert "registration-only" not in router_source
    assert "JWT_SECRET_KEY" not in router_source
    assert "os.environ" not in router_source
