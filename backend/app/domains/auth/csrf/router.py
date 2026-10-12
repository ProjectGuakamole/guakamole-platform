"""Router FastAPI para emisión de tokens CSRF."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.domains.auth.csrf.schemas import CsrfTokenResponse
from app.domains.auth.csrf.service import CsrfTokenService
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.csrf_dependencies import (
    get_verified_access_token_from_cookie,
)
from app.domains.auth.shared.dependencies import build_auth_settings
from app.domains.auth.shared.tokens import VerifiedAccessToken

router = APIRouter()


@router.get("/csrf", response_model=CsrfTokenResponse)
def csrf(
    verified_access_token: Annotated[
        VerifiedAccessToken,
        Depends(get_verified_access_token_from_cookie),
    ],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> CsrfTokenResponse:
    """Emite un token CSRF ligado a la sesión autenticada actual."""

    csrf_token = CsrfTokenService(auth_settings).issue_csrf_token(verified_access_token)
    return CsrfTokenResponse(csrf_token=csrf_token)
