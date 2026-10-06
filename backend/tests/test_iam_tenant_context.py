"""Tests unitarios del TenantContext mínimo de IAM."""

import pytest

from app.domain.iam.access import tenant_context as tenant_context_module
from app.domain.iam.access.tenant_context import (
    InactiveOrganizationError,
    InactiveUserError,
    TenantAccessDeniedError,
    TenantContext,
    build_tenant_context,
)


def test_company_admin_same_organization_builds_valid_context() -> None:
    context = build_tenant_context(
        actor_user_id=101,
        requested_organization_id=10,
        effective_organization_id=10,
        platform_role="USER",
        organization_role="COMPANY_ADMIN",
    )

    assert context == TenantContext(
        actor_user_id=101,
        requested_organization_id=10,
        effective_organization_id=10,
        platform_role="USER",
        organization_role="COMPANY_ADMIN",
        user_status="ACTIVE",
        organization_status="ACTIVE",
        is_platform_admin=False,
    )
    assert context.is_same_organization is True
    assert context.is_active_user is True
    assert context.is_active_organization is True


def test_platform_admin_cross_tenant_builds_valid_context() -> None:
    context = build_tenant_context(
        actor_user_id=1,
        requested_organization_id=20,
        effective_organization_id=10,
        platform_role="PLATFORM_ADMIN",
        organization_role="COMPANY_ADMIN",
    )

    assert context.is_platform_admin is True
    assert context.is_same_organization is False
    assert context.requested_organization_id == 20
    assert context.effective_organization_id == 10


def test_inactive_user_raises_controlled_error() -> None:
    with pytest.raises(InactiveUserError):
        build_tenant_context(
            actor_user_id=101,
            requested_organization_id=10,
            effective_organization_id=10,
            platform_role="USER",
            organization_role="COMPANY_ADMIN",
            user_status="DISABLED",
        )


def test_inactive_organization_raises_controlled_error() -> None:
    with pytest.raises(InactiveOrganizationError):
        build_tenant_context(
            actor_user_id=101,
            requested_organization_id=10,
            effective_organization_id=10,
            platform_role="USER",
            organization_role="COMPANY_ADMIN",
            organization_status="DISABLED",
        )


def test_non_platform_cross_tenant_raises_access_denied() -> None:
    with pytest.raises(TenantAccessDeniedError):
        build_tenant_context(
            actor_user_id=101,
            requested_organization_id=20,
            effective_organization_id=10,
            platform_role="USER",
            organization_role="COMPANY_ADMIN",
        )


def test_platform_admin_flag_cannot_escalate_without_platform_role() -> None:
    with pytest.raises(TenantAccessDeniedError):
        build_tenant_context(
            actor_user_id=101,
            requested_organization_id=20,
            effective_organization_id=10,
            platform_role="USER",
            organization_role="COMPANY_ADMIN",
            is_platform_admin=True,
        )


def test_tenant_context_module_does_not_import_fastapi_or_sqlalchemy() -> None:
    module_names = set(tenant_context_module.__dict__)

    assert "FastAPI" not in module_names
    assert "sqlalchemy" not in module_names
