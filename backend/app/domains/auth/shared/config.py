"""Configuración tipada de autenticación y seguridad."""

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_AUTH_COOKIE_SAMESITE_VALUES = frozenset({"lax", "strict", "none"})
ALLOWED_JWT_ALGORITHMS = frozenset({"HS256"})
DEFAULT_CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


class CorsSettings(BaseSettings):
    """Settings CORS cargables sin depender de secretos de autenticación."""

    cors_allow_credentials: bool = True
    cors_allow_authorization_header: bool = True
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: DEFAULT_CORS_ALLOWED_ORIGINS.copy(),
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: object) -> object:
        """Permite configurar origins CORS como lista o cadena separada por comas."""

        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_allowed_origins(cls, value: list[str]) -> list[str]:
        """Rechaza wildcards para evitar CORS permisivo con credenciales."""

        if "*" in value:
            msg = "cors_allowed_origins no puede contener '*'"
            raise ValueError(msg)
        return value


class AuthSettings(CorsSettings):
    """Settings de auth cargables desde variables de entorno."""

    access_token_expire_minutes: int = Field(default=15, ge=1)
    jwt_secret_key: str = Field(
        min_length=32,
        validation_alias=AliasChoices("jwt_secret_key", "JWT_SECRET_KEY", "JWT_SECRET"),
    )
    jwt_algorithm: str = "HS256"
    auth_cookie_name: str = "guak_access_token"
    auth_cookie_path: str = "/api"
    auth_cookie_domain: str | None = None
    auth_cookie_httponly: bool = True
    auth_cookie_secure: bool = True
    auth_cookie_samesite: str = "lax"
    auth_enable_password_bearer_token: bool = False
    default_registered_organization_status: str = "ACTIVE"
    default_registered_user_status: str = "ACTIVE"
    default_platform_role: str = "USER"
    default_organization_role: str = "COMPANY_ADMIN"

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

    @model_validator(mode="after")
    def validate_cookie_transport_security(self) -> "AuthSettings":
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            msg = "SameSite=None requiere auth_cookie_secure=True"
            raise ValueError(msg)
        return self
