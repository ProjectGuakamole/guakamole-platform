"""Router FastAPI para logout mediante eliminación de cookie HttpOnly."""

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Response

from app.domain.auth.config import AuthSettings
from app.domain.auth.cookies import build_auth_cookie_settings
from app.domain.auth.csrf_dependencies import require_valid_csrf_token
from app.domain.auth.dependencies import build_auth_settings
from app.domain.auth.logout_schemas import LogoutResponse

router = APIRouter()


@router.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    _valid_csrf: Annotated[None, Depends(require_valid_csrf_token)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> LogoutResponse:
    """Cierra la sesión del navegador eliminando la cookie de access token."""

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
