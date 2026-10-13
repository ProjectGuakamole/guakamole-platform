"""Tests HTTP ligeros para GET /api/v1/auth/csrf."""

import pytest
from fastapi.testclient import TestClient

from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.session_dependencies import get_auth_session_service
from app.domains.auth.shared.session_repository import ActiveSessionIdentity
from app.domains.auth.shared.tokens import JwtAccessTokenService
from app.main import create_app

pytestmark = pytest.mark.test_unit


class StubSessionService:
    def __init__(self, settings: AuthSettings) -> None:
        self._tokens = JwtAccessTokenService(settings)

    def validate(self, raw_token: str) -> tuple[object, ActiveSessionIdentity]:
        return self._tokens.verify_access_token(raw_token), ActiveSessionIdentity(
            "usr_123", "org_123"
        )


def build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv(
        "JWT_SECRET_KEY", "test-secret-not-for-production-with-safe-length"
    )
    app = create_app()
    settings = AuthSettings.model_validate(
        {
            "app_env": "test",
            "database_url": "postgresql+psycopg://test:test@localhost/guakamole_test",
            "jwt_secret_key": "test-secret-not-for-production-with-safe-length",
        },
    )
    app.dependency_overrides[get_auth_session_service] = lambda: StubSessionService(
        settings
    )
    return TestClient(app)


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
    settings = AuthSettings.model_validate(
        {
            "app_env": "test",
            "database_url": "postgresql+psycopg://test:test@localhost/guakamole_test",
            "jwt_secret_key": "test-secret-not-for-production-with-safe-length",
        },
    )
    access_token = JwtAccessTokenService(settings).issue_access_token("usr_123")
    client = build_client(monkeypatch)
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
