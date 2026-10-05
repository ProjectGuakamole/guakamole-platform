from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.iam.users.schemas import (
    OrganizationUserListResponse,
    OrganizationUserRead,
    UserListQuery,
)


def valid_organization_user_payload() -> dict[str, object]:
    now = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
    return {
        "id_user": 10,
        "id_organization": 20,
        "email": "ana@example.test",
        "first_name": "Ana",
        "last_name": "García",
        "id_status": 1,
        "id_platform_role": 2,
        "id_org_role": 3,
        "created_at": now,
        "updated_at": None,
        "last_login_at": now,
    }


@dataclass(frozen=True)
class OrganizationUserOrmStub:
    id_user: int
    id_organization: int
    email: str
    first_name: str
    last_name: str
    id_status: int
    id_platform_role: int
    id_org_role: int
    created_at: datetime
    updated_at: datetime | None
    last_login_at: datetime | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "password_hash", str(self.id_user))


def test_user_list_query_uses_safe_defaults() -> None:
    query = UserListQuery()

    assert query.limit == 50
    assert query.offset == 0
    assert query.search is None
    assert query.sort_by == "email"
    assert query.sort_dir == "asc"


@pytest.mark.parametrize("limit", [1, 100])
def test_user_list_query_accepts_limit_boundaries(limit: int) -> None:
    assert UserListQuery(limit=limit).limit == limit


def test_user_list_query_accepts_offset_zero() -> None:
    assert UserListQuery(offset=0).offset == 0


@pytest.mark.parametrize(
    "sort_by",
    ["email", "first_name", "last_name", "create_at", "last_login_at", "id_user"],
)
def test_user_list_query_accepts_allowed_sort_fields(sort_by: str) -> None:
    assert UserListQuery.model_validate({"sort_by": sort_by}).sort_by == sort_by


@pytest.mark.parametrize("sort_dir", ["asc", "desc"])
def test_user_list_query_accepts_allowed_sort_directions(sort_dir: str) -> None:
    assert UserListQuery.model_validate({"sort_dir": sort_dir}).sort_dir == sort_dir


def test_user_list_query_trims_search() -> None:
    query = UserListQuery(search="  ana@example.test  ")

    assert query.search == "ana@example.test"


def test_organization_user_read_serializes_allowed_fields_only() -> None:
    user = OrganizationUserRead.model_validate(
        {**valid_organization_user_payload(), "password_hash": "not-exposed"}
    )

    serialized = user.model_dump()

    assert serialized == valid_organization_user_payload()
    assert "password_hash" not in serialized


def test_organization_user_read_validates_from_attributes_orm_like_object() -> None:
    now = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
    updated_at = datetime(2026, 10, 5, 13, 0, tzinfo=UTC)
    orm_user = OrganizationUserOrmStub(
        id_user=10,
        id_organization=20,
        email="ana@example.test",
        first_name="Ana",
        last_name="García",
        id_status=1,
        id_platform_role=2,
        id_org_role=3,
        created_at=now,
        updated_at=updated_at,
        last_login_at=now,
    )

    user = OrganizationUserRead.model_validate(orm_user)
    serialized = user.model_dump()

    assert serialized["created_at"] == now
    assert serialized["updated_at"] == updated_at
    assert "password_hash" not in serialized


def test_organization_user_list_response_serializes_items_and_pagination() -> None:
    item = OrganizationUserRead.model_validate(valid_organization_user_payload())
    response = OrganizationUserListResponse(
        items=[item],
        limit=50,
        offset=0,
        total=1,
    )

    serialized = response.model_dump()

    assert serialized["items"] == [valid_organization_user_payload()]
    assert serialized["limit"] == 50
    assert serialized["offset"] == 0
    assert serialized["total"] == 1


@pytest.mark.parametrize("limit", [0, 101])
def test_user_list_query_rejects_invalid_limits(limit: int) -> None:
    with pytest.raises(ValidationError):
        UserListQuery(limit=limit)


def test_user_list_query_rejects_negative_offset() -> None:
    with pytest.raises(ValidationError):
        UserListQuery(offset=-1)


@pytest.mark.parametrize("sort_by", ["password_hash", "arbitrary_column"])
def test_user_list_query_rejects_unsafe_sort_fields(sort_by: str) -> None:
    with pytest.raises(ValidationError):
        UserListQuery.model_validate({"sort_by": sort_by})


def test_user_list_query_rejects_unsafe_sort_direction() -> None:
    with pytest.raises(ValidationError):
        UserListQuery.model_validate({"sort_dir": "drop table"})


def test_user_list_query_rejects_too_long_search() -> None:
    with pytest.raises(ValidationError):
        UserListQuery(search="a" * 101)


def test_organization_user_read_model_fields_do_not_include_password_hash() -> None:
    assert "password_hash" not in OrganizationUserRead.model_fields


def test_user_list_query_rejects_extra_sensitive_field() -> None:
    with pytest.raises(ValidationError):
        UserListQuery.model_validate({"password_hash": "not-allowed"})
