"""Caso de uso para validar el ciclo de vida de una sesión JWT."""

from jwt import InvalidTokenError

from app.domains.auth.logout.audit import (
    LogoutAuditEvent,
    LogoutAuditPort,
    NoOpLogoutAuditAdapter,
    hash_jti,
)
from app.domains.auth.shared.session_repository import (
    ActiveSessionIdentity,
    SessionStateRepository,
)
from app.domains.auth.shared.tokens import TokenVerifier, VerifiedAccessToken


class InvalidSessionError(Exception):
    """La sesión no puede utilizarse sin revelar su causa concreta."""


class AuthSessionService:
    """Combina criptografía JWT con estado IAM y revocación persistente."""

    def __init__(
        self,
        token_verifier: TokenVerifier,
        repository: SessionStateRepository,
        audit: LogoutAuditPort | None = None,
    ) -> None:
        self._token_verifier = token_verifier
        self._repository = repository
        self._audit = audit or NoOpLogoutAuditAdapter()

    def validate(
        self, raw_token: str
    ) -> tuple[VerifiedAccessToken, ActiveSessionIdentity]:
        try:
            token = self._token_verifier.verify_access_token(raw_token)
        except InvalidTokenError as error:
            raise InvalidSessionError from error
        if token.organization is None or self._repository.is_jti_revoked(token.jti):
            raise InvalidSessionError
        identity = self._repository.find_active_identity(
            token.subject, token.organization
        )
        if identity is None:
            raise InvalidSessionError
        return token, identity

    def revoke(self, token: VerifiedAccessToken) -> None:
        self._repository.revoke(token.jti, token.expires_at)
        if token.organization is not None:
            self._audit.record_logout(
                LogoutAuditEvent(
                    user_id=token.subject,
                    organization_id=token.organization,
                    jti_hash=hash_jti(token.jti),
                )
            )
