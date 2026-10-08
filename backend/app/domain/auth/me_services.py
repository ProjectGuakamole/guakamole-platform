"""Caso de uso de consulta de identidad autenticada."""

from jwt import InvalidTokenError

from app.domain.auth.me_exceptions import NotAuthenticatedError
from app.domain.auth.me_repositories import AuthMeRepository
from app.domain.auth.me_schemas import AuthMeResponse
from app.domain.auth.tokens import TokenVerifier


class AuthMeService:
    """Valida JWT y resuelve la identidad pública actual sin depender de FastAPI."""

    def __init__(
        self,
        *,
        token_verifier: TokenVerifier,
        repository: AuthMeRepository,
    ) -> None:
        self._token_verifier = token_verifier
        self._repository = repository

    def get_current_identity(self, token: str) -> AuthMeResponse:
        try:
            verified_token = self._token_verifier.verify_access_token(token)
        except InvalidTokenError as error:
            raise NotAuthenticatedError from error

        if verified_token.organization is None:
            raise NotAuthenticatedError

        identity = self._repository.find_active_identity(
            user_public_id=verified_token.subject,
            organization_public_id=verified_token.organization,
        )
        if identity is None:
            raise NotAuthenticatedError

        return AuthMeResponse(
            authenticated=True,
            user_id=identity.user_public_id,
            organization_id=identity.organization_public_id,
        )
