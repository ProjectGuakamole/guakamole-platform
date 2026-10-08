"""Tests HTTP ligeros para POST /api/v1/auth/login."""

import pytest
from fastapi.testclient import TestClient

from app.domain.auth.login_exceptions import InvalidLoginCredentialsError
from app.domain.auth.login_routers import get_login_service
from app.domain.auth.login_schemas import LoginRequest, LoginTokenData
from app.main import create_app

pytestmark = pytest.mark.test_unit

COOKIE_VALUE = "jwt-test-value"


class StubLoginService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def login(self, request: LoginRequest) -> LoginTokenData:
        _ = request
        if self.error is not None:
            raise self.error
        return LoginTokenData(
            access_token=COOKIE_VALUE,
            user_public_id="usr_public",
            organization_public_id="org_public",
        )


def build_client(
    service: StubLoginService,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-production")
    app = create_app()
    app.dependency_overrides[get_login_service] = lambda: service
    return TestClient(app)


def test_login_endpoint_sets_httponly_cookie_without_body_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(StubLoginService(), monkeypatch)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@empresa.com", "password": "PasswordSeguro123!"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "authenticated"}
    assert "token" not in response.json()
    set_cookie = response.headers["set-cookie"]
    assert f"guak_access_token={COOKIE_VALUE}" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Path=/api" in set_cookie
    assert "SameSite=lax" in set_cookie


def test_login_endpoint_returns_generic_401_for_invalid_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(StubLoginService(InvalidLoginCredentialsError()), monkeypatch)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@empresa.com", "password": "bad"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas."


def test_login_endpoint_rejects_extra_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    client = build_client(StubLoginService(), monkeypatch)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "ana@empresa.com",
            "password": "PasswordSeguro123!",
            "organization_id": 1,
        },
    )

    assert response.status_code == 422


def test_login_endpoint_does_not_expose_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(StubLoginService(), monkeypatch)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@empresa.com", "password": "PasswordSeguro123!"},
    )

    body = response.json()
    assert "password_hash" not in body
    assert "id_user" not in body
    assert "id_organization" not in body
    assert "roles" not in body
    assert "jwt" not in body
