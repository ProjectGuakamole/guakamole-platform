"""Router FastAPI para login con cookie HttpOnly."""

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.domain.auth.config import AuthSettings
from app.domain.auth.cookies import build_auth_cookie_settings
from app.domain.auth.dependencies import build_auth_settings
from app.domain.auth.login_exceptions import InvalidLoginCredentialsError
from app.domain.auth.login_repositories import SqlAlchemyLoginUserRepository
from app.domain.auth.login_schemas import LoginRequest, LoginResponse
from app.domain.auth.login_services import LoginService, NoOpLoginAuditAdapter
from app.domain.auth.password_hasher import PwdlibPasswordHasher
from app.domain.auth.tokens import JwtAccessTokenService
from app.domain.iam.users.dependencies import get_db_session

router = APIRouter()


def get_login_service(
    session: Annotated[Session, Depends(get_db_session)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> LoginService:
    return LoginService(
        repository=SqlAlchemyLoginUserRepository(session),
        password_hasher=PwdlibPasswordHasher(),
        token_issuer=JwtAccessTokenService(auth_settings),
        audit=NoOpLoginAuditAdapter(),
    )


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    response: Response,
    service: Annotated[LoginService, Depends(get_login_service)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> LoginResponse:
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
