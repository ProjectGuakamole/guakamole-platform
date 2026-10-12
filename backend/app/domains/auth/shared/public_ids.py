"""Generación de identificadores públicos sin dependencia de persistencia."""

from enum import StrEnum
from uuid import UUID, uuid4


class PublicIdPrefix(StrEnum):
    """Prefijos públicos soportados por el core de auth."""

    USER = "usr"
    ORGANIZATION = "org"


def generate_public_id(prefix: PublicIdPrefix) -> str:
    """Genera un ID público con prefijo y UUID v4."""
    return f"{prefix.value}_{uuid4()}"


def parse_public_uuid(public_id: str, prefix: PublicIdPrefix) -> UUID:
    """Extrae y valida el UUID de un ID público con el prefijo esperado."""
    expected_prefix = f"{prefix.value}_"
    if not public_id.startswith(expected_prefix):
        raise ValueError("El identificador público no usa el prefijo esperado.")
    return UUID(public_id.removeprefix(expected_prefix))
