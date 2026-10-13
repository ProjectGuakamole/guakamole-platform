"""Adaptador ORM para el estado operativo de una sesión JWT."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.domains.auth.shared.models import RevokedAccessToken
from app.domains.iam.access.models import Status
from app.domains.iam.organizations.models import Organization
from app.domains.iam.users.models import User

ACTIVE_STATUS = "ACTIVE"


@dataclass(frozen=True, slots=True)
class ActiveSessionIdentity:
    """Identidad resuelta contra el estado actual de IAM."""

    user_public_id: str
    organization_public_id: str


class SessionStateRepository(Protocol):
    """Puerto de persistencia para validar y revocar sesiones."""

    def find_active_identity(
        self, user_public_id: str, organization_public_id: str
    ) -> ActiveSessionIdentity | None: ...

    def is_jti_revoked(self, jti: str) -> bool: ...

    def revoke(self, jti: str, expires_at: datetime) -> None: ...


class SqlAlchemySessionStateRepository:
    """Repositorio SQLAlchemy sin dependencias de transporte HTTP."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_active_identity(
        self, user_public_id: str, organization_public_id: str
    ) -> ActiveSessionIdentity | None:
        user_status = aliased(Status)
        organization_status = aliased(Status)
        statement = (
            select(User.public_id, Organization.public_id)
            .join(Organization, Organization.id_organization == User.id_organization)
            .join(user_status, user_status.id_status == User.id_status)
            .join(
                organization_status,
                organization_status.id_status == Organization.id_status,
            )
            .where(User.public_id == user_public_id)
            .where(Organization.public_id == organization_public_id)
            .where(user_status.status == ACTIVE_STATUS)
            .where(organization_status.status == ACTIVE_STATUS)
        )
        row = self._session.execute(statement).one_or_none()
        if row is None:
            return None
        return ActiveSessionIdentity(
            user_public_id=row[0], organization_public_id=row[1]
        )

    def is_jti_revoked(self, jti: str) -> bool:
        statement = select(RevokedAccessToken.id_revoked_access_token).where(
            RevokedAccessToken.jti == jti
        )
        return self._session.execute(statement).scalar_one_or_none() is not None

    def revoke(self, jti: str, expires_at: datetime) -> None:
        self._session.add(
            RevokedAccessToken(
                jti=jti,
                expires_at=expires_at,
                revoked_at=datetime.now(expires_at.tzinfo),
            ),
        )
        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            if not self.is_jti_revoked(jti):
                raise
