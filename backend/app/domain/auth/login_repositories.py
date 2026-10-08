"""Repositorios de autenticación por email/password."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.iam.access.models import Status
from app.domain.iam.organizations.models import Organization
from app.domain.iam.users.models import User


@dataclass(frozen=True, slots=True)
class LoginUserRecord:
    """Datos mínimos necesarios para autenticar un usuario."""

    user_public_id: str
    organization_public_id: str
    password_hash: str
    status: str


class LoginUserRepository(Protocol):
    """Puerto de consulta de usuarios para login."""

    def find_by_normalized_email(self, email: str) -> LoginUserRecord | None:
        """Busca un usuario por email normalizado."""


class SqlAlchemyLoginUserRepository:
    """Repository SQLAlchemy para consulta de credenciales."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_normalized_email(self, email: str) -> LoginUserRecord | None:
        statement = (
            select(
                User.public_id,
                Organization.public_id,
                User.password_hash,
                Status.status,
            )
            .join(Organization, Organization.id_organization == User.id_organization)
            .join(Status, Status.id_status == User.id_status)
            .where(func.lower(User.email) == email.lower())
        )
        row = self._session.execute(statement).one_or_none()
        if row is None:
            return None
        return LoginUserRecord(
            user_public_id=row[0],
            organization_public_id=row[1],
            password_hash=row[2],
            status=row[3],
        )
