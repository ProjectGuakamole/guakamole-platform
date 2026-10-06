"""Tests unitarios de la policy para listar usuarios de organización."""

import pytest

from app.domain.iam.access.tenant_context import (
    InactiveOrganizationError,
    InactiveUserError,
    TenantAccessDeniedError,
    TenantContext,
    build_tenant_context,
)
from app.domain.iam.users import policies as policies_module
from app.domain.iam.users.policies import ensure_can_list_organization_users


def test_platform_admin_can_list_cross_tenant_users() -> None:
    context = build_tenant_context(
        actor_user_id=1,
        requested_organization_id=20,
        effective_organization_id=10,
        platform_role="PLATFORM_ADMIN",
        organization_role="EMPLOYEE",
    )

    ensure_can_list_organization_users(context)


def test_company_admin_can_list_own_organization_users() -> None:
    context = build_tenant_context(
        actor_user_id=101,
        requested_organization_id=10,
        effective_organization_id=10,
        platform_role="USER",
        organization_role="COMPANY_ADMIN",
    )

    ensure_can_list_organization_users(context)


def test_company_admin_cannot_build_context_for_other_organization() -> None:
    # El acceso cross-tenant de un rol organizativo se bloquea al construir
    # TenantContext, antes de que cualquier policy pueda consultar datos.
    with pytest.raises(TenantAccessDeniedError):
        build_tenant_context(
            actor_user_id=101,
            requested_organization_id=20,
            effective_organization_id=10,
            platform_role="USER",
            organization_role="COMPANY_ADMIN",
        )


@pytest.mark.parametrize(
    "organization_role",
    ["GROUP_MANAGER", "EMPLOYEE", "UNKNOWN_ROLE"],
)
def test_non_privileged_roles_are_denied(organization_role: str) -> None:
    context = build_tenant_context(
        actor_user_id=101,
        requested_organization_id=10,
        effective_organization_id=10,
        platform_role="USER",
        organization_role=organization_role,
    )

    with pytest.raises(TenantAccessDeniedError):
        ensure_can_list_organization_users(context)


def test_policy_revalidates_inactive_user_context() -> None:
    context = TenantContext(
        actor_user_id=101,
        requested_organization_id=10,
        effective_organization_id=10,
        platform_role="USER",
        organization_role="COMPANY_ADMIN",
        user_status="DISABLED",
        organization_status="ACTIVE",
        is_platform_admin=False,
    )

    with pytest.raises(InactiveUserError):
        ensure_can_list_organization_users(context)


def test_policy_revalidates_inactive_organization_context() -> None:
    context = TenantContext(
        actor_user_id=101,
        requested_organization_id=10,
        effective_organization_id=10,
        platform_role="USER",
        organization_role="COMPANY_ADMIN",
        user_status="ACTIVE",
        organization_status="DISABLED",
        is_platform_admin=False,
    )

    with pytest.raises(InactiveOrganizationError):
        ensure_can_list_organization_users(context)


def test_policy_module_does_not_import_fastapi_or_sqlalchemy() -> None:
    module_names = set(policies_module.__dict__)

    assert "FastAPI" not in module_names
    assert "sqlalchemy" not in module_names
