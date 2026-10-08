"""Tests HTTP ligeros para GET /api/v1/auth/me."""

import pytest
from fastapi.testclient import TestClient

from app.domain.auth.me_routers import get_auth_me_service
from app.domain.auth.me_schemas import AuthMeResponse
from app.main import create_app

pytestmark = pytest.mark.test_unit
COOKIE_VALUE = "jwt-" + "test-value"


class StubAuthMeService:
    def get_current_identity(self, token: str) -> AuthMeResponse:
        assert token == COOKIE_VALUE
        return AuthMeResponse(
            authenticated=True,
            user_id="usr_public",
            organization_id="org_public",
        )


def build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-production")
    app = create_app()
    app.dependency_overrides[get_auth_me_service] = lambda: StubAuthMeService()
    return TestClient(app)


def test_auth_me_without_cookie_returns_generic_401(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "No autenticado."}


def test_auth_me_with_valid_cookie_returns_public_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(monkeypatch)
    client.cookies.set("guak_access_token", COOKIE_VALUE)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "authenticated": True,
        "user_id": "usr_public",
        "organization_id": "org_public",
    }
    assert "email" not in response.json()
    assert "roles" not in response.json()
    assert "token" not in response.json()
    assert "id_user" not in response.json()
    assert "id_organization" not in response.json()
