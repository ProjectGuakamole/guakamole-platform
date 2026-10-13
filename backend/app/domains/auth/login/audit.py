"""Adaptador de auditoría del caso de uso de login."""

from app.domains.auth.login.service import LoginFailedAuditEvent, LoginSuccessAuditEvent
from app.shared.audit import StructuredAuditLogger


class StructuredLoginAuditAdapter:
    def __init__(self, logger: StructuredAuditLogger | None = None) -> None:
        self._logger = logger or StructuredAuditLogger()

    def record_login_success(self, event: LoginSuccessAuditEvent) -> None:
        self._logger.emit(
            action=event.action,
            metadata={"email_hash": event.email_hash, "user_id": event.user_public_id},
        )

    def record_login_failed(self, event: LoginFailedAuditEvent) -> None:
        self._logger.emit(
            action=event.action, metadata={"email_hash": event.email_hash}
        )
