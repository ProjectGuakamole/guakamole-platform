"""Tests unitarios del service para listar usuarios de organización."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain.iam.access.tenant_context import (
    TenantAccessDeniedError,
    TenantContext,
    build_tenant_context,
)
from app.domain.iam.users.schemas import (
    OrganizationUserListResponse,
    OrganizationUserRead,
    UserListQuery,
)
from app.domain.iam.users.services import ListOrganizationUsersService


class FakePolicy:
    def __init__(self, *, allowed: bool, calls: list[str] | None = None) -> None:
        self._allowed = allowed
        self._calls = calls
        self.called = False

    def ensure_allowed(self, context: TenantContext) -> None:
        _ = context
        self.called = True
        if self._calls is not None:
            self._calls.append("policy")
        if not self._allowed:
            raise TenantAccessDeniedError("Listado de usuarios denegado.")


class FakeOrganizationUsersRepository:
    def __init__(
        self,
        *,
        response: OrganizationUserListResponse,
        calls: list[str] | None = None,
    ) -> None:
        self._response = response
        self._calls = calls
        self.called = False
        self.received_organization_id: int | None = None
        self.received_query: UserListQuery | None = None

    def list_by_organization(
        self,
        *,
        organization_id: int,
        query: UserListQuery,
    ) -> OrganizationUserListResponse:
        if self._calls is not None and "policy" not in self._calls:
            raise AssertionError("Repository ejecutado antes que policy.")
        self.called = True
        self.received_organization_id = organization_id
        self.received_query = query
        if self._calls is not None:
            self._calls.append("repository")
        return self._response


def test_service_allowed_returns_repository_response() -> None:
    response = make_response()
    policy = FakePolicy(allowed=True)
    repository = FakeOrganizationUsersRepository(response=response)
    service = ListOrganizationUsersService(repository=repository, policy=policy)
    context = make_context(requested_organization_id=20)
    query = UserListQuery(limit=10)

    result = service.list_users(context=context, query=query)

    assert result == response
    assert policy.called
    assert repository.called


def test_service_uses_requested_organization_id_for_repository() -> None:
    response = make_response()
    repository = FakeOrganizationUsersRepository(response=response)
    service = ListOrganizationUsersService(
        repository=repository,
        policy=FakePolicy(allowed=True),
    )
    context = make_context(requested_organization_id=42)
    query = UserListQuery(offset=5)

    service.list_users(context=context, query=query)

    assert repository.received_organization_id == 42
    assert repository.received_query == query


def test_service_propagates_controlled_error_when_policy_denies() -> None:
    repository = FakeOrganizationUsersRepository(response=make_response())
    service = ListOrganizationUsersService(
        repository=repository,
        policy=FakePolicy(allowed=False),
    )

    with pytest.raises(TenantAccessDeniedError):
        service.list_users(context=make_context(), query=UserListQuery())


def test_service_does_not_call_repository_when_policy_denies() -> None:
    repository = FakeOrganizationUsersRepository(response=make_response())
    service = ListOrganizationUsersService(
        repository=repository,
        policy=FakePolicy(allowed=False),
    )

    with pytest.raises(TenantAccessDeniedError):
        service.list_users(context=make_context(), query=UserListQuery())

    assert not repository.called


def test_service_calls_policy_before_repository() -> None:
    calls: list[str] = []
    repository = FakeOrganizationUsersRepository(response=make_response(), calls=calls)
    service = ListOrganizationUsersService(
        repository=repository,
        policy=FakePolicy(allowed=True, calls=calls),
    )

    service.list_users(context=make_context(), query=UserListQuery())

    assert calls == ["policy", "repository"]


def test_service_response_does_not_expose_sensitive_fields() -> None:
    service = ListOrganizationUsersService(
        repository=FakeOrganizationUsersRepository(response=make_response()),
        policy=FakePolicy(allowed=True),
    )

    result = service.list_users(context=make_context(), query=UserListQuery())

    dumped_user = result.items[0].model_dump()
    assert "password_hash" not in dumped_user
    assert not hasattr(result.items[0], "password_hash")


def test_service_does_not_import_fastapi_or_sqlalchemy() -> None:
    service_source = Path("app/domain/iam/users/services.py").read_text(
        encoding="utf-8"
    )

    assert "fastapi" not in service_source.lower()
    assert "sqlalchemy" not in service_source.lower()


def make_context(*, requested_organization_id: int = 10) -> TenantContext:
    return build_tenant_context(
        actor_user_id=1,
        requested_organization_id=requested_organization_id,
        effective_organization_id=requested_organization_id,
        platform_role="USER",
        organization_role="COMPANY_ADMIN",
    )


def make_response() -> OrganizationUserListResponse:
    return OrganizationUserListResponse(
        items=[
            OrganizationUserRead(
                id_user=100,
                id_organization=10,
                email="ana.service@example.test",
                first_name="Ana",
                last_name="Servicio",
                id_status=1,
                id_platform_role=2,
                id_org_role=3,
                created_at=datetime(2026, 10, 1, 9, 0, tzinfo=UTC),
                updated_at=None,
                last_login_at=None,
            )
        ],
        limit=50,
        offset=0,
        total=1,
    )
