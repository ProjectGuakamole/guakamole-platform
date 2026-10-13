"""Tests de configuración CORS controlada para OAuth2 browser flows."""

from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from pydantic import ValidationError

from app.core.cors import configure_cors
from app.domains.auth.shared.config import AuthSettings, CorsSettings
from app.main import create_app

pytestmark = pytest.mark.test_unit

ALLOWED_ORIGIN = "http://localhost:5173"
DISALLOWED_ORIGIN = "https://frontend.example.invalid"
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


def build_settings(
    *,
    cors_allow_authorization_header: bool = True,
    cors_allowed_origins: list[str] | None = None,
) -> AuthSettings:
    return AuthSettings.model_validate(
        {
            "jwt_secret_key": "test-secret-not-for-production-with-safe-length",
            "cors_allow_authorization_header": cors_allow_authorization_header,
            "cors_allowed_origins": cors_allowed_origins or [ALLOWED_ORIGIN],
        },
    )


def build_cors_client(settings: AuthSettings) -> TestClient:
    app = FastAPI()
    configure_cors(app, settings)
    return TestClient(app)


def preflight(
    client: TestClient,
    *,
    origin: str = ALLOWED_ORIGIN,
    request_headers: str = "X-CSRF-Token, Content-Type",
) -> Response:
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": request_headers,
        },
    )
    return cast(Response, response)


def test_preflight_from_allowed_origin_returns_expected_cors_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "JWT_SECRET_KEY", "test-secret-not-for-production-with-safe-length"
    )
    client = TestClient(create_app())

    response = preflight(client)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "*" not in response.headers["access-control-allow-origin"]
    assert "X-CSRF-Token" in response.headers["access-control-allow-headers"]


def test_preflight_from_disallowed_origin_does_not_return_permissive_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "JWT_SECRET_KEY", "test-secret-not-for-production-with-safe-length"
    )
    client = TestClient(create_app())

    response = preflight(client, origin=DISALLOWED_ORIGIN)

    assert response.headers.get("access-control-allow-origin") is None


def test_create_app_does_not_require_jwt_secret_for_cors_only_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)

    client = TestClient(create_app())
    response = preflight(client)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


@pytest.mark.parametrize("origin", DEFAULT_ALLOWED_ORIGINS)
def test_default_cors_origins_are_allowed_without_wildcard(
    origin: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    client = TestClient(create_app())

    response = preflight(client, origin=origin)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-origin"] != "*"


def test_cors_allowed_origins_can_be_configured_from_comma_separated_string() -> None:
    settings = CorsSettings.model_validate(
        {"cors_allowed_origins": "https://one.example, https://two.example"},
    )

    assert settings.cors_allowed_origins == [
        "https://one.example",
        "https://two.example",
    ]


def test_authorization_header_is_allowed_when_enabled() -> None:
    client = build_cors_client(build_settings(cors_allow_authorization_header=True))

    response = preflight(client, request_headers="Authorization, X-CSRF-Token")

    assert response.status_code == 200
    assert "Authorization" in response.headers["access-control-allow-headers"]


def test_authorization_header_is_rejected_when_disabled() -> None:
    client = build_cors_client(build_settings(cors_allow_authorization_header=False))

    response = preflight(client, request_headers="Authorization, X-CSRF-Token")

    assert response.status_code == 400
    assert "Authorization" not in response.headers["access-control-allow-headers"]


def test_wildcard_origin_is_rejected_by_settings() -> None:
    with pytest.raises(ValidationError, match="cors_allowed_origins"):
        build_settings(cors_allowed_origins=["*"])


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/v1/auth/login"),
        ("GET", "/api/v1/auth/csrf"),
        ("POST", "/api/v1/auth/logout"),
        ("GET", "/api/v1/auth/me"),
    ],
)
def test_auth_endpoints_preflight_is_not_broken_by_cors(
    method: str,
    path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "JWT_SECRET_KEY", "test-secret-not-for-production-with-safe-length"
    )
    client = TestClient(create_app())

    response = client.options(
        path,
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "X-CSRF-Token, Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
