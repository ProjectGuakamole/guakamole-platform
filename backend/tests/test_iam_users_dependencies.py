import ast
from inspect import signature
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.domain.iam.access.tenant_context import TenantContext
from app.domain.iam.users.dependencies import (
    PilotAuthenticatedUser,
    get_list_organization_users_service,
    get_pilot_authenticated_user,
    get_tenant_context,
    get_user_list_query,
)
from app.domain.iam.users.repositories import SqlAlchemyOrganizationUsersRepository
from app.domain.iam.users.schemas import UserListQuery
from app.domain.iam.users.services import ListOrganizationUsersService


def test_user_list_query_dependency_creates_defaults() -> None:
    query = get_user_list_query()

    assert query == UserListQuery()


def test_user_list_query_dependency_respects_valid_values() -> None:
    query = get_user_list_query(
        limit=25,
        offset=10,
        search="  ana  ",
        sort_by="last_name",
        sort_dir="desc",
    )

    assert query.limit == 25
    assert query.offset == 10
    assert query.search == "ana"
    assert query.sort_by == "last_name"
    assert query.sort_dir == "desc"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("limit", 0),
        ("limit", 101),
        ("offset", -1),
        ("search", "x" * 101),
        ("sort_by", "password_hash"),
        ("sort_dir", "drop table"),
    ],
)
def test_user_list_query_dependency_propagates_pydantic_validation(
    field: str,
    value: object,
) -> None:
    payload: dict[str, object] = {field: value}

    with pytest.raises(ValidationError):
        UserListQuery.model_validate(payload)


def test_service_dependency_returns_service_with_sqlalchemy_repository() -> None:
    session = Session()

    service = get_list_organization_users_service(session=session)

    assert isinstance(service, ListOrganizationUsersService)
    assert isinstance(service._repository, SqlAlchemyOrganizationUsersRepository)


def test_pilot_authenticated_user_dependency_is_explicitly_provisional() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_pilot_authenticated_user()

    assert exc_info.value.status_code == 501


def test_tenant_context_dependency_uses_path_organization_and_actor() -> None:
    actor = PilotAuthenticatedUser(
        user_id=42,
        organization_id=7,
        platform_role="USER",
        organization_role="COMPANY_ADMIN",
    )

    context = get_tenant_context(organization_id=7, actor=actor)

    assert isinstance(context, TenantContext)
    assert context.actor_user_id == 42
    assert context.requested_organization_id == 7
    assert context.effective_organization_id == 7


def test_tenant_context_dependency_rejects_cross_tenant_non_platform() -> None:
    actor = PilotAuthenticatedUser(
        user_id=42,
        organization_id=7,
        platform_role="USER",
        organization_role="COMPANY_ADMIN",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_tenant_context(organization_id=8, actor=actor)

    assert exc_info.value.status_code == 403


def test_tenant_context_dependency_does_not_accept_query_or_body_org_id() -> None:
    dependency_signature = signature(get_tenant_context)

    assert tuple(dependency_signature.parameters) == ("organization_id", "actor")


def test_fastapi_imports_remain_limited_to_dependencies_module() -> None:
    users_module = Path(__file__).resolve().parents[1] / "app/domain/iam/users"
    modules_without_fastapi = ("services.py", "policies.py", "repositories.py")

    for module_name in modules_without_fastapi:
        tree = ast.parse((users_module / module_name).read_text(encoding="utf-8"))
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

        assert "fastapi" not in imported_modules
        assert "fastapi" not in direct_imports


def test_dependencies_do_not_contain_secret_literals() -> None:
    dependencies_path = (
        Path(__file__).resolve().parents[1] / "app/domain/iam/users/dependencies.py"
    )
    source = dependencies_path.read_text(encoding="utf-8").lower()

    assert "password=" not in source
    assert "secret" not in source
