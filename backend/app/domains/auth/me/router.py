"""Router FastAPI para GET /auth/me."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.domains.auth.me.exceptions import NotAuthenticatedError
from app.domains.auth.me.repository import SqlAlchemyAuthMeRepository
from app.domains.auth.me.schemas import AuthMeResponse
from app.domains.auth.me.service import AuthMeService
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.dependencies import build_auth_settings
from app.domains.auth.shared.tokens import JwtAccessTokenService
from app.domains.iam.users.dependencies import get_db_session

router = APIRouter()


def get_auth_me_service(
    session: Annotated[Session, Depends(get_db_session)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> AuthMeService:
    return AuthMeService(
        token_verifier=JwtAccessTokenService(auth_settings),
        repository=SqlAlchemyAuthMeRepository(session),
    )


def unauthorized_response() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado.",
    )


@router.get("/me", response_model=AuthMeResponse)
def me(
    request: Request,
    service: Annotated[AuthMeService, Depends(get_auth_me_service)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> AuthMeResponse:
    guak_access_token = request.cookies.get(auth_settings.auth_cookie_name)
    if guak_access_token is None:
        raise unauthorized_response()
    try:
        return service.get_current_identity(guak_access_token)
    except NotAuthenticatedError as error:
        raise unauthorized_response() from error
