"""Tests unitarios del login seguro."""

from dataclasses import asdict, dataclass

import jwt
import pytest
from pydantic import ValidationError

from app.domain.auth.config import AuthSettings
from app.domain.auth.login_exceptions import InvalidLoginCredentialsError
from app.domain.auth.login_repositories import LoginUserRecord
from app.domain.auth.login_schemas import LoginRequest, LoginResponse
from app.domain.auth.login_services import (
    LOGIN_FAILED,
    LOGIN_SUCCESS,
    LoginFailedAuditEvent,
    LoginService,
    LoginSuccessAuditEvent,
)
from app.domain.auth.password_hasher import PwdlibPasswordHasher
from app.domain.auth.tokens import JwtAccessTokenService

pytestmark = pytest.mark.test_unit

VALID_CREDENTIAL = "PasswordSeguro123!"
INVALID_CREDENTIAL = "PasswordIncorrecto123!"


@dataclass(slots=True)
class StubLoginRepository:
    user: LoginUserRecord | None
    requested_email: str | None = None

    def find_by_normalized_email(self, email: str) -> LoginUserRecord | None:
        self.requested_email = email
        return self.user


class SpyAuditAdapter:
    def __init__(self) -> None:
        self.success_events: list[LoginSuccessAuditEvent] = []
        self.failed_events: list[LoginFailedAuditEvent] = []

    def record_login_success(self, event: LoginSuccessAuditEvent) -> None:
        self.success_events.append(event)

    def record_login_failed(self, event: LoginFailedAuditEvent) -> None:
        self.failed_events.append(event)


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings.model_validate(
        {"jwt_secret_key": "test-secret-not-for-production-with-safe-length"},
    )


def build_service(
    user: LoginUserRecord | None,
    auth_settings: AuthSettings,
    audit: SpyAuditAdapter,
) -> tuple[LoginService, StubLoginRepository]:
    repository = StubLoginRepository(user=user)
    service = LoginService(
        repository=repository,
        password_hasher=PwdlibPasswordHasher(),
        token_issuer=JwtAccessTokenService(auth_settings),
        audit=audit,
    )
    return service, repository


def test_login_schema_normalizes_email_and_rejects_extra_fields() -> None:
    request = LoginRequest.model_validate(
        {"email": "  Ana@Empresa.COM ", "password": "PasswordSeguro123!"},
    )

    assert request.email == "ana@empresa.com"
    with pytest.raises(ValidationError):
        LoginRequest.model_validate(
            {
                "email": "ana@empresa.com",
                "password": "PasswordSeguro123!",
                "organization_id": 1,
            },
        )


def test_login_ok_returns_token_data_and_public_response_has_no_token(
    auth_settings: AuthSettings,
) -> None:
    hasher = PwdlibPasswordHasher()
    user = LoginUserRecord(
        user_public_id="usr_public",
        organization_public_id="org_public",
        password_hash=hasher.hash(VALID_CREDENTIAL),
        status="ACTIVE",
    )
    audit = SpyAuditAdapter()
    service, repository = build_service(user, auth_settings, audit)

    token_data = service.login(
        LoginRequest(email="ANA@EMPRESA.COM", password=VALID_CREDENTIAL),
    )
    response = LoginResponse().model_dump()

    assert repository.requested_email == "ana@empresa.com"
    assert token_data.access_token
    assert token_data.user_public_id == "usr_public"
    assert response == {"status": "authenticated"}
    assert "access_token" not in response
    assert "token" not in response


@pytest.mark.parametrize(
    ("user", "password"),
    [
        (None, VALID_CREDENTIAL),
        (
            LoginUserRecord(
                user_public_id="usr_public",
                organization_public_id="org_public",
                password_hash=PwdlibPasswordHasher().hash(VALID_CREDENTIAL),
                status="ACTIVE",
            ),
            INVALID_CREDENTIAL,
        ),
        (
            LoginUserRecord(
                user_public_id="usr_public",
                organization_public_id="org_public",
                password_hash=PwdlibPasswordHasher().hash(VALID_CREDENTIAL),
                status="DISABLED",
            ),
            VALID_CREDENTIAL,
        ),
    ],
)
def test_login_failures_raise_generic_error(
    user: LoginUserRecord | None,
    password: str,
    auth_settings: AuthSettings,
) -> None:
    audit = SpyAuditAdapter()
    service, _ = build_service(user, auth_settings, audit)

    with pytest.raises(InvalidLoginCredentialsError):
        service.login(LoginRequest(email="ana@empresa.com", password=password))

    assert audit.failed_events[0].action == LOGIN_FAILED


def test_token_claims_use_public_ids_without_internal_ids(
    auth_settings: AuthSettings,
) -> None:
    hasher = PwdlibPasswordHasher()
    user = LoginUserRecord(
        user_public_id="usr_public",
        organization_public_id="org_public",
        password_hash=hasher.hash(VALID_CREDENTIAL),
        status="ACTIVE",
    )
    audit = SpyAuditAdapter()
    service, _ = build_service(user, auth_settings, audit)

    token_data = service.login(
        LoginRequest(email="ana@empresa.com", password=VALID_CREDENTIAL),
    )
    payload = jwt.decode(
        token_data.access_token,
        auth_settings.jwt_secret_key,
        algorithms=[auth_settings.jwt_algorithm],
    )

    assert payload["sub"] == "usr_public"
    assert payload["org"] == "org_public"
    assert "id_user" not in payload
    assert "id_organization" not in payload
    assert "password_hash" not in payload
    assert "roles" not in payload


def test_audit_events_do_not_contain_password_hash_or_token(
    auth_settings: AuthSettings,
) -> None:
    hasher = PwdlibPasswordHasher()
    user = LoginUserRecord(
        user_public_id="usr_public",
        organization_public_id="org_public",
        password_hash=hasher.hash(VALID_CREDENTIAL),
        status="ACTIVE",
    )
    audit = SpyAuditAdapter()
    service, _ = build_service(user, auth_settings, audit)

    service.login(LoginRequest(email="ana@empresa.com", password=VALID_CREDENTIAL))

    success_event = audit.success_events[0]
    event_payload = asdict(success_event)
    assert success_event.action == LOGIN_SUCCESS
    assert "password" not in event_payload
    assert "password_hash" not in event_payload
    assert "token" not in event_payload
    assert success_event.user_public_id == "usr_public"
