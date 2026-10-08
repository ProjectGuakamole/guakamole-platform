"""Dependencias reutilizables para protección CSRF explícita."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from jwt import InvalidTokenError

from app.domain.auth.config import AuthSettings
from app.domain.auth.csrf_exceptions import InvalidCsrfTokenError
from app.domain.auth.csrf_services import CsrfTokenService
from app.domain.auth.dependencies import build_auth_settings
from app.domain.auth.tokens import JwtAccessTokenService, VerifiedAccessToken


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
    request: Request,
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> VerifiedAccessToken:
    access_token = request.cookies.get(auth_settings.auth_cookie_name)
    if access_token is None:
        raise unauthorized_response()
    try:
        return JwtAccessTokenService(auth_settings).verify_access_token(access_token)
    except InvalidTokenError as error:
        raise unauthorized_response() from error


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
