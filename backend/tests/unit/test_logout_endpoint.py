"""Tests HTTP ligeros para POST /api/v1/auth/logout."""

import pytest
from fastapi.testclient import TestClient

from app.domain.auth.config import AuthSettings
from app.domain.auth.csrf_services import CsrfTokenService
from app.domain.auth.tokens import JwtAccessTokenService
from app.main import create_app

pytestmark = pytest.mark.test_unit


def build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-production")
    return TestClient(create_app())


def auth_settings() -> AuthSettings:
    return AuthSettings.model_validate(
        {"jwt_secret_key": "test-secret-not-for-production"},
    )


def issue_access_and_csrf(subject: str = "usr_123") -> tuple[str, str]:
    settings = auth_settings()
    access_service = JwtAccessTokenService(settings)
    access_token = access_service.issue_access_token(subject)
    verified_access_token = access_service.verify_access_token(access_token)
    csrf_token = CsrfTokenService(settings).issue_csrf_token(verified_access_token)
    return access_token, csrf_token


def test_logout_returns_logged_out_and_deletes_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)
    access_token, csrf_token = issue_access_and_csrf()
    client.cookies.set("guak_access_token", access_token)

    response = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "logged_out"}
    set_cookie = response.headers["set-cookie"]
    assert "guak_access_token=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/api" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "HttpOnly" in set_cookie


def test_logout_without_cookie_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    client = build_client(monkeypatch)

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 401
    assert response.json() == {"detail": "No autenticado."}


def test_logout_with_valid_cookie_without_csrf_returns_403(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)
    access_token, _ = issue_access_and_csrf()
    client.cookies.set("guak_access_token", access_token)

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 403
    assert response.json() == {"detail": "CSRF inválido."}


def test_logout_response_does_not_expose_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)
    access_token, csrf_token = issue_access_and_csrf()
    client.cookies.set("guak_access_token", access_token)

    response = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )

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
    access_token, csrf_token = issue_access_and_csrf()
    client.cookies.set("custom_access_token", access_token)

    response = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )

    set_cookie = response.headers["set-cookie"]
    assert "custom_access_token=" in set_cookie
    assert "Path=/api/custom" in set_cookie
    assert "SameSite=strict" in set_cookie
    assert "Secure" in set_cookie
    assert "Domain=example.test" in set_cookie


def test_logout_rejects_csrf_from_other_access_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)
    access_token, _ = issue_access_and_csrf("usr_123")
    _, other_csrf_token = issue_access_and_csrf("usr_123")
    client.cookies.set("guak_access_token", access_token)

    response = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": other_csrf_token},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "CSRF inválido."}
