"""Tests unitarios de GET /auth/me sin acoplamiento HTTP."""

from dataclasses import fields
from datetime import UTC, datetime, timedelta

import pytest
from jwt import ExpiredSignatureError, InvalidTokenError

from app.domain.auth.me_exceptions import NotAuthenticatedError
from app.domain.auth.me_repositories import AuthenticatedIdentityRecord
from app.domain.auth.me_services import AuthMeService
from app.domain.auth.tokens import VerifiedAccessToken

pytestmark = pytest.mark.test_unit


class StubTokenVerifier:
    def __init__(self, token: VerifiedAccessToken | Exception) -> None:
        self._token = token

    def verify_access_token(self, token: str) -> VerifiedAccessToken:
        _ = token
        if isinstance(self._token, Exception):
            raise self._token
        return self._token


class StubAuthMeRepository:
    def __init__(self, identity: AuthenticatedIdentityRecord | None) -> None:
        self._identity = identity
        self.requested_user_public_id: str | None = None
        self.requested_organization_public_id: str | None = None

    def find_active_identity(
        self,
        *,
        user_public_id: str,
        organization_public_id: str,
    ) -> AuthenticatedIdentityRecord | None:
        self.requested_user_public_id = user_public_id
        self.requested_organization_public_id = organization_public_id
        return self._identity


def build_verified_token(
    organization: str | None = "org_public",
) -> VerifiedAccessToken:
    issued_at = datetime.now(UTC)
    return VerifiedAccessToken(
        subject="usr_public",
        organization=organization,
        jti="jti-test",
        issued_at=issued_at,
        expires_at=issued_at + timedelta(minutes=15),
    )


def test_auth_me_service_returns_public_identity_for_valid_token_and_active_user() -> (
    None
):
    repository = StubAuthMeRepository(
        AuthenticatedIdentityRecord(
            user_public_id="usr_public",
            organization_public_id="org_public",
        ),
    )
    service = AuthMeService(
        token_verifier=StubTokenVerifier(build_verified_token()),
        repository=repository,
    )

    response = service.get_current_identity("jwt")

    assert response.model_dump() == {
        "authenticated": True,
        "user_id": "usr_public",
        "organization_id": "org_public",
    }
    assert repository.requested_user_public_id == "usr_public"
    assert repository.requested_organization_public_id == "org_public"


def test_auth_me_service_rejects_missing_org_claim() -> None:
    service = AuthMeService(
        token_verifier=StubTokenVerifier(build_verified_token(organization=None)),
        repository=StubAuthMeRepository(None),
    )

    with pytest.raises(NotAuthenticatedError):
        service.get_current_identity("jwt")


def test_auth_me_service_rejects_mismatched_org_or_missing_user() -> None:
    service = AuthMeService(
        token_verifier=StubTokenVerifier(build_verified_token()),
        repository=StubAuthMeRepository(None),
    )

    with pytest.raises(NotAuthenticatedError):
        service.get_current_identity("jwt")


@pytest.mark.parametrize(
    "token_error",
    [InvalidTokenError("invalid"), ExpiredSignatureError("expired")],
)
def test_auth_me_service_maps_invalid_or_expired_token_to_not_authenticated(
    token_error: InvalidTokenError,
) -> None:
    service = AuthMeService(
        token_verifier=StubTokenVerifier(token_error),
        repository=StubAuthMeRepository(None),
    )

    with pytest.raises(NotAuthenticatedError):
        service.get_current_identity("jwt")


def test_auth_me_response_does_not_contain_sensitive_fields() -> None:
    service = AuthMeService(
        token_verifier=StubTokenVerifier(build_verified_token()),
        repository=StubAuthMeRepository(
            AuthenticatedIdentityRecord("usr_public", "org_public"),
        ),
    )

    body = service.get_current_identity("jwt").model_dump()

    assert "email" not in body
    assert "roles" not in body
    assert "token" not in body
    assert "id_user" not in body
    assert "id_organization" not in body
    assert {field.name for field in fields(AuthenticatedIdentityRecord)} == {
        "user_public_id",
        "organization_public_id",
    }
