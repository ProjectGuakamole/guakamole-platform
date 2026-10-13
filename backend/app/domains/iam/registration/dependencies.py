"""Composición HTTP del registro público."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.dependencies import build_auth_settings
from app.domains.auth.shared.password_hasher import PwdlibPasswordHasher
from app.domains.iam.registration.repository import SqlAlchemyRegistrationRepository
from app.domains.iam.registration.service import RegistrationService
from app.shared.audit import StructuredAuditLogger


def get_registration_service(
    session: Annotated[Session, Depends(get_db_session)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> RegistrationService:
    return RegistrationService(
        repository=SqlAlchemyRegistrationRepository(session),
        password_hasher=PwdlibPasswordHasher(),
        auth_settings=auth_settings,
        audit_logger=StructuredAuditLogger(),
    )
