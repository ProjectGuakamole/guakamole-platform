"""Router FastAPI para login con cookie HttpOnly."""

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.rate_limit import require_auth_login_rate_limit
from app.domains.auth.login.dependencies import get_login_service
from app.domains.auth.login.exceptions import InvalidLoginCredentialsError
from app.domains.auth.login.schemas import LoginRequest, LoginResponse
from app.domains.auth.login.service import LoginService
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.cookies import build_auth_cookie_settings
from app.domains.auth.shared.dependencies import build_auth_settings

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    response: Response,
    _rate_limit: Annotated[None, Depends(require_auth_login_rate_limit)],
    service: Annotated[LoginService, Depends(get_login_service)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> LoginResponse:
    _ = _rate_limit
    try:
        token_data = service.login(request)
    except InvalidLoginCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        ) from error

    cookie_settings = build_auth_cookie_settings(auth_settings)
    same_site = cast(Literal["lax", "strict", "none"], cookie_settings.samesite)
    response.set_cookie(
        key=cookie_settings.name,
        value=token_data.access_token,
        max_age=cookie_settings.max_age,
        httponly=cookie_settings.httponly,
        secure=cookie_settings.secure,
        samesite=same_site,
        path=cookie_settings.path,
        domain=cookie_settings.domain,
    )
    return LoginResponse()
