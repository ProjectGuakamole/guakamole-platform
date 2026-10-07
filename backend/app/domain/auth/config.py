"""Configuración tipada de autenticación y seguridad."""

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_AUTH_COOKIE_SAMESITE_VALUES = frozenset({"lax", "strict", "none"})
ALLOWED_JWT_ALGORITHMS = frozenset({"HS256"})


class AuthSettings(BaseSettings):
    """Settings de auth cargables desde variables de entorno."""

    access_token_expire_minutes: int = Field(default=15, ge=1)
    jwt_secret_key: str = Field(
        min_length=1,
        validation_alias=AliasChoices("jwt_secret_key", "JWT_SECRET_KEY", "JWT_SECRET"),
    )
    jwt_algorithm: str = "HS256"
    auth_cookie_name: str = "guak_access_token"
    auth_cookie_path: str = "/api"
    auth_cookie_domain: str | None = None
    auth_cookie_httponly: bool = True
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    cors_allow_credentials: bool = True
    cors_allow_authorization_header: bool = True
    auth_enable_password_bearer_token: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("auth_cookie_samesite")
    @classmethod
    def validate_auth_cookie_samesite(cls, value: str) -> str:
        """Normaliza y restringe SameSite a valores soportados por cookies HTTP."""

        normalized_value = value.lower()
        if normalized_value not in ALLOWED_AUTH_COOKIE_SAMESITE_VALUES:
            allowed_values = ", ".join(sorted(ALLOWED_AUTH_COOKIE_SAMESITE_VALUES))
            msg = f"auth_cookie_samesite debe ser uno de: {allowed_values}"
            raise ValueError(msg)
        return normalized_value

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        """Restringe el algoritmo JWT al permitido para el MVP."""

        if value not in ALLOWED_JWT_ALGORITHMS:
            allowed_values = ", ".join(sorted(ALLOWED_JWT_ALGORITHMS))
            msg = f"jwt_algorithm debe ser uno de: {allowed_values}"
            raise ValueError(msg)
        return value
