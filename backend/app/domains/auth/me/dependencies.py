"""Composición HTTP del caso de uso de identidad autenticada."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domains.auth.me.repository import SqlAlchemyAuthMeRepository
from app.domains.auth.me.service import AuthMeService
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.dependencies import build_auth_settings
from app.domains.auth.shared.tokens import JwtAccessTokenService


def get_auth_me_service(
    session: Annotated[Session, Depends(get_db_session)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> AuthMeService:
    return AuthMeService(
        token_verifier=JwtAccessTokenService(auth_settings),
        repository=SqlAlchemyAuthMeRepository(session),
    )
