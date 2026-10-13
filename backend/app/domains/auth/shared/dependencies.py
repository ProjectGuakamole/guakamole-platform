"""Dependencias compartidas del dominio de autenticación."""

from app.core.config import get_settings
from app.domains.auth.shared.config import AuthSettings


def build_auth_settings() -> AuthSettings:
    """Obtiene los settings centrales sin cargar ficheros implícitos."""

    return get_settings()
