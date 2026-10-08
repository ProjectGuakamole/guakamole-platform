"""Servicios para emisión y validación de tokens CSRF firmados."""

from datetime import UTC, datetime
from typing import cast

import jwt
from jwt import InvalidTokenError

from app.domain.auth.config import AuthSettings
from app.domain.auth.csrf_exceptions import InvalidCsrfTokenError
from app.domain.auth.tokens import VerifiedAccessToken

CSRF_CLAIM_VALUE = "csrf"


class CsrfTokenService:
    """Emite y valida tokens CSRF ligados a un access token concreto."""

    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings

    def issue_csrf_token(self, access_token: VerifiedAccessToken) -> str:
        issued_at = datetime.now(UTC)
        payload: dict[str, object] = {
            "sub": access_token.subject,
            "type": CSRF_CLAIM_VALUE,
            "access_jti": access_token.jti,
            "iat": issued_at,
            "exp": access_token.expires_at,
        }
        return jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )

    def validate_csrf_token(
        self,
        csrf_token: str,
        access_token: VerifiedAccessToken,
    ) -> None:
        try:
            payload = self._decode_token(csrf_token)
            self._validate_payload(payload, access_token)
        except InvalidTokenError as error:
            raise InvalidCsrfTokenError from error

    def _decode_token(self, token: str) -> dict[str, object]:
        decoded = jwt.decode(
            token,
            self._settings.jwt_secret_key,
            algorithms=[self._settings.jwt_algorithm],
            options={"require": ["sub", "type", "access_jti", "iat", "exp"]},
        )
        return cast(dict[str, object], decoded)

    def _validate_payload(
        self,
        payload: dict[str, object],
        access_token: VerifiedAccessToken,
    ) -> None:
        if payload.get("type") != CSRF_CLAIM_VALUE:
            raise InvalidTokenError("El token no es de tipo csrf.")
        if self._required_str(payload, "sub") != access_token.subject:
            raise InvalidTokenError("El sujeto CSRF no coincide.")
        if self._required_str(payload, "access_jti") != access_token.jti:
            raise InvalidTokenError("El jti CSRF no coincide.")
        expires_at = self._required_datetime(payload, "exp")
        if expires_at > access_token.expires_at:
            raise InvalidTokenError("CSRF expira después del access token.")

    @staticmethod
    def _required_str(payload: dict[str, object], claim: str) -> str:
        value = payload.get(claim)
        if not isinstance(value, str) or not value:
            raise InvalidTokenError(f"Claim inválido: {claim}.")
        return value

    @staticmethod
    def _required_datetime(payload: dict[str, object], claim: str) -> datetime:
        value = payload.get(claim)
        if not isinstance(value, int):
            raise InvalidTokenError(f"Claim inválido: {claim}.")
        return datetime.fromtimestamp(value, UTC)
