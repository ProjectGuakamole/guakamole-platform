from datetime import UTC, date, datetime
from pathlib import Path
from typing import TypedDict, cast

import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, Date, DateTime, String
from sqlalchemy.sql.schema import (
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    Table,
    UniqueConstraint,
)
from sqlalchemy.sql.type_api import TypeEngine

from app.domain.iam.users.models import User
from app.domain.iam.users.schemas import UserCreate, UserRead, UserUpdate

pytestmark = pytest.mark.test_unit

EXPECTED_COLUMNS = {
    "id_user",
    "id_organization",
    "id_platform_role",
    "id_country",
    "id_state",
    "id_city",
    "id_org_role",
    "id_status",
    "email",
    "password_hash",
    "first_name",
    "last_name",
    "birthdate",
    "user_address",
    "user_zipcode",
    "create_at",
    "update_at",
    "last_login_at",
}

HASH_SAMPLE = "argon2id-test-hash"
HASH_UPDATED = "argon2id-updated-test-hash"


class UserPayload(TypedDict):
    id_organization: int
    id_platform_role: int
    id_country: int
    id_state: int
    id_city: int
    id_org_role: int
    id_status: int
    email: str
    first_name: str
    last_name: str
    birthdate: date
    user_address: str
    user_zipcode: str


def valid_user_payload() -> UserPayload:
    return {
        "id_organization": 1,
        "id_platform_role": 2,
        "id_country": 3,
        "id_state": 4,
        "id_city": 5,
        "id_org_role": 6,
        "id_status": 7,
        "email": "ana@example.test",
        "first_name": "Ana",
        "last_name": "García",
        "birthdate": date(1990, 1, 1),
        "user_address": "Calle Mayor 1",
        "user_zipcode": "08001",
    }


def test_user_model_uses_expected_table_and_schema() -> None:
    assert User.__tablename__ == "tbl_users"
    assert User.__table__.schema == "sch_iam"


def test_user_model_has_exact_expected_columns() -> None:
    assert set(User.__table__.columns.keys()) == EXPECTED_COLUMNS


@pytest.mark.parametrize(
    ("column_name", "expected_type", "nullable", "length"),
    [
        ("id_user", BigInteger, False, None),
        ("id_organization", BigInteger, False, None),
        ("id_platform_role", BigInteger, False, None),
        ("id_country", BigInteger, False, None),
        ("id_state", BigInteger, False, None),
        ("id_city", BigInteger, False, None),
        ("id_org_role", BigInteger, False, None),
        ("id_status", BigInteger, False, None),
        ("email", String, False, 254),
        ("password_hash", String, False, 255),
        ("first_name", String, False, 100),
        ("last_name", String, False, 150),
        ("birthdate", Date, False, None),
        ("user_address", String, False, 255),
        ("user_zipcode", String, False, 20),
        ("create_at", DateTime, False, None),
        ("update_at", DateTime, True, None),
        ("last_login_at", DateTime, True, None),
    ],
)
def test_user_columns_have_expected_types_and_nullability(
    column_name: str,
    expected_type: type[TypeEngine[object]],
    nullable: bool,
    length: int | None,
) -> None:
    column = User.__table__.columns[column_name]

    assert isinstance(column.type, expected_type)
    assert column.nullable is nullable
    if length is not None:
        string_type = cast(String, column.type)
        assert string_type.length == length


def test_user_primary_key_has_explicit_name() -> None:
    primary_key = User.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_users"


