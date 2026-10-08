"""Tests HTTP ligeros para POST /api/v1/auth/logout."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

pytestmark = pytest.mark.test_unit


def build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-production")
    return TestClient(create_app())


def test_logout_returns_logged_out_and_deletes_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)
    client.cookies.set("guak_access_token", "invalid-or-expired-token")

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"status": "logged_out"}
    set_cookie = response.headers["set-cookie"]
    assert "guak_access_token=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/api" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "HttpOnly" in set_cookie


def test_logout_without_cookie_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    client = build_client(monkeypatch)

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"status": "logged_out"}
    assert "guak_access_token=" in response.headers["set-cookie"]


def test_logout_response_does_not_expose_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)

    response = client.post("/api/v1/auth/logout")

    body = response.json()
    assert "token" not in body
    assert "user_id" not in body
    assert "organization_id" not in body
    assert "email" not in body
    assert "roles" not in body


def test_logout_uses_cookie_settings_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-production")
    monkeypatch.setenv("AUTH_COOKIE_NAME", "custom_access_token")
    monkeypatch.setenv("AUTH_COOKIE_PATH", "/api/custom")
    monkeypatch.setenv("AUTH_COOKIE_SAMESITE", "strict")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("AUTH_COOKIE_DOMAIN", "example.test")
    client = TestClient(create_app())

    response = client.post("/api/v1/auth/logout")

    set_cookie = response.headers["set-cookie"]
    assert "custom_access_token=" in set_cookie
    assert "Path=/api/custom" in set_cookie
    assert "SameSite=strict" in set_cookie
    assert "Secure" in set_cookie
    assert "Domain=example.test" in set_cookie
