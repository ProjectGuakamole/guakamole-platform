"""Repositorio de identidad autenticada para /auth/me."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.iam.access.models import Status
from app.domain.iam.organizations.models import Organization
from app.domain.iam.users.models import User


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
        statement = (
            select(User.public_id, Organization.public_id)
            .join(Organization, Organization.id_organization == User.id_organization)
            .join(Status, Status.id_status == User.id_status)
            .where(User.public_id == user_public_id)
            .where(Organization.public_id == organization_public_id)
            .where(Status.status == "ACTIVE")
        )
        row = self._session.execute(statement).one_or_none()
        if row is None:
            return None
        return AuthenticatedIdentityRecord(
            user_public_id=row[0],
            organization_public_id=row[1],
        )
