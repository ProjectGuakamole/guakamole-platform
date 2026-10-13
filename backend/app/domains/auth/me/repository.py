"""Repositorio de identidad autenticada para /auth/me."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.domains.auth.shared.models import RevokedAccessToken
from app.domains.iam.access.models import Status
from app.domains.iam.organizations.models import Organization
from app.domains.iam.users.models import User


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentityRecord:
    """Datos públicos mínimos de un usuario autenticado."""

    user_public_id: str
    organization_public_id: str


class AuthMeRepository(Protocol):
    """Puerto de lectura de identidad autenticada."""

    def find_active_identity(
        self,
        *,
        user_public_id: str,
        organization_public_id: str,
    ) -> AuthenticatedIdentityRecord | None:
        """Busca usuario activo por public IDs de usuario y organización."""

    def is_jti_revoked(self, jti: str) -> bool:
        """Indica si el identificador JWT fue revocado."""


class SqlAlchemyAuthMeRepository:
    """Repository SQLAlchemy para resolver identidad autenticada."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_active_identity(
        self,
        *,
        user_public_id: str,
        organization_public_id: str,
    ) -> AuthenticatedIdentityRecord | None:
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
            .where(user_status.status == "ACTIVE")
            .where(organization_status.status == "ACTIVE")
        )
        row = self._session.execute(statement).one_or_none()
        if row is None:
            return None
        return AuthenticatedIdentityRecord(
            user_public_id=row[0],
            organization_public_id=row[1],
        )

    def is_jti_revoked(self, jti: str) -> bool:
        statement = select(RevokedAccessToken.id_revoked_access_token).where(
            RevokedAccessToken.jti == jti
        )
        return self._session.execute(statement).scalar_one_or_none() is not None
