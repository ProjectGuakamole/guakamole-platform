"""Router OAuth2 Password Bearer para Swagger y desarrollo."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.rate_limit import require_auth_token_rate_limit
from app.domain.auth.config import AuthSettings
from app.domain.auth.dependencies import build_auth_settings
from app.domain.auth.login_exceptions import InvalidLoginCredentialsError
from app.domain.auth.login_routers import get_login_service
from app.domain.auth.login_schemas import LoginRequest
from app.domain.auth.login_services import LoginService
from app.domain.auth.token_schemas import PasswordBearerTokenResponse

router = APIRouter()


@router.post("/token", response_model=PasswordBearerTokenResponse)
def issue_password_bearer_token(
    _rate_limit: Annotated[None, Depends(require_auth_token_rate_limit)],
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[LoginService, Depends(get_login_service)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> PasswordBearerTokenResponse:
    """Emite access token bearer para Swagger/dev sin crear cookies."""

    _ = _rate_limit
    if not auth_settings.auth_enable_password_bearer_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Endpoint OAuth2 deshabilitado.",
        )

    try:
        token_data = service.login(
            LoginRequest(email=form.username, password=form.password),
        )
    except InvalidLoginCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        ) from error

    return PasswordBearerTokenResponse(
        access_token=token_data.access_token,
        expires_in=auth_settings.access_token_expire_minutes * 60,
    )
