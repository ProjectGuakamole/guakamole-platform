"""Composición HTTP del caso de uso de login."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domains.auth.login.audit import StructuredLoginAuditAdapter
from app.domains.auth.login.repository import SqlAlchemyLoginUserRepository
from app.domains.auth.login.service import LoginService
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.dependencies import build_auth_settings
from app.domains.auth.shared.password_hasher import PwdlibPasswordHasher
from app.domains.auth.shared.tokens import JwtAccessTokenService


def get_login_service(
    session: Annotated[Session, Depends(get_db_session)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> LoginService:
    return LoginService(
        repository=SqlAlchemyLoginUserRepository(session),
        password_hasher=PwdlibPasswordHasher(),
        token_issuer=JwtAccessTokenService(auth_settings),
        audit=StructuredLoginAuditAdapter(),
    )
