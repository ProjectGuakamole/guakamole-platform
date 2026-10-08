"""Tests unitarios del servicio CSRF."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.domain.auth.config import AuthSettings
from app.domain.auth.csrf_exceptions import InvalidCsrfTokenError
from app.domain.auth.csrf_services import CSRF_CLAIM_VALUE, CsrfTokenService
from app.domain.auth.tokens import VerifiedAccessToken

pytestmark = pytest.mark.test_unit


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings.model_validate(
        {"jwt_secret_key": "test-secret-not-for-production-with-safe-length"},
    )


@pytest.fixture
def verified_access_token() -> VerifiedAccessToken:
    issued_at = datetime.now(UTC)
    return VerifiedAccessToken(
        subject="usr_123",
        organization=None,
        jti="access-jti-1",
        issued_at=issued_at,
        expires_at=issued_at + timedelta(minutes=15),
    )


def encode_csrf(
    settings: AuthSettings,
    access_token: VerifiedAccessToken,
    *,
    subject: str | None = None,
    access_jti: str | None = None,
    token_type: str = CSRF_CLAIM_VALUE,
    expires_at: datetime | None = None,
) -> str:
    return jwt.encode(
        {
            "sub": subject or access_token.subject,
            "type": token_type,
            "access_jti": access_jti or access_token.jti,
            "iat": datetime.now(UTC),
            "exp": expires_at or access_token.expires_at,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def test_csrf_issuer_contains_minimum_required_claims(
    auth_settings: AuthSettings,
    verified_access_token: VerifiedAccessToken,
) -> None:
    token = CsrfTokenService(auth_settings).issue_csrf_token(verified_access_token)

    payload = jwt.decode(
        token,
        auth_settings.jwt_secret_key,
        algorithms=[auth_settings.jwt_algorithm],
    )

    assert payload["type"] == CSRF_CLAIM_VALUE
    assert payload["sub"] == verified_access_token.subject
    assert payload["access_jti"] == verified_access_token.jti
    assert payload["exp"] <= int(verified_access_token.expires_at.timestamp())
    assert "email" not in payload
    assert "roles" not in payload
    assert "organization_id" not in payload


def test_csrf_service_validates_correct_token(
    auth_settings: AuthSettings,
    verified_access_token: VerifiedAccessToken,
) -> None:
    service = CsrfTokenService(auth_settings)
    token = service.issue_csrf_token(verified_access_token)

    service.validate_csrf_token(token, verified_access_token)


def test_csrf_service_rejects_expired_token(
    auth_settings: AuthSettings,
    verified_access_token: VerifiedAccessToken,
) -> None:
    token = encode_csrf(
        auth_settings,
        verified_access_token,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    with pytest.raises(InvalidCsrfTokenError):
        CsrfTokenService(auth_settings).validate_csrf_token(
            token,
            verified_access_token,
        )


def test_csrf_service_rejects_different_access_jti(
    auth_settings: AuthSettings,
    verified_access_token: VerifiedAccessToken,
) -> None:
    token = encode_csrf(auth_settings, verified_access_token, access_jti="other-jti")

    with pytest.raises(InvalidCsrfTokenError):
        CsrfTokenService(auth_settings).validate_csrf_token(
            token,
            verified_access_token,
        )


def test_csrf_service_rejects_different_subject(
    auth_settings: AuthSettings,
    verified_access_token: VerifiedAccessToken,
) -> None:
    token = encode_csrf(auth_settings, verified_access_token, subject="usr_other")

    with pytest.raises(InvalidCsrfTokenError):
        CsrfTokenService(auth_settings).validate_csrf_token(
            token,
            verified_access_token,
        )


def test_csrf_service_rejects_wrong_type(
    auth_settings: AuthSettings,
    verified_access_token: VerifiedAccessToken,
) -> None:
    wrong_type = "access"
    token = encode_csrf(auth_settings, verified_access_token, token_type=wrong_type)

    with pytest.raises(InvalidCsrfTokenError):
        CsrfTokenService(auth_settings).validate_csrf_token(
            token,
            verified_access_token,
        )
