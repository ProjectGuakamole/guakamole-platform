"""Casos de uso para IAM/users."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol

from app.domain.iam.access.tenant_context import TenantContext
from app.domain.iam.users.policies import ListOrganizationUsersPolicy
from app.domain.iam.users.repositories import OrganizationUsersRepository
from app.domain.iam.users.schemas import (
    OrganizationUserListResponse,
    UserListQuery,
)

IAM_ORGANIZATION_USERS_LISTED = "IAM_ORGANIZATION_USERS_LISTED"
AuditMetadataValue = bool | int | str | None
AuditMetadata = Mapping[str, AuditMetadataValue]


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Evento auditable mínimo emitido por el piloto IAM/users."""

    action: str
    metadata: AuditMetadata

    def __post_init__(self) -> None:
        """Congela la metadata para impedir mutaciones posteriores."""
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class AuditLogger(Protocol):
    """Puerto mínimo para emitir eventos auditables."""

    def emit(self, event: AuditEvent) -> None:
        """Registra un evento auditable."""


class NoopAuditLogger:
    """Implementación segura por defecto hasta integrar auditoría real."""

    def emit(self, event: AuditEvent) -> None:
        """Descarta el evento sin efectos secundarios."""
        _ = event


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
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._repository = repository
        self._policy = policy or ListOrganizationUsersPolicy()
        self._audit_logger = audit_logger or NoopAuditLogger()

    def list_users(
        self,
        *,
        context: TenantContext,
        query: UserListQuery,
    ) -> OrganizationUserListResponse:
        """Lista usuarios tras autorizar el TenantContext recibido."""
        self._policy.ensure_allowed(context)
        response = self._repository.list_by_organization(
            organization_id=context.requested_organization_id,
            query=query,
        )
        self._audit_logger.emit(
            build_users_listed_audit_event(
                context=context,
                query=query,
                result_count=len(response.items),
            )
        )
        return response


def build_users_listed_audit_event(
    *,
    context: TenantContext,
    query: UserListQuery,
    result_count: int,
) -> AuditEvent:
    """Construye metadata audit segura para el listado de usuarios IAM."""
    return AuditEvent(
        action=IAM_ORGANIZATION_USERS_LISTED,
        metadata={
            "requested_organization_id": context.requested_organization_id,
            "effective_organization_id": context.effective_organization_id,
            "actor_user_id": context.actor_user_id,
            "actor_platform_role": context.platform_role,
            "actor_organization_role": context.organization_role,
            "cross_tenant": not context.is_same_organization,
            "result_count": result_count,
            "limit": query.limit,
            "offset": query.offset,
            "search_present": query.search is not None,
            "sort_by": query.sort_by,
            "sort_dir": query.sort_dir,
        },
    )


__all__ = (
    "AuditEvent",
    "AuditLogger",
    "AuditMetadata",
    "AuditMetadataValue",
    "IAM_ORGANIZATION_USERS_LISTED",
    "ListOrganizationUsersAuthorizer",
    "ListOrganizationUsersService",
    "NoopAuditLogger",
    "build_users_listed_audit_event",
)
