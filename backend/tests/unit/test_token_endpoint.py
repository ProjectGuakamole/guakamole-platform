"""Tests HTTP ligeros para POST /api/v1/auth/token."""

import pytest
from fastapi.testclient import TestClient

from app.domains.auth.login_exceptions import InvalidLoginCredentialsError
from app.domains.auth.login_routers import get_login_service
from app.domains.auth.login_schemas import LoginRequest, LoginTokenData
from app.main import create_app

pytestmark = pytest.mark.test_unit

ACCESS_TOKEN = "jwt-test-value"  # noqa: S105 - Token opaco ficticio para tests.


class StubLoginService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls = 0
        self.last_request: LoginRequest | None = None

    def login(self, request: LoginRequest) -> LoginTokenData:
        self.calls += 1
        self.last_request = request
        if self.error is not None:
            raise self.error
        return LoginTokenData(
            access_token=ACCESS_TOKEN,
            user_public_id="usr_public",
            organization_public_id="org_public",
        )


def build_client(
    service: StubLoginService,
    monkeypatch: pytest.MonkeyPatch,
    *,
    bearer_enabled: bool = True,
    access_token_expire_minutes: int = 15,
) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-production")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(access_token_expire_minutes))
    monkeypatch.setenv(
        "AUTH_ENABLE_PASSWORD_BEARER_TOKEN",
        "true" if bearer_enabled else "false",
    )
    app = create_app()
    app.dependency_overrides[get_login_service] = lambda: service
    return TestClient(app)


def test_token_endpoint_returns_bearer_token_without_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(StubLoginService(), monkeypatch)

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "ana@empresa.com", "password": "PasswordSeguro123!"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": ACCESS_TOKEN,
        "token_type": "bearer",
        "expires_in": 900,
    }
    assert "set-cookie" not in response.headers


def test_token_endpoint_uses_configured_expiration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(
        StubLoginService(),
        monkeypatch,
        access_token_expire_minutes=30,
    )

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "ana@empresa.com", "password": "PasswordSeguro123!"},
    )

    assert response.status_code == 200
    assert response.json()["expires_in"] == 1800


def test_token_endpoint_does_not_expose_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(StubLoginService(), monkeypatch)

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "ana@empresa.com", "password": "PasswordSeguro123!"},
    )

    body = response.json()
    assert "email" not in body
    assert "roles" not in body
    assert "user_id" not in body
    assert "organization_id" not in body
    assert "password_hash" not in body


def test_token_endpoint_returns_generic_401_for_invalid_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(StubLoginService(InvalidLoginCredentialsError()), monkeypatch)

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "ana@empresa.com", "password": "bad"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciales inválidas."}


def test_token_endpoint_disabled_returns_403_without_authenticating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StubLoginService()
    client = build_client(service, monkeypatch, bearer_enabled=False)

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "ana@empresa.com", "password": "PasswordSeguro123!"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Endpoint OAuth2 deshabilitado."}
    assert service.calls == 0


def test_token_endpoint_does_not_require_csrf(monkeypatch: pytest.MonkeyPatch) -> None:
    client = build_client(StubLoginService(), monkeypatch)

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "ana@empresa.com", "password": "PasswordSeguro123!"},
    )

    assert response.status_code == 200


def test_token_endpoint_rejects_json_body_without_authenticating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StubLoginService()
    client = build_client(service, monkeypatch)

    response = client.post(
        "/api/v1/auth/token",
        json={"username": "ana@empresa.com", "password": "PasswordSeguro123!"},
    )

    assert response.status_code == 422
    assert service.calls == 0
    assert service.last_request is None


def test_token_endpoint_ignores_extra_form_fields_for_login_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StubLoginService()
    client = build_client(service, monkeypatch)

    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "  ANA@EMPRESA.COM  ",
            "password": "PasswordSeguro123!",
            "organization_id": "org-forged",
            "tenant": "tenant-forged",
        },
    )

    assert response.status_code == 200
    assert service.calls == 1
    assert service.last_request is not None
    assert service.last_request.email == "ana@empresa.com"
    assert service.last_request.password == "PasswordSeguro123!"  # noqa: S105 - Valor ficticio de test.
    assert not hasattr(service.last_request, "organization_id")
    assert not hasattr(service.last_request, "tenant")
    assert "set-cookie" not in response.headers
