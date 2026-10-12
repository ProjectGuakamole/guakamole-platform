"""Tests HTTP ligeros para rate limiting explícito en auth/registro."""

import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import reset_rate_limiter_state
from app.domains.auth.login.router import get_login_service
from app.domains.auth.login.schemas import LoginRequest, LoginTokenData
from app.domains.auth.me.router import get_auth_me_service
from app.domains.iam.registration.router import get_registration_service
from app.domains.iam.registration.schemas import (
    RegistrationRequest,
    RegistrationResponse,
)
from app.main import create_app

pytestmark = pytest.mark.test_unit

ACCESS_TOKEN = "jwt-test-value"  # noqa: S105 - Token opaco ficticio para tests.


class CountingLoginService:
    def __init__(self) -> None:
        self.calls = 0

    def login(self, request: LoginRequest) -> LoginTokenData:
        _ = request
        self.calls += 1
        return LoginTokenData(
            access_token=ACCESS_TOKEN,
            user_public_id="usr_public",
            organization_public_id="org_public",
        )


class CountingRegistrationService:
    def __init__(self) -> None:
        self.calls = 0

    def register(self, request: RegistrationRequest) -> RegistrationResponse:
        _ = request
        self.calls += 1
        return RegistrationResponse(
            organization_id="org_public",
            user_id="usr_public",
            organization_status="PENDING_ACTIVATION",
            user_status="ACTIVE",
        )


@pytest.fixture(autouse=True)
def isolate_rate_limiter() -> None:
    reset_rate_limiter_state()


def build_registration_payload() -> dict[str, object]:
    return {
        "organization": {
            "name": "Mi Empresa",
            "slug": "mi-empresa",
            "legal_name": "Mi Empresa S.L.",
            "tax_id": "B12345678",
            "country": "España",
            "state": "Catalunya",
            "city": "Barcelona",
            "address": "Calle Mayor 10",
            "postal_code": "08001",
        },
        "user": {
            "first_name": "Ana",
            "last_name": "García",
            "email": "ana@empresa.com",
            "birth_date": "1990-01-01",
            "password": "PasswordSeguro123!",
            "password_confirm": "PasswordSeguro123!",
            "country": "España",
            "state": "Catalunya",
            "city": "Barcelona",
            "address": "Calle Mayor 10",
            "postal_code": "08001",
        },
    }


def build_client(
    monkeypatch: pytest.MonkeyPatch,
    login_service: CountingLoginService,
    registration_service: CountingRegistrationService,
    *,
    enabled: bool = True,
) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-production")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true" if enabled else "false")
    monkeypatch.setenv("AUTH_LOGIN_RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("AUTH_TOKEN_RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("AUTH_TOKEN_RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("REGISTRATION_RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("REGISTRATION_RATE_LIMIT_WINDOW_SECONDS", "300")
    app = create_app()
    app.dependency_overrides[get_login_service] = lambda: login_service
    app.dependency_overrides[get_registration_service] = lambda: registration_service
    app.dependency_overrides[get_auth_me_service] = lambda: object()
    return TestClient(app)


def assert_generic_429(response_text: str) -> None:
    assert "Demasiadas solicitudes. Inténtalo más tarde." in response_text
    assert "ana@empresa.com" not in response_text
    assert "PasswordSeguro123!" not in response_text
    assert "org_public" not in response_text
    assert "jwt-test-value" not in response_text


def test_login_rate_limit_returns_429_and_does_not_call_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CountingLoginService()
    client = build_client(monkeypatch, service, CountingRegistrationService())

    payload = {"email": "ana@empresa.com", "password": "PasswordSeguro123!"}
    assert client.post("/api/v1/auth/login", json=payload).status_code == 200
    response = client.post("/api/v1/auth/login", json=payload)

    assert response.status_code == 429
    assert int(response.headers["retry-after"]) in {59, 60}
    assert service.calls == 1
    assert_generic_429(response.text)


def test_login_rate_limit_does_not_trust_x_forwarded_for(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CountingLoginService()
    client = build_client(monkeypatch, service, CountingRegistrationService())
    payload = {"email": "ana@empresa.com", "password": "PasswordSeguro123!"}

    first_response = client.post(
        "/api/v1/auth/login",
        headers={"X-Forwarded-For": "1.1.1.1"},
        json=payload,
    )
    second_response = client.post(
        "/api/v1/auth/login",
        headers={"X-Forwarded-For": "2.2.2.2"},
        json=payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert service.calls == 1


def test_token_rate_limit_returns_429_and_does_not_call_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CountingLoginService()
    client = build_client(monkeypatch, service, CountingRegistrationService())

    form = {"username": "ana@empresa.com", "password": "PasswordSeguro123!"}
    assert client.post("/api/v1/auth/token", data=form).status_code == 200
    response = client.post("/api/v1/auth/token", data=form)

    assert response.status_code == 429
    assert service.calls == 1
    assert_generic_429(response.text)


def test_registration_rate_limit_returns_429_and_does_not_call_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CountingRegistrationService()
    client = build_client(monkeypatch, CountingLoginService(), service)

    payload = build_registration_payload()
    success_response = client.post("/api/v1/organizations/register", json=payload)
    assert success_response.status_code == 201
    response = client.post("/api/v1/organizations/register", json=payload)

    assert response.status_code == 429
    assert service.calls == 1
    assert_generic_429(response.text)


def test_disabled_rate_limit_does_not_block(monkeypatch: pytest.MonkeyPatch) -> None:
    service = CountingLoginService()
    client = build_client(
        monkeypatch,
        service,
        CountingRegistrationService(),
        enabled=False,
    )

    payload = {"email": "ana@empresa.com", "password": "PasswordSeguro123!"}
    assert client.post("/api/v1/auth/login", json=payload).status_code == 200
    assert client.post("/api/v1/auth/login", json=payload).status_code == 200
    assert service.calls == 2


def test_other_auth_endpoints_are_not_blocked_by_this_limiter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = build_client(
        monkeypatch,
        CountingLoginService(),
        CountingRegistrationService(),
    )

    for _ in range(2):
        assert client.get("/api/v1/auth/me").status_code == 401
        assert client.get("/api/v1/auth/csrf").status_code == 401
        assert client.post("/api/v1/auth/logout").status_code == 401
