"""Dependencias FastAPI para el piloto IAM/users."""

import os
from collections.abc import Generator
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Path, Query, status
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.iam.access.tenant_context import (
    ACTIVE_STATUS,
    PLATFORM_ADMIN_ROLE,
    TenantContext,
    TenantContextError,
    build_tenant_context,
)
from app.domain.iam.users.repositories import SqlAlchemyOrganizationUsersRepository
from app.domain.iam.users.schemas import SortDirection, UserListQuery, UserListSortField
from app.domain.iam.users.services import ListOrganizationUsersService

DATABASE_URL_ENV_VAR = "DATABASE_URL"


@dataclass(frozen=True, slots=True)
class PilotAuthenticatedUser:
    """Identidad autenticada mínima hasta integrar el sistema auth real."""

    user_id: int
    organization_id: int
    platform_role: str
    organization_role: str
    user_status: str = ACTIVE_STATUS
    organization_status: str = ACTIVE_STATUS


def get_user_list_query(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(max_length=100)] = None,
    sort_by: Annotated[UserListSortField, Query()] = "email",
    sort_dir: Annotated[SortDirection, Query()] = "asc",
) -> UserListQuery:
    """Construye el schema validado de query params del listado."""

    return UserListQuery(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


def get_pilot_authenticated_user() -> PilotAuthenticatedUser:
    """Dependency provisional: debe sustituirse por auth real en la Task 8+.

    No acepta identidad, roles ni organización desde query/body. En tests o en el
    futuro router deberá sobrescribirse por una dependencia de autenticación real
    que derive estos datos de credenciales verificadas.
    """

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="La autenticación real todavía no está integrada en el piloto IAM.",
    )


def get_tenant_context(
    organization_id: Annotated[int, Path(gt=0)],
    actor: Annotated[PilotAuthenticatedUser, Depends(get_pilot_authenticated_user)],
) -> TenantContext:
    """Construye TenantContext desde path validado e identidad resuelta."""

    try:
        return build_tenant_context(
            actor_user_id=actor.user_id,
            requested_organization_id=organization_id,
            effective_organization_id=actor.organization_id,
            platform_role=actor.platform_role,
            organization_role=actor.organization_role,
            user_status=actor.user_status,
            organization_status=actor.organization_status,
            is_platform_admin=actor.platform_role == PLATFORM_ADMIN_ROLE,
        )
    except TenantContextError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para operar sobre la organización solicitada.",
        ) from error


def get_required_database_url() -> str:
    """Obtiene la URL de base de datos para dependencies HTTP."""

    database_url = os.environ.get(DATABASE_URL_ENV_VAR)
    if database_url is None or database_url == "":
        raise RuntimeError(
            f"La variable de entorno {DATABASE_URL_ENV_VAR} debe estar definida."
        )
    return database_url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Crea el engine SQLAlchemy compartido del proceso API."""

    return create_engine(get_required_database_url(), hide_parameters=True)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Crea la factoría de sesiones SQLAlchemy para FastAPI."""

    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    """Proporciona una sesión SQLAlchemy por request."""

    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def get_list_organization_users_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ListOrganizationUsersService:
    """Construye el caso de uso con el repository SQLAlchemy real."""

    repository = SqlAlchemyOrganizationUsersRepository(session)
    return ListOrganizationUsersService(repository=repository)


__all__ = (
    "PilotAuthenticatedUser",
    "get_db_session",
    "get_list_organization_users_service",
    "get_pilot_authenticated_user",
    "get_tenant_context",
    "get_user_list_query",
)
