"""Value objects para cookies de autenticación."""

from dataclasses import dataclass

from app.domain.auth.config import AuthSettings


@dataclass(frozen=True, slots=True)
class AuthCookieSettings:
    """Configuración de cookie derivada de auth settings."""

    name: str
    path: str
    domain: str | None
    httponly: bool
    secure: bool
    samesite: str
    max_age: int


def build_auth_cookie_settings(settings: AuthSettings) -> AuthCookieSettings:
    """Construye la configuración de cookie sin acoplarse a FastAPI Response."""
    return AuthCookieSettings(
        name=settings.auth_cookie_name,
        path=settings.auth_cookie_path,
        domain=settings.auth_cookie_domain,
        httponly=settings.auth_cookie_httponly,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
    )
