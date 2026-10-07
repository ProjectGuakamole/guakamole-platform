"""Tests unitarios del core reutilizable de autenticación."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import ValidationError

from app.domain.auth.config import AuthSettings
from app.domain.auth.cookies import build_auth_cookie_settings
from app.domain.auth.password_hasher import PwdlibPasswordHasher
from app.domain.auth.public_ids import (
    PublicIdPrefix,
    generate_public_id,
    parse_public_uuid,
)
from app.domain.auth.tokens import ACCESS_CLAIM_VALUE, JwtAccessTokenService


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings.model_validate(
        {"jwt_secret_key": "test-secret-not-for-production-with-safe-length"},
    )


@pytest.mark.test_unit
def test_auth_settings_accepts_legacy_jwt_secret_alias() -> None:
    settings = AuthSettings.model_validate(
        {"JWT_SECRET": "legacy-test-secret-not-for-production"},
    )

    configured_value = settings.jwt_secret_key

    assert configured_value == "legacy-test-secret-not-for-production"


@pytest.mark.test_unit
def test_auth_settings_prefers_jwt_secret_key_over_legacy_alias() -> None:
    settings = AuthSettings.model_validate(
        {
            "JWT_SECRET_KEY": "preferred-test-secret-not-for-production",
            "JWT_SECRET": "legacy-test-secret-not-for-production",
        },
    )

    configured_value = settings.jwt_secret_key

    assert configured_value == "preferred-test-secret-not-for-production"


@pytest.mark.test_unit
def test_auth_settings_normalizes_valid_cookie_samesite() -> None:
    settings = AuthSettings.model_validate(
        {
            "jwt_secret_key": "test-secret-not-for-production-with-safe-length",
            "auth_cookie_samesite": "Strict",
        },
    )

    assert settings.auth_cookie_samesite == "strict"


@pytest.mark.test_unit
def test_auth_settings_rejects_invalid_cookie_samesite() -> None:
    with pytest.raises(ValidationError):
        AuthSettings.model_validate(
            {
                "jwt_secret_key": "test-secret-not-for-production-with-safe-length",
                "auth_cookie_samesite": "invalid",
            },
        )


@pytest.mark.test_unit
def test_auth_settings_rejects_invalid_jwt_algorithm() -> None:
    with pytest.raises(ValidationError):
        AuthSettings.model_validate(
            {
                "jwt_secret_key": "test-secret-not-for-production-with-safe-length",
                "jwt_algorithm": "RS256",
            },
        )


@pytest.mark.test_unit
def test_password_hash_is_not_plain_password() -> None:
    hasher = PwdlibPasswordHasher()
    raw_credential = "PasswordSeguro123!"

    password_hash = hasher.hash(raw_credential)

    assert password_hash != raw_credential


@pytest.mark.test_unit
def test_password_verify_ok() -> None:
    hasher = PwdlibPasswordHasher()
    password_hash = hasher.hash("PasswordSeguro123!")

    assert hasher.verify("PasswordSeguro123!", password_hash) is True


@pytest.mark.test_unit
def test_password_verify_fail() -> None:
    hasher = PwdlibPasswordHasher()
    password_hash = hasher.hash("PasswordSeguro123!")

    assert hasher.verify("PasswordIncorrecto123!", password_hash) is False


@pytest.mark.test_unit
def test_token_issuer_contains_only_minimum_required_claims(
    auth_settings: AuthSettings,
) -> None:
    token = JwtAccessTokenService(auth_settings).issue_access_token("usr_123")

    payload = jwt.decode(
        token,
        auth_settings.jwt_secret_key,
        algorithms=[auth_settings.jwt_algorithm],
    )

    assert {"sub", "type", "jti", "iat", "exp"}.issubset(payload)
    assert payload["sub"] == "usr_123"
    assert payload["type"] == ACCESS_CLAIM_VALUE
    assert "organization_id" not in payload
    assert "roles" not in payload
    assert "permissions" not in payload
    assert "email" not in payload


@pytest.mark.test_unit
def test_token_verifier_accepts_issued_token(auth_settings: AuthSettings) -> None:
    service = JwtAccessTokenService(auth_settings)
    token = service.issue_access_token("usr_123")

    verified = service.verify_access_token(token)

    assert verified.subject == "usr_123"
    assert UUID(verified.jti)
    assert verified.expires_at > verified.issued_at


@pytest.mark.test_unit
def test_token_verifier_rejects_expired_token(auth_settings: AuthSettings) -> None:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "usr_123",
            "type": ACCESS_CLAIM_VALUE,
            "jti": "11111111-1111-4111-8111-111111111111",
            "iat": now - timedelta(minutes=30),
            "exp": now - timedelta(minutes=15),
        },
        auth_settings.jwt_secret_key,
        algorithm=auth_settings.jwt_algorithm,
    )

    with pytest.raises(ExpiredSignatureError):
        JwtAccessTokenService(auth_settings).verify_access_token(token)


@pytest.mark.test_unit
def test_token_verifier_rejects_wrong_token_type(auth_settings: AuthSettings) -> None:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "usr_123",
            "type": "refresh",
            "jti": "11111111-1111-4111-8111-111111111111",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        auth_settings.jwt_secret_key,
        algorithm=auth_settings.jwt_algorithm,
    )

    with pytest.raises(InvalidTokenError):
        JwtAccessTokenService(auth_settings).verify_access_token(token)


@pytest.mark.test_unit
def test_cookie_settings_max_age_is_derived_from_token_expiration(
    auth_settings: AuthSettings,
) -> None:
    cookie_settings = build_auth_cookie_settings(auth_settings)

    assert cookie_settings.name == "guak_access_token"
    assert cookie_settings.path == "/api"
    assert cookie_settings.domain is None
    assert cookie_settings.httponly is True
    assert cookie_settings.secure is False
    assert cookie_settings.samesite == "lax"
    assert cookie_settings.max_age == 900


@pytest.mark.test_unit
@pytest.mark.parametrize(
    ("prefix", "expected_prefix"),
    [
        (PublicIdPrefix.USER, "usr_"),
        (PublicIdPrefix.ORGANIZATION, "org_"),
    ],
)
def test_public_id_helper_generates_expected_prefix_and_valid_uuid(
    prefix: PublicIdPrefix,
    expected_prefix: str,
) -> None:
    public_id = generate_public_id(prefix)

    parsed_uuid = parse_public_uuid(public_id, prefix)

    assert public_id.startswith(expected_prefix)
    assert parsed_uuid.version == 4
