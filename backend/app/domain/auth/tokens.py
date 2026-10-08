"""Emisión y verificación de access tokens JWT mínimos."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol, cast
from uuid import uuid4

import jwt
from jwt import InvalidTokenError

from app.domain.auth.config import AuthSettings

ACCESS_CLAIM_VALUE = "access"


class TokenIssuer(Protocol):
    """Puerto para emisión de access tokens."""

    def issue_access_token(self, subject: str, organization: str | None = None) -> str:
        """Emite un access token para el sujeto autenticado."""


class TokenVerifier(Protocol):
    """Puerto para validación de access tokens propios."""

    def verify_access_token(self, token: str) -> "VerifiedAccessToken":
        """Valida y normaliza un access token."""


@dataclass(frozen=True, slots=True)
class VerifiedAccessToken:
    """Datos mínimos confiables extraídos de un access token válido."""

    subject: str
    organization: str | None
    jti: str
    issued_at: datetime
    expires_at: datetime


class JwtAccessTokenService:
    """Servicio JWT mínimo para emitir y verificar tokens propios."""

    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings

    def issue_access_token(self, subject: str, organization: str | None = None) -> str:
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(
            minutes=self._settings.access_token_expire_minutes,
        )
        payload: dict[str, object] = {
            "sub": subject,
            "type": ACCESS_CLAIM_VALUE,
            "jti": str(uuid4()),
            "iat": issued_at,
            "exp": expires_at,
        }
        if organization is not None:
            payload["org"] = organization
        return jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )

    def verify_access_token(self, token: str) -> VerifiedAccessToken:
        payload = self._decode_token(token)
        if payload.get("type") != ACCESS_CLAIM_VALUE:
            raise InvalidTokenError("El token no es de tipo access.")
        return VerifiedAccessToken(
            subject=self._required_str(payload, "sub"),
            organization=self._optional_str(payload, "org"),
            jti=self._required_str(payload, "jti"),
            issued_at=self._required_datetime(payload, "iat"),
            expires_at=self._required_datetime(payload, "exp"),
        )

    def _decode_token(self, token: str) -> dict[str, object]:
        decoded = jwt.decode(
            token,
            self._settings.jwt_secret_key,
            algorithms=[self._settings.jwt_algorithm],
            options={"require": ["sub", "type", "jti", "iat", "exp"]},
        )
        return cast(dict[str, object], decoded)

    @staticmethod
    def _required_str(payload: dict[str, object], claim: str) -> str:
        value = payload.get(claim)
        if not isinstance(value, str) or not value:
            raise InvalidTokenError(f"Claim inválido: {claim}.")
        return value

    @staticmethod
    def _optional_str(payload: dict[str, object], claim: str) -> str | None:
        value = payload.get(claim)
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            raise InvalidTokenError(f"Claim inválido: {claim}.")
        return value

    @staticmethod
    def _required_datetime(payload: dict[str, object], claim: str) -> datetime:
        value = payload.get(claim)
        if not isinstance(value, int):
            raise InvalidTokenError(f"Claim inválido: {claim}.")
        return datetime.fromtimestamp(value, UTC)
