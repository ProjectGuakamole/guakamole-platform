"""Router FastAPI para login con cookie HttpOnly."""

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.rate_limit import require_auth_login_rate_limit
from app.domains.auth.config import AuthSettings
from app.domains.auth.cookies import build_auth_cookie_settings
from app.domains.auth.dependencies import build_auth_settings
from app.domains.auth.login_exceptions import InvalidLoginCredentialsError
from app.domains.auth.login_repositories import SqlAlchemyLoginUserRepository
from app.domains.auth.login_schemas import LoginRequest, LoginResponse
from app.domains.auth.login_services import LoginService, NoOpLoginAuditAdapter
from app.domains.auth.password_hasher import PwdlibPasswordHasher
from app.domains.auth.tokens import JwtAccessTokenService
from app.domains.iam.users.dependencies import get_db_session

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
