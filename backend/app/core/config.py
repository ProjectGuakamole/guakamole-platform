"""Configuración centralizada, sin carga implícita de ficheros .env."""

from __future__ import annotations

import os
from collections.abc import Mapping
from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

AppEnvironment = Literal["development", "test", "staging", "production"]
_PLACEHOLDER_MARKERS = ("change-me", "placeholder", "example", "replace-me")


class Settings(BaseModel):
    """Configuración efectiva creada exclusivamente desde un mapping explícito."""

    app_env: AppEnvironment
    database_url: str = Field(min_length=1)
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1)
    auth_cookie_name: str = "guak_access_token"
    auth_cookie_path: str = "/api"
    auth_cookie_domain: str | None = None
    auth_cookie_httponly: bool = True
    auth_cookie_secure: bool = True
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    auth_enable_password_bearer_token: bool = False
    cors_allow_credentials: bool = True
    cors_allow_authorization_header: bool = True
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )
    rate_limit_enabled: bool = True
    auth_login_rate_limit_requests: int = Field(default=5, ge=1)
    auth_login_rate_limit_window_seconds: int = Field(default=60, ge=1)
    auth_token_rate_limit_requests: int = Field(default=5, ge=1)
    auth_token_rate_limit_window_seconds: int = Field(default=60, ge=1)
    registration_rate_limit_requests: int = Field(default=3, ge=1)
    registration_rate_limit_window_seconds: int = Field(default=300, ge=1)
    default_registered_organization_status: str = "ACTIVE"
    default_registered_user_status: str = "ACTIVE"
    default_platform_role: str = "USER"
    default_organization_role: str = "COMPANY_ADMIN"

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("auth_cookie_samesite", mode="before")
    @classmethod
    def normalize_samesite(cls, value: object) -> object:
        return value.lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_security(self) -> Settings:
        protected = self.app_env in {"staging", "production"}
        is_placeholder = any(
            marker in self.jwt_secret_key.lower() for marker in _PLACEHOLDER_MARKERS
        ) or ("<" in self.jwt_secret_key and ">" in self.jwt_secret_key)
        if is_placeholder:
            raise ValueError("La clave JWT no puede ser un valor de plantilla.")
        if "*" in self.cors_allowed_origins:
            raise ValueError("cors_allowed_origins no puede contener '*'.")
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("SameSite=None requiere una cookie segura.")
        if not protected:
            return self
        if not self.auth_cookie_secure or not self.auth_cookie_httponly:
            raise ValueError("Staging y producción requieren cookies seguras HttpOnly.")
        if self.auth_enable_password_bearer_token or not self.rate_limit_enabled:
            raise ValueError(
                "Staging y producción requieren controles de acceso activos."
            )
        if not self.cors_allowed_origins:
            raise ValueError("Staging y producción requieren orígenes CORS explícitos.")
        for origin in self.cors_allowed_origins:
            parsed = urlparse(origin)
            is_local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
            if parsed.scheme != "https" or is_local:
                raise ValueError(
                    "Los orígenes CORS protegidos deben usar HTTPS público."
                )
        return self


def settings_from_mapping(environment: Mapping[str, str]) -> Settings:
    """Construye settings usando sólo el entorno recibido, sin valores ocultos."""

    if "JWT_SECRET" in environment:
        raise ValueError("JWT_SECRET es legacy y está prohibida; usa JWT_SECRET_KEY.")
    required = ("APP_ENV", "DATABASE_URL", "JWT_SECRET_KEY")
    missing = [name for name in required if not environment.get(name)]
    if missing:
        raise ValueError("Faltan variables obligatorias de configuración.")
    values = {
        name: environment[name.upper()]
        for name in Settings.model_fields
        if name.upper() in environment
    }
    return Settings.model_validate(values)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Obtiene settings del proceso, que tiene prioridad sobre cualquier fichero."""

    return settings_from_mapping(os.environ)


def reset_settings_cache() -> None:
    """Restablece la caché para tests aislados."""

    get_settings.cache_clear()
