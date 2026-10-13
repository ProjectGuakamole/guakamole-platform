"""Adaptador de auditoría estructurada no persistente."""

import logging
import re
from collections.abc import Mapping
from math import isfinite

REDACTED_VALUE = "[REDACTED]"
TRUNCATED_VALUE = "[TRUNCATED]"
MAX_METADATA_DEPTH = 5
MAX_METADATA_ITEMS = 50
MAX_METADATA_STRING_LENGTH = 1_024
MAX_METADATA_KEY_LENGTH = 128

_SENSITIVE_KEY_PARTS = frozenset(
    {
        "apikey",
        "authorization",
        "credential",
        "csrf",
        "jwt",
        "password",
        "passwd",
        "passphrase",
        "privatekey",
        "pwd",
        "secret",
        "token",
    }
)
_BEARER_VALUE_PATTERN = re.compile(r"^bearer\s+\S+", re.IGNORECASE)
_JWT_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")


def sanitize_audit_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    """Devuelve metadata apta para logs sin secretos ni valores no seguros."""

    sanitized = _sanitize_mapping(metadata, depth=0)
    return sanitized if sanitized is not None else {}


def _sanitize_mapping(
    value: Mapping[str, object], *, depth: int
) -> dict[str, object] | None:
    if depth >= MAX_METADATA_DEPTH:
        return None

    sanitized: dict[str, object] = {}
    for index, (key, nested_value) in enumerate(value.items()):
        if index >= MAX_METADATA_ITEMS:
            sanitized[TRUNCATED_VALUE] = TRUNCATED_VALUE
            break
        if not isinstance(key, str) or len(key) > MAX_METADATA_KEY_LENGTH:
            continue
        if _is_sensitive_key(key):
            continue
        safe_value = _sanitize_value(nested_value, depth=depth + 1)
        if safe_value is not None:
            sanitized[key] = safe_value
    return sanitized


def _sanitize_sequence(
    value: list[object] | tuple[object, ...], *, depth: int
) -> list[object]:
    sanitized: list[object] = []
    for index, nested_value in enumerate(value):
        if index >= MAX_METADATA_ITEMS:
            sanitized.append(TRUNCATED_VALUE)
            break
        safe_value = _sanitize_value(nested_value, depth=depth + 1)
        if safe_value is not None:
            sanitized.append(safe_value)
    return sanitized


def _sanitize_value(value: object, *, depth: int) -> object | None:
    if isinstance(value, str):
        if _is_sensitive_value(value):
            return REDACTED_VALUE
        if len(value) > MAX_METADATA_STRING_LENGTH:
            return TRUNCATED_VALUE
        return value
    if value is None or isinstance(value, bool | int):
        return value
    if isinstance(value, float):
        return value if isfinite(value) else None
    if isinstance(value, Mapping):
        return _sanitize_mapping(value, depth=depth)
    if isinstance(value, list | tuple):
        return _sanitize_sequence(value, depth=depth)
    return None


def _is_sensitive_key(key: str) -> bool:
    normalized_key = "".join(
        character for character in key.lower() if character.isalnum()
    )
    return any(part in normalized_key for part in _SENSITIVE_KEY_PARTS)


def _is_sensitive_value(value: str) -> bool:
    return bool(
        _BEARER_VALUE_PATTERN.match(value) or _JWT_VALUE_PATTERN.fullmatch(value)
    )


class StructuredAuditLogger:
    """Emite auditoría mínima y nunca afecta al flujo de negocio."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("guakamole.audit")

    def emit(self, *, action: str, metadata: Mapping[str, object]) -> None:
        try:
            self._logger.info(
                "audit_event",
                extra={
                    "audit_action": action,
                    "audit_metadata": sanitize_audit_metadata(metadata),
                },
            )
        except Exception:
            # La auditoría de runtime no es persistente aún y no debe bloquear la API.
            return
