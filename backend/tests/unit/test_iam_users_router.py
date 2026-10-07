import ast
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain.iam.access.tenant_context import TenantContext
from app.domain.iam.users.dependencies import (
    PilotAuthenticatedUser,
    get_list_organization_users_service,
    get_pilot_authenticated_user,
)
from app.domain.iam.users.schemas import (
    OrganizationUserListResponse,
    OrganizationUserRead,
    UserListQuery,
)
from app.main import app

pytestmark = pytest.mark.test_unit


class FakeListOrganizationUsersService:
    def __init__(self, *, allowed: bool = True) -> None:
        self._allowed = allowed
        self.received_organization_id: int | None = None
        self.received_query: UserListQuery | None = None

    def list_users(
        self,
        *,
        context: TenantContext,
        query: UserListQuery,
    ) -> OrganizationUserListResponse:
        requested_id = context.requested_organization_id
        self.received_organization_id = requested_id
        self.received_query = query
        return make_response(
            organization_id=requested_id,
            limit=query.limit,
            offset=query.offset,
        )


def test_openapi_includes_iam_users_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert (
        "/api/v1/iam/organizations/{organization_id}/users" in response.json()["paths"]
    )


def test_endpoint_without_auth_override_returns_provisional_501() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/iam/organizations/1/users")

    assert response.status_code == 501


def test_endpoint_allowed_returns_users_and_uses_path_organization() -> None:
    fake_service = FakeListOrganizationUsersService()
    app.dependency_overrides[get_pilot_authenticated_user] = lambda: make_actor(
        organization_id=7
    )
    app.dependency_overrides[get_list_organization_users_service] = lambda: fake_service
    client = TestClient(app)

    try:
        response = client.get("/api/v1/iam/organizations/7/users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert payload["total"] == 1
    assert payload["items"][0]["id_organization"] == 7
    assert fake_service.received_organization_id == 7


def test_endpoint_passes_normalized_query_params_to_service() -> None:
    fake_service = FakeListOrganizationUsersService()
    app.dependency_overrides[get_pilot_authenticated_user] = lambda: make_actor(
        organization_id=9
    )
    app.dependency_overrides[get_list_organization_users_service] = lambda: fake_service
    client = TestClient(app)

    try:
        response = client.get(
            "/api/v1/iam/organizations/9/users",
            params={
                "limit": 25,
                "offset": 5,
                "search": "  ana  ",
                "sort_by": "last_name",
                "sort_dir": "desc",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert fake_service.received_query == UserListQuery(
        limit=25,
        offset=5,
        search="ana",
        sort_by="last_name",
        sort_dir="desc",
    )


def test_endpoint_cross_tenant_denied_returns_403() -> None:
    app.dependency_overrides[get_pilot_authenticated_user] = lambda: make_actor(
        organization_id=7
    )
    app.dependency_overrides[get_list_organization_users_service] = lambda: (
        FakeListOrganizationUsersService()
    )
    client = TestClient(app)

    try:
        response = client.get("/api/v1/iam/organizations/8/users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.parametrize(
    "url",
    [
        "/api/v1/iam/organizations/1/users?limit=0",
        "/api/v1/iam/organizations/1/users?sort_by=password_hash",
        "/api/v1/iam/organizations/0/users",
    ],
)
def test_endpoint_invalid_request_returns_422(url: str) -> None:
    app.dependency_overrides[get_pilot_authenticated_user] = lambda: make_actor(
        organization_id=1
    )
    app.dependency_overrides[get_list_organization_users_service] = lambda: (
        FakeListOrganizationUsersService()
    )
    client = TestClient(app)

    try:
        response = client.get(url)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_endpoint_response_does_not_expose_password_hash() -> None:
    app.dependency_overrides[get_pilot_authenticated_user] = lambda: make_actor(
        organization_id=3
    )
    app.dependency_overrides[get_list_organization_users_service] = lambda: (
        FakeListOrganizationUsersService()
    )
    client = TestClient(app)

    try:
        response = client.get("/api/v1/iam/organizations/3/users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "password_hash" not in response.text


def test_router_does_not_import_sqlalchemy_or_repository_directly() -> None:
    router_path = Path("app/domain/iam/users/routers.py")
    tree = ast.parse(router_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    direct_imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    assert "sqlalchemy" not in direct_imports
    assert not any(module.startswith("sqlalchemy") for module in imported_modules)
    assert "app.domain.iam.users.repositories" not in imported_modules


def make_actor(*, organization_id: int) -> PilotAuthenticatedUser:
    return PilotAuthenticatedUser(
        user_id=42,
        organization_id=organization_id,
        platform_role="USER",
        organization_role="COMPANY_ADMIN",
    )


def make_response(
    *,
    organization_id: int,
    limit: int,
    offset: int,
) -> OrganizationUserListResponse:
    return OrganizationUserListResponse(
        items=[
            OrganizationUserRead(
                id_user=100,
                id_organization=organization_id,
                email="ana.router@example.test",
                first_name="Ana",
                last_name="Router",
                id_status=1,
                id_platform_role=2,
                id_org_role=3,
                created_at=datetime(2026, 10, 1, 9, 0, tzinfo=UTC),
                updated_at=None,
                last_login_at=None,
            )
        ],
        limit=limit,
        offset=offset,
        total=1,
    )
