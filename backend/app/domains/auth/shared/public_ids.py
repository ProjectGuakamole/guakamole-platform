"""Generación de identificadores públicos sin dependencia de persistencia."""

import re
from base64 import urlsafe_b64decode, urlsafe_b64encode
from enum import StrEnum
from uuid import UUID, uuid4


class PublicIdPrefix(StrEnum):
    """Prefijos públicos soportados por el core de auth."""

    USER = "usr"
    ORGANIZATION = "org"


ENCODED_UUID_PATTERN = re.compile(r"[A-Za-z0-9_-]{22}")


def generate_public_id(prefix: PublicIdPrefix) -> str:
    """Genera un ID público con prefijo y UUID v4."""
    return f"{prefix.value}_{_encode_uuid(uuid4())}"


def parse_public_uuid(public_id: str, prefix: PublicIdPrefix) -> UUID:
    """Extrae y valida el UUID de un ID público con el prefijo esperado."""
    expected_prefix = f"{prefix.value}_"
    if not public_id.startswith(expected_prefix):
        raise ValueError("El identificador público no usa el prefijo esperado.")
    encoded_uuid = public_id.removeprefix(expected_prefix)
    if ENCODED_UUID_PATTERN.fullmatch(encoded_uuid) is None:
        raise ValueError("El identificador público contiene un UUID inválido.")
    try:
        value = UUID(bytes=urlsafe_b64decode(f"{encoded_uuid}=="))
    except (ValueError, UnicodeEncodeError) as error:
        raise ValueError(
            "El identificador público contiene un UUID inválido."
        ) from error
    if _encode_uuid(value) != encoded_uuid:
        raise ValueError("El identificador público contiene un UUID inválido.")
    return value


def _encode_uuid(value: UUID) -> str:
    return urlsafe_b64encode(value.bytes).decode("ascii").rstrip("=")
