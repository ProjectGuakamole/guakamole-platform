"""Auditoría estructurada para revocación de sesión."""

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from app.shared.audit import StructuredAuditLogger

LOGOUT = "LOGOUT"


@dataclass(frozen=True, slots=True)
class LogoutAuditEvent:
    user_id: str
    organization_id: str
    jti_hash: str


class LogoutAuditPort(Protocol):
    def record_logout(self, event: LogoutAuditEvent) -> None: ...


class NoOpLogoutAuditAdapter:
    def record_logout(self, event: LogoutAuditEvent) -> None:
        _ = event


class StructuredLogoutAuditAdapter:
    def __init__(self, logger: StructuredAuditLogger | None = None) -> None:
        self._logger = logger or StructuredAuditLogger()

    def record_logout(self, event: LogoutAuditEvent) -> None:
        self._logger.emit(
            action=LOGOUT,
            metadata={
                "user_id": event.user_id,
                "organization_id": event.organization_id,
                "jti_hash": event.jti_hash,
            },
        )


def hash_jti(jti: str) -> str:
    """Evita registrar el identificador reutilizable de la sesión."""
    return sha256(jti.encode("utf-8")).hexdigest()
