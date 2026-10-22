"""Contrato de seguridad de la configuración central."""

import pytest
from pydantic import ValidationError

from app.core.config import get_settings, reset_settings_cache, settings_from_mapping
from app.core.test_database import get_test_database_url

pytestmark = pytest.mark.test_unit


def valid_mapping(**overrides: str) -> dict[str, str]:
    values = {
        "APP_ENV": "test",
        "DATABASE_URL": "postgresql+psycopg://test:test@localhost/guakamole_test",
        "JWT_SECRET_KEY": "test-secret-not-for-production-with-safe-length",
        "CORS_ALLOWED_ORIGINS": "http://localhost:5173",
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize("app_env", ["", "invalid"])
def test_rejects_missing_blank_or_invalid_app_env(app_env: str) -> None:
    values = valid_mapping(APP_ENV=app_env)

    with pytest.raises((ValueError, ValidationError)):
        settings_from_mapping(values)


def test_requires_app_env() -> None:
    values = valid_mapping()
    del values["APP_ENV"]

    with pytest.raises(ValueError, match="obligatorias"):
        settings_from_mapping(values)


def test_process_mapping_is_the_only_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://test:test@localhost/guakamole_test"
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY", "test-secret-not-for-production-with-safe-length"
    )
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
    reset_settings_cache()

    assert get_settings().app_env == "test"


@pytest.mark.parametrize("app_env", ["development", "test"])
def test_development_and_test_allow_explicit_local_transport(app_env: str) -> None:
    assert settings_from_mapping(valid_mapping(APP_ENV=app_env)).app_env == app_env


@pytest.mark.parametrize("app_env", ["staging", "production"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"AUTH_COOKIE_SECURE": "false"},
        {"AUTH_COOKIE_HTTPONLY": "false"},
        {"AUTH_ENABLE_PASSWORD_BEARER_TOKEN": "true"},
        {"RATE_LIMIT_ENABLED": "false"},
        {"CORS_ALLOWED_ORIGINS": ""},
        {"CORS_ALLOWED_ORIGINS": "*"},
        {"CORS_ALLOWED_ORIGINS": "http://localhost:5173"},
        {"CORS_ALLOWED_ORIGINS": "https://127.0.0.1"},
    ],
)
def test_protected_environments_reject_insecure_settings(
    app_env: str, overrides: dict[str, str]
) -> None:
    with pytest.raises(ValidationError):
        settings_from_mapping(valid_mapping(APP_ENV=app_env, **overrides))


@pytest.mark.parametrize(
    "secret", ["<jwt-secret>", "change-me-secret-value-that-is-long-enough"]
)
def test_rejects_placeholder_secrets(secret: str) -> None:
    with pytest.raises(ValidationError):
        settings_from_mapping(valid_mapping(JWT_SECRET_KEY=secret))


def test_rejects_legacy_jwt_secret() -> None:
    with pytest.raises(ValueError, match="legacy"):
        settings_from_mapping(valid_mapping(JWT_SECRET="legacy-" + "not-permitted"))


def test_does_not_read_environment_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    reset_settings_cache()

    with pytest.raises(ValueError, match="obligatorias"):
        get_settings()


@pytest.mark.parametrize(
    "environment",
    [
        {},
        {"DATABASE_URL": "postgresql+psycopg://test:test@localhost/application"},
        {"TEST_DATABASE_URL": "sqlite:///guakamole_test"},
        {"TEST_DATABASE_URL": "postgresql+psycopg://test:test@localhost/application"},
        {"TEST_DATABASE_URL": "postgresql+psycopg://test:test@remote/guakamole_test"},
    ],
)
def test_test_database_selector_rejects_fallbacks_and_unsafe_urls(
    environment: dict[str, str],
) -> None:
    with pytest.raises(RuntimeError):
        get_test_database_url(environment)


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+psycopg://test:test@localhost/guakamole_test",
        "postgresql+psycopg://test:test@127.0.0.1/guakamole_test",
        "postgresql+psycopg://test:test@[::1]/guakamole_test",
        "postgresql+psycopg:///guakamole_test?host=/var/run/postgresql",
    ],
)
def test_test_database_selector_accepts_only_dedicated_local_postgresql_database(
    database_url: str,
) -> None:
    environment = {"TEST_DATABASE_URL": database_url}

    assert get_test_database_url(environment) == environment["TEST_DATABASE_URL"]
