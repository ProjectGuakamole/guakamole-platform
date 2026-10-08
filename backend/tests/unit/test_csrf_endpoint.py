"""Tests HTTP ligeros para GET /api/v1/auth/csrf."""

import pytest
from fastapi.testclient import TestClient

from app.domain.auth.config import AuthSettings
from app.domain.auth.tokens import JwtAccessTokenService
from app.main import create_app

pytestmark = pytest.mark.test_unit


def build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-production")
    return TestClient(create_app())


def test_csrf_without_cookie_returns_generic_401(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)

    response = client.get("/api/v1/auth/csrf")

    assert response.status_code == 401
    assert response.json() == {"detail": "No autenticado."}


def test_csrf_with_valid_access_cookie_returns_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)
    settings = AuthSettings.model_validate(
        {"jwt_secret_key": "test-secret-not-for-production"},
    )
    access_token = JwtAccessTokenService(settings).issue_access_token("usr_123")
    client.cookies.set("guak_access_token", access_token)

    response = client.get("/api/v1/auth/csrf")

    body = response.json()
    assert response.status_code == 200
    assert isinstance(body["csrf_token"], str)
    assert body["csrf_token"]
    assert body["csrf_token"] != access_token
    assert "user_id" not in body
    assert "email" not in body
    assert "roles" not in body
    assert "organization_id" not in body
