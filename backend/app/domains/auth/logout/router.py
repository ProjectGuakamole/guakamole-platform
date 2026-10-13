"""Router FastAPI para logout mediante eliminación de cookie HttpOnly."""

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Response

from app.domains.auth.logout.schemas import LogoutResponse
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.cookies import build_auth_cookie_settings
from app.domains.auth.shared.csrf_dependencies import require_valid_csrf_token
from app.domains.auth.shared.dependencies import build_auth_settings
from app.domains.auth.shared.session_dependencies import (
    get_active_access_token,
    get_auth_session_service,
)
from app.domains.auth.shared.session_service import AuthSessionService
from app.domains.auth.shared.tokens import VerifiedAccessToken

router = APIRouter()


@router.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    _valid_csrf: Annotated[None, Depends(require_valid_csrf_token)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
    access_token: Annotated[VerifiedAccessToken, Depends(get_active_access_token)],
    session_service: Annotated[AuthSessionService, Depends(get_auth_session_service)],
) -> LogoutResponse:
    """Cierra la sesión del navegador eliminando la cookie de access token."""

    _ = _valid_csrf
    session_service.revoke(access_token)
    cookie_settings = build_auth_cookie_settings(auth_settings)
    same_site = cast(Literal["lax", "strict", "none"], cookie_settings.samesite)
    response.delete_cookie(
        key=cookie_settings.name,
        path=cookie_settings.path,
        domain=cookie_settings.domain,
        secure=cookie_settings.secure,
        httponly=True,
        samesite=same_site,
    )
    return LogoutResponse()
