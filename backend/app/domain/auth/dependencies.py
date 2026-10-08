"""Dependencias compartidas del dominio de autenticación."""

from app.domain.auth.config import AuthSettings


def build_auth_settings() -> AuthSettings:
    """Carga settings de auth mediante Pydantic Settings sin fallback inseguro."""

    # Pydantic Settings resuelve el secreto obligatorio desde las fuentes configuradas.
    return AuthSettings()  # type: ignore[call-arg]
