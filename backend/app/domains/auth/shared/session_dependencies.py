"""Composición FastAPI del caso de uso de sesión autenticada."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domains.auth.logout.audit import StructuredLogoutAuditAdapter
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.dependencies import build_auth_settings
from app.domains.auth.shared.session_repository import SqlAlchemySessionStateRepository
from app.domains.auth.shared.session_service import (
    AuthSessionService,
    InvalidSessionError,
)
from app.domains.auth.shared.tokens import JwtAccessTokenService, VerifiedAccessToken


def unauthorized_response() -> HTTPException:
    """Construye una respuesta uniforme para una sesión no utilizable."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado."
    )


def get_auth_session_service(
    session: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> AuthSessionService:
    return AuthSessionService(
        JwtAccessTokenService(settings),
        SqlAlchemySessionStateRepository(session),
        StructuredLogoutAuditAdapter(),
    )


def get_raw_access_token(
    request: Request,
    settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> str:
    """Extrae la cookie antes de abrir una sesión de base de datos."""
    raw_token = request.cookies.get(settings.auth_cookie_name)
    if raw_token is None:
        raise unauthorized_response()
    return raw_token


def get_active_access_token(
    raw_token: Annotated[str, Depends(get_raw_access_token)],
    service: Annotated[AuthSessionService, Depends(get_auth_session_service)],
) -> VerifiedAccessToken:
    try:
        token, _ = service.validate(raw_token)
    except InvalidSessionError as error:
        raise unauthorized_response() from error
    return token
