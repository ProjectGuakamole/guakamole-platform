"""Tests de auditoría mínima para el listado IAM/users."""

from collections.abc import MutableMapping
from datetime import UTC, datetime
from typing import cast

import pytest

from app.domain.iam.access.tenant_context import (
    PLATFORM_ADMIN_ROLE,
    TenantAccessDeniedError,
    TenantContext,
    build_tenant_context,
)
from app.domain.iam.users.schemas import (
    OrganizationUserListResponse,
    OrganizationUserRead,
    UserListQuery,
)
from app.domain.iam.users.services import (
    IAM_ORGANIZATION_USERS_LISTED,
    AuditEvent,
    AuditMetadataValue,
    ListOrganizationUsersService,
)


class FakeAuditLogger:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def emit(self, event: AuditEvent) -> None:
        self.events.append(event)


class FakePolicy:
    def __init__(self, *, allowed: bool) -> None:
        self._allowed = allowed

    def ensure_allowed(self, context: TenantContext) -> None:
        _ = context
        if not self._allowed:
            raise TenantAccessDeniedError("Listado de usuarios denegado.")


class FakeOrganizationUsersRepository:
    def __init__(self, *, response: OrganizationUserListResponse) -> None:
        self._response = response
        self.called = False

    def list_by_organization(
        self,
        *,
        organization_id: int,
        query: UserListQuery,
    ) -> OrganizationUserListResponse:
        _ = organization_id
        _ = query
        self.called = True
        return self._response


def test_audit_event_emitted_for_allowed_same_org_list() -> None:
    audit_logger = FakeAuditLogger()
    service = make_service(audit_logger=audit_logger)
    context = make_context(requested_organization_id=10, effective_organization_id=10)

    service.list_users(context=context, query=UserListQuery(limit=25, offset=5))

    assert len(audit_logger.events) == 1
    event = audit_logger.events[0]
    assert event.action == IAM_ORGANIZATION_USERS_LISTED
    assert event.metadata["actor_user_id"] == 1
    assert event.metadata["requested_organization_id"] == 10
    assert event.metadata["effective_organization_id"] == 10
    assert event.metadata["cross_tenant"] is False
    assert event.metadata["result_count"] == 1
    assert event.metadata["limit"] == 25
    assert event.metadata["offset"] == 5


def test_audit_event_marks_platform_admin_cross_tenant_access() -> None:
    audit_logger = FakeAuditLogger()
    service = make_service(audit_logger=audit_logger)
    context = make_context(
        requested_organization_id=20,
        effective_organization_id=10,
        platform_role=PLATFORM_ADMIN_ROLE,
        organization_role="COMPANY_ADMIN",
    )

    service.list_users(context=context, query=UserListQuery(search="ana"))

    event = audit_logger.events[0]
    assert event.metadata["actor_platform_role"] == PLATFORM_ADMIN_ROLE
    assert event.metadata["actor_organization_role"] == "COMPANY_ADMIN"
    assert event.metadata["requested_organization_id"] == 20
    assert event.metadata["effective_organization_id"] == 10
    assert event.metadata["cross_tenant"] is True
    assert event.metadata["search_present"] is True


def test_audit_success_event_not_emitted_when_policy_denies() -> None:
    audit_logger = FakeAuditLogger()
    repository = FakeOrganizationUsersRepository(response=make_response())
    service = ListOrganizationUsersService(
        repository=repository,
        policy=FakePolicy(allowed=False),
        audit_logger=audit_logger,
    )

    with pytest.raises(TenantAccessDeniedError):
        service.list_users(context=make_context(), query=UserListQuery())

    assert audit_logger.events == []
    assert not repository.called


def test_audit_metadata_does_not_contain_sensitive_or_personal_payload() -> None:
    audit_logger = FakeAuditLogger()
    service = make_service(audit_logger=audit_logger)

    service.list_users(context=make_context(), query=UserListQuery(search="Ana García"))

    event = audit_logger.events[0]
    serialized_keys = " ".join(event.metadata.keys()).lower()
    serialized_values = " ".join(
        str(value).lower() for value in event.metadata.values()
    )
    serialized_metadata = f"{serialized_keys} {serialized_values}"

    forbidden_fragments = [
        "password_hash",
        "token",
        "secret",
        "ana.garcia@example.test",
        "ana garcía",
        "garcía",
        "response",
        "items",
        "select ",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in serialized_metadata

    assert event.metadata["search_present"] is True


def test_audit_metadata_is_immutable_after_event_creation() -> None:
    audit_logger = FakeAuditLogger()
    service = make_service(audit_logger=audit_logger)

    service.list_users(context=make_context(), query=UserListQuery())

    event = audit_logger.events[0]
    mutable_metadata = cast(
        MutableMapping[str, AuditMetadataValue],
        event.metadata,
    )
    with pytest.raises(TypeError):
        mutable_metadata["actor_user_id"] = 999

    assert event.metadata["actor_user_id"] == 1


def test_service_uses_noop_audit_logger_by_default() -> None:
    service = ListOrganizationUsersService(
        repository=FakeOrganizationUsersRepository(response=make_response()),
        policy=FakePolicy(allowed=True),
    )

    result = service.list_users(context=make_context(), query=UserListQuery())

    assert result.total == 1


def make_service(*, audit_logger: FakeAuditLogger) -> ListOrganizationUsersService:
    return ListOrganizationUsersService(
        repository=FakeOrganizationUsersRepository(response=make_response()),
        policy=FakePolicy(allowed=True),
        audit_logger=audit_logger,
    )


def make_context(
    *,
    requested_organization_id: int = 10,
    effective_organization_id: int = 10,
    platform_role: str = "USER",
    organization_role: str = "COMPANY_ADMIN",
) -> TenantContext:
    return build_tenant_context(
        actor_user_id=1,
        requested_organization_id=requested_organization_id,
        effective_organization_id=effective_organization_id,
        platform_role=platform_role,
        organization_role=organization_role,
    )


def make_response() -> OrganizationUserListResponse:
    return OrganizationUserListResponse(
        items=[
            OrganizationUserRead(
                id_user=100,
                id_organization=10,
                email="ana.garcia@example.test",
                first_name="Ana",
                last_name="García",
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
