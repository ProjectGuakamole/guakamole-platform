"""Dependencias reutilizables para protección CSRF explícita."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.domains.auth.csrf.exceptions import InvalidCsrfTokenError
from app.domains.auth.csrf.service import CsrfTokenService
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.dependencies import build_auth_settings
from app.domains.auth.shared.session_dependencies import get_active_access_token
from app.domains.auth.shared.tokens import VerifiedAccessToken


def unauthorized_response() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado.",
    )


def csrf_forbidden_response() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="CSRF inválido.",
    )


def get_verified_access_token_from_cookie(
    verified_access_token: Annotated[
        VerifiedAccessToken, Depends(get_active_access_token)
    ],
) -> VerifiedAccessToken:
    """Mantiene el nombre de dependencia y exige una sesión activa."""
    return verified_access_token


def require_valid_csrf_token(
    verified_access_token: Annotated[
        VerifiedAccessToken,
        Depends(get_verified_access_token_from_cookie),
    ],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
    x_csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> None:
    if x_csrf_token is None:
        raise csrf_forbidden_response()
    try:
        CsrfTokenService(auth_settings).validate_csrf_token(
            x_csrf_token,
            verified_access_token,
        )
    except InvalidCsrfTokenError as error:
        raise csrf_forbidden_response() from error
