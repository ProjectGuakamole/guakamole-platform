"""Policies de autorización para IAM/users."""

from app.domain.iam.access.tenant_context import (
    TenantAccessDeniedError,
    TenantContext,
    validate_tenant_context,
)

COMPANY_ADMIN_ROLE = "COMPANY_ADMIN"


class ListOrganizationUsersPolicy:
    """Autoriza el caso de uso de listado de usuarios de organización."""

    def ensure_allowed(self, context: TenantContext) -> None:
        """Lanza un error controlado si el actor no puede listar usuarios."""
        validate_tenant_context(context)

        if context.is_platform_admin:
            return

        if (
            context.organization_role == COMPANY_ADMIN_ROLE
            and context.is_same_organization
        ):
            return

        raise TenantAccessDeniedError(
            "El actor no puede listar usuarios de la organización solicitada."
        )


def ensure_can_list_organization_users(context: TenantContext) -> None:
    """Autoriza el listado de usuarios usando la policy del caso de uso."""
    ListOrganizationUsersPolicy().ensure_allowed(context)


__all__ = [
    "COMPANY_ADMIN_ROLE",
    "ListOrganizationUsersPolicy",
    "ensure_can_list_organization_users",
]
