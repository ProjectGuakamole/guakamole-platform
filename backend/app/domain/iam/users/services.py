"""Casos de uso para IAM/users."""

from typing import Protocol

from app.domain.iam.access.tenant_context import TenantContext
from app.domain.iam.users.policies import ListOrganizationUsersPolicy
from app.domain.iam.users.repositories import OrganizationUsersRepository
from app.domain.iam.users.schemas import (
    OrganizationUserListResponse,
    UserListQuery,
)


class ListOrganizationUsersAuthorizer(Protocol):
    """Contrato mínimo para autorizar el listado de usuarios."""

    def ensure_allowed(self, context: TenantContext) -> None:
        """Lanza un error controlado si el contexto no está autorizado."""


class ListOrganizationUsersService:
    """Orquesta el caso de uso de listado de usuarios de organización."""

    def __init__(
        self,
        *,
        repository: OrganizationUsersRepository,
        policy: ListOrganizationUsersAuthorizer | None = None,
    ) -> None:
        self._repository = repository
        self._policy = policy or ListOrganizationUsersPolicy()

    def list_users(
        self,
        *,
        context: TenantContext,
        query: UserListQuery,
    ) -> OrganizationUserListResponse:
        """Lista usuarios tras autorizar el TenantContext recibido."""
        self._policy.ensure_allowed(context)
        return self._repository.list_by_organization(
            organization_id=context.requested_organization_id,
            query=query,
        )


__all__ = (
    "ListOrganizationUsersAuthorizer",
    "ListOrganizationUsersService",
)
