"""Tests unitarios del core reutilizable de autenticación."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import ValidationError

from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.cookies import build_auth_cookie_settings
from app.domains.auth.shared.password_hasher import PwdlibPasswordHasher
from app.domains.auth.shared.public_ids import (
    PublicIdPrefix,
    generate_public_id,
    parse_public_uuid,
)
from app.domains.auth.shared.tokens import ACCESS_CLAIM_VALUE, JwtAccessTokenService

SETTINGS_INPUT = {
    "app_env": "test",
    "database_url": "postgresql+psycopg://test:test@localhost/test_db",
    "jwt_secret_key": "test-secret-not-for-production-with-safe-length",
}


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings.model_validate(
        SETTINGS_INPUT,
    )


@pytest.mark.test_unit
def test_auth_settings_requires_jwt_secret_without_input() -> None:
    with pytest.raises(ValidationError):
        AuthSettings.model_validate({})


@pytest.mark.test_unit
def test_auth_settings_uses_synthetic_context_for_isolated_collaborators() -> None:
    settings = AuthSettings.model_validate(SETTINGS_INPUT)

    assert settings.app_env == "test"


@pytest.mark.test_unit
def test_auth_settings_uses_explicit_jwt_secret_key() -> None:
    settings = AuthSettings.model_validate(SETTINGS_INPUT)

    assert settings.jwt_secret_key == SETTINGS_INPUT["jwt_secret_key"]


@pytest.mark.test_unit
def test_auth_settings_normalizes_valid_cookie_samesite() -> None:
    settings = AuthSettings.model_validate(
        {
            **SETTINGS_INPUT,
            "auth_cookie_samesite": "Strict",
        },
    )

    assert settings.auth_cookie_samesite == "strict"


@pytest.mark.test_unit
def test_auth_settings_rejects_invalid_cookie_samesite() -> None:
    with pytest.raises(ValidationError):
        AuthSettings.model_validate(
            {
                **SETTINGS_INPUT,
                "auth_cookie_samesite": "invalid",
            },
        )


@pytest.mark.test_unit
def test_auth_settings_rejects_invalid_jwt_algorithm() -> None:
    with pytest.raises(ValidationError):
        AuthSettings.model_validate(
            {
                **SETTINGS_INPUT,
                "jwt_algorithm": "RS256",
            },
        )


@pytest.mark.test_unit
def test_auth_settings_rejects_jwt_secret_shorter_than_32_characters() -> None:
    with pytest.raises(ValidationError):
        AuthSettings.model_validate({**SETTINGS_INPUT, "jwt_secret_key": "too-short"})


@pytest.mark.test_unit
def test_auth_settings_rejects_samesite_none_without_secure_cookie() -> None:
    with pytest.raises(ValidationError):
        AuthSettings.model_validate(
            {
                **SETTINGS_INPUT,
                "auth_cookie_samesite": "none",
                "auth_cookie_secure": False,
            },
        )


@pytest.mark.test_unit
def test_auth_settings_accepts_samesite_none_with_secure_cookie() -> None:
    settings = AuthSettings.model_validate(
        {
            **SETTINGS_INPUT,
            "auth_cookie_samesite": "none",
            "auth_cookie_secure": True,
        },
    )

    assert settings.auth_cookie_samesite == "none"
    assert settings.auth_cookie_secure is True


@pytest.mark.test_unit
def test_auth_settings_disables_password_bearer_token_by_default() -> None:
    settings = AuthSettings.model_validate(
        SETTINGS_INPUT,
    )

    assert settings.auth_enable_password_bearer_token is False


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
    assert cookie_settings.secure is True
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
    assert len(public_id) <= 40
    assert parsed_uuid.version == 4


@pytest.mark.test_unit
@pytest.mark.parametrize("prefix", list(PublicIdPrefix))
def test_public_id_parser_accepts_canonical_generated_ids(
    prefix: PublicIdPrefix,
) -> None:
    public_id = generate_public_id(prefix)

    assert parse_public_uuid(public_id, prefix).bytes


@pytest.mark.test_unit
@pytest.mark.parametrize(
    "public_id",
    [
        "org_!!!!!!!!!!!!!!!!!!!!!!",
        "org_abcdefghijklmnopqrstu",
        "org_abcdefghijklmnopqrstuvw",
        "org_abcdefghijklmnopqrstuv=",
        "org_abcdefghijklmnopqrstuvextra",
        "org_AAAAAAAAAAAAAAAAAAAAAB",
    ],
)
def test_public_id_parser_rejects_noncanonical_or_malformed_values(
    public_id: str,
) -> None:
    with pytest.raises(ValueError, match="UUID inválido"):
        parse_public_uuid(public_id, PublicIdPrefix.ORGANIZATION)