def test_user_foreign_keys_have_expected_targets_and_policies() -> None:
    table = cast(Table, User.__table__)
    foreign_keys = {
        constraint.name: constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    expected_targets = {
        "fk_tbl_users_id_organization": "sch_iam.tbl_organization.id_organization",
        "fk_tbl_users_id_platform_role": "sch_iam.tbl_platform_role.id_platform_role",
        "fk_tbl_users_id_country": "sch_iam.tbl_country.id_country",
        "fk_tbl_users_id_state": "sch_iam.tbl_state.id_state",
        "fk_tbl_users_id_city": "sch_iam.tbl_city.id_city",
        "fk_tbl_users_id_org_role": "sch_iam.tbl_organization_role.id_org_role",
        "fk_tbl_users_id_status": "sch_iam.tbl_status.id_status",
    }

    assert set(foreign_keys) == set(expected_targets)
    for name, target in expected_targets.items():
        foreign_key = foreign_keys[name]
        assert foreign_key.ondelete == "RESTRICT"
        assert foreign_key.onupdate == "CASCADE"
        assert [element.target_fullname for element in foreign_key.elements] == [target]


def test_user_unique_email_constraint_has_explicit_name() -> None:
    table = cast(Table, User.__table__)
    unique_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert unique_names == {"uq_tbl_users_email"}


def test_user_has_foreign_key_indexes() -> None:
    table = cast(Table, User.__table__)
    indexes = {
        index.name: [column.name for column in index.columns] for index in table.indexes
    }

    assert indexes == {
        "ix_tbl_users_id_organization": ["id_organization"],
        "ix_tbl_users_id_platform_role": ["id_platform_role"],
        "ix_tbl_users_id_country": ["id_country"],
        "ix_tbl_users_id_state": ["id_state"],
        "ix_tbl_users_id_city": ["id_city"],
        "ix_tbl_users_id_org_role": ["id_org_role"],
        "ix_tbl_users_id_status": ["id_status"],
    }


def test_user_timestamps_and_last_login_are_timezone_aware() -> None:
    created_at = User.__table__.columns["create_at"]
    updated_at = User.__table__.columns["update_at"]
    last_login_at = User.__table__.columns["last_login_at"]

    assert isinstance(created_at.type, DateTime)
    assert created_at.type.timezone is True
    assert created_at.server_default is not None
    assert isinstance(updated_at.type, DateTime)
    assert updated_at.type.timezone is True
    assert updated_at.nullable is True
    assert isinstance(last_login_at.type, DateTime)
    assert last_login_at.type.timezone is True
    assert last_login_at.nullable is True


def test_user_create_accepts_valid_data_with_password_hash() -> None:
    user = UserCreate(password_hash=HASH_SAMPLE, **valid_user_payload())

    assert user.email == "ana@example.test"
    assert user.password_hash == HASH_SAMPLE


def test_user_update_allows_partial_update_with_optional_password_hash() -> None:
    user_update = UserUpdate(
        first_name="Ana María",
        password_hash=HASH_UPDATED,
    )

    assert user_update.first_name == "Ana María"
    assert user_update.password_hash == HASH_UPDATED
    assert user_update.email is None


def test_user_read_does_not_expose_password_hash() -> None:
    now = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    user = UserRead(
        id_user=10,
        created_at=now,
        updated_at=None,
        last_login_at=now,
        **valid_user_payload(),
    )

    assert "password_hash" not in user.model_dump()
    assert not hasattr(user, "password_hash")


@pytest.mark.parametrize(
    ("field_name", "max_length", "schema_name"),
    [
        ("email", 254, "create"),
        ("password_hash", 255, "create"),
        ("first_name", 100, "create"),
        ("last_name", 150, "create"),
        ("user_address", 255, "create"),
        ("user_zipcode", 20, "create"),
        ("password_hash", 255, "update"),
    ],
)
def test_user_schemas_validate_lengths(
    field_name: str, max_length: int, schema_name: str
) -> None:
    payload: dict[str, object] = dict(valid_user_payload())
    payload["password_hash"] = HASH_SAMPLE
    payload[field_name] = "a" * (max_length + 1)
    schema = UserCreate if schema_name == "create" else UserUpdate

    with pytest.raises(ValidationError) as exc_info:
        schema.model_validate(payload)

    assert field_name in str(exc_info.value)


def test_user_migration_creates_only_tbl_users_without_seeds() -> None:
    migration_content = Path("alembic/versions/0009_create_tbl_users.py").read_text(
        encoding="utf-8"
    )

    assert "tbl_users" in migration_content
    assert 'schema="sch_iam"' in migration_content
    assert 'down_revision: str | None = "0008_create_tbl_organization"' in (
        migration_content
    )
    for expected_fragment in (
        "pk_tbl_users",
        "fk_tbl_users_id_organization",
        "fk_tbl_users_id_platform_role",
        "fk_tbl_users_id_country",
        "fk_tbl_users_id_state",
        "fk_tbl_users_id_city",
        "fk_tbl_users_id_org_role",
        "fk_tbl_users_id_status",
        "uq_tbl_users_email",
        "ix_tbl_users_id_organization",
        "ix_tbl_users_id_platform_role",
        "ix_tbl_users_id_country",
        "ix_tbl_users_id_state",
        "ix_tbl_users_id_city",
        "ix_tbl_users_id_org_role",
        "ix_tbl_users_id_status",
        "sch_iam.tbl_organization.id_organization",
        "sch_iam.tbl_platform_role.id_platform_role",
        "sch_iam.tbl_country.id_country",
        "sch_iam.tbl_state.id_state",
        "sch_iam.tbl_city.id_city",
        "sch_iam.tbl_organization_role.id_org_role",
        "sch_iam.tbl_status.id_status",
        'ondelete="RESTRICT"',
        'onupdate="CASCADE"',
    ):
        assert expected_fragment in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert migration_content.count("op.create_table") == 1
    assert 'op.create_table(\n        "tbl_department"' not in migration_content
    department_relations_create_table = (
        'op.create_table(\n        "tbl_department_relations"'
    )
    assert department_relations_create_table not in migration_content
