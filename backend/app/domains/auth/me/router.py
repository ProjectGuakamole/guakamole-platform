"""Router FastAPI para GET /auth/me."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.domains.auth.me.dependencies import get_auth_me_service
from app.domains.auth.me.exceptions import NotAuthenticatedError
from app.domains.auth.me.schemas import AuthMeResponse
from app.domains.auth.me.service import AuthMeService
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.dependencies import build_auth_settings

router = APIRouter()


def unauthorized_response() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado.",
    )


@router.get("/me", response_model=AuthMeResponse)
def me(
    request: Request,
    service: Annotated[AuthMeService, Depends(get_auth_me_service)],
    settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> AuthMeResponse:
    raw_token = request.cookies.get(settings.auth_cookie_name)
    if raw_token is None:
        raise unauthorized_response()
    try:
        return service.get_current_identity(raw_token)
    except NotAuthenticatedError as error:
        raise unauthorized_response() from error
