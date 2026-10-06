"""Repositorios de lectura para IAM/users."""

from datetime import datetime
from typing import Protocol

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import UnaryExpression

from app.domain.iam.users.models import User
from app.domain.iam.users.schemas import (
    OrganizationUserListResponse,
    OrganizationUserRead,
    UserListQuery,
)


class OrganizationUsersRepository(Protocol):
    """Contrato para listar usuarios visibles de una organización validada."""

    def list_by_organization(
        self,
        *,
        organization_id: int,
        query: UserListQuery,
    ) -> OrganizationUserListResponse:
        """Lista usuarios filtrando siempre por organización."""


class SqlAlchemyOrganizationUsersRepository:
    """Repositorio SQLAlchemy para listados seguros de usuarios IAM."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_organization(
        self,
        *,
        organization_id: int,
        query: UserListQuery,
    ) -> OrganizationUserListResponse:
        """Lista usuarios de una organización con filtros y paginación seguros."""

        base_query = self._base_query(organization_id=organization_id, query=query)
        total = self._count(base_query)
        users = self._session.scalars(
            base_query.order_by(self._sort_expression(query))
            .limit(query.limit)
            .offset(query.offset)
        ).all()

        items = [
            OrganizationUserRead.model_validate(user, from_attributes=True)
            for user in users
        ]
        return OrganizationUserListResponse(
            items=items,
            limit=query.limit,
            offset=query.offset,
            total=total,
        )

    @staticmethod
    def _base_query(
        *,
        organization_id: int,
        query: UserListQuery,
    ) -> Select[tuple[User]]:
        statement = select(User).where(User.id_organization == organization_id)
        if query.search is None:
            return statement

        search = f"%{query.search.lower()}%"
        return statement.where(
            or_(
                func.lower(User.email).like(search),
                func.lower(User.first_name).like(search),
                func.lower(User.last_name).like(search),
            )
        )

    @staticmethod
    def _sort_expression(
        query: UserListQuery,
    ) -> (
        UnaryExpression[str]
        | UnaryExpression[int]
        | UnaryExpression[datetime]
        | UnaryExpression[datetime | None]
    ):
        match query.sort_by:
            case "email":
                if query.sort_dir == "desc":
                    return User.email.desc()
                return User.email.asc()
            case "first_name":
                if query.sort_dir == "desc":
                    return User.first_name.desc()
                return User.first_name.asc()
            case "last_name":
                if query.sort_dir == "desc":
                    return User.last_name.desc()
                return User.last_name.asc()
            case "create_at":
                if query.sort_dir == "desc":
                    return User.created_at.desc()
                return User.created_at.asc()
            case "last_login_at":
                if query.sort_dir == "desc":
                    return User.last_login_at.desc()
                return User.last_login_at.asc()
            case "id_user":
                if query.sort_dir == "desc":
                    return User.id_user.desc()
                return User.id_user.asc()

    def _count(self, statement: Select[tuple[User]]) -> int:
        count_statement = select(func.count()).select_from(statement.subquery())
        return self._session.scalar(count_statement) or 0


__all__ = (
    "OrganizationUsersRepository",
    "SqlAlchemyOrganizationUsersRepository",
)
