"""Caso de uso de login seguro."""

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from app.domains.auth.login.exceptions import InvalidLoginCredentialsError
from app.domains.auth.login.repository import LoginUserRecord, LoginUserRepository
from app.domains.auth.login.schemas import LoginRequest, LoginTokenData
from app.domains.auth.shared.password_hasher import PasswordHasher
from app.domains.auth.shared.tokens import TokenIssuer

ACTIVE_STATUS = "ACTIVE"
LOGIN_SUCCESS = "LOGIN_SUCCESS"
LOGIN_FAILED = "LOGIN_FAILED"


class LoginAuditPort(Protocol):
    """Puerto conceptual para auditoría de login."""

    def record_login_success(self, event: "LoginSuccessAuditEvent") -> None: ...
    def record_login_failed(self, event: "LoginFailedAuditEvent") -> None: ...


@dataclass(frozen=True, slots=True)
class LoginSuccessAuditEvent:
    action: str
    email_hash: str
    user_public_id: str


@dataclass(frozen=True, slots=True)
class LoginFailedAuditEvent:
    action: str
    email_hash: str


class NoOpLoginAuditAdapter:
    """Adaptador no-op hasta disponer de auditoría persistente."""

    def record_login_success(self, event: LoginSuccessAuditEvent) -> None:
        _ = event

    def record_login_failed(self, event: LoginFailedAuditEvent) -> None:
        _ = event


class LoginService:
    """Autentica credenciales y emite access token sin acoplarse a FastAPI."""

    def __init__(
        self,
        *,
        repository: LoginUserRepository,
        password_hasher: PasswordHasher,
        token_issuer: TokenIssuer,
        audit: LoginAuditPort,
    ) -> None:
        self._repository = repository
        self._password_hasher = password_hasher
        self._token_issuer = token_issuer
        self._audit = audit

    def login(self, request: LoginRequest) -> LoginTokenData:
        email_hash = self._hash_email(request.email)
        user = self._repository.find_by_normalized_email(request.email)
        if user is None:
            self._record_failed_login(email_hash)
            raise InvalidLoginCredentialsError

        if not self._is_active_with_valid_password(user, request.password):
            self._record_failed_login(email_hash)
            raise InvalidLoginCredentialsError

        token = self._token_issuer.issue_access_token(
            subject=user.user_public_id,
            organization=user.organization_public_id,
        )
        self._audit.record_login_success(
            LoginSuccessAuditEvent(
                action=LOGIN_SUCCESS,
                email_hash=email_hash,
                user_public_id=user.user_public_id,
            ),
        )
        return LoginTokenData(
            access_token=token,
            user_public_id=user.user_public_id,
            organization_public_id=user.organization_public_id,
        )

    def _record_failed_login(self, email_hash: str) -> None:
        self._audit.record_login_failed(
            LoginFailedAuditEvent(action=LOGIN_FAILED, email_hash=email_hash),
        )

    def _is_active_with_valid_password(
        self, user: LoginUserRecord, plain_password: str
    ) -> bool:
        return (
            user.status == ACTIVE_STATUS
            and user.organization_status == ACTIVE_STATUS
            and self._password_hasher.verify(
                plain_password,
                user.password_hash,
            )
        )

    @staticmethod
    def _hash_email(email: str) -> str:
        return sha256(email.encode("utf-8")).hexdigest()
