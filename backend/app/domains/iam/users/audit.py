"""Adaptador de auditoría estructurada del piloto IAM/users."""

from app.domains.iam.users.services import AuditEvent
from app.shared.audit import StructuredAuditLogger


class StructuredUsersAuditLogger:
    def __init__(self, logger: StructuredAuditLogger | None = None) -> None:
        self._logger = logger or StructuredAuditLogger()

    def emit(self, event: AuditEvent) -> None:
        self._logger.emit(action=event.action, metadata=event.metadata)
