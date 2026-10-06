from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.sql.schema import PrimaryKeyConstraint

from app.domain.iam.access.models import PlatformRole, Status
from app.domain.iam.access.schemas import (
    PlatformRoleCreate,
    PlatformRoleRead,
    PlatformRoleUpdate,
)

pytestmark = pytest.mark.test_unit


def test_platform_role_model_uses_expected_table_and_schema() -> None:
    assert PlatformRole.__tablename__ == "tbl_platform_role"
    assert PlatformRole.__table__.schema == "sch_iam"


def test_platform_role_model_has_exact_expected_columns() -> None:
    assert set(PlatformRole.__table__.columns.keys()) == {
        "id_platform_role",
        "platform_role_type",
        "description",
        "create_at",
        "update_at",
    }


def test_platform_role_id_is_big_integer_primary_key() -> None:
    id_column = PlatformRole.__table__.columns["id_platform_role"]

    assert isinstance(id_column.type, BigInteger)
    assert id_column.primary_key is True


def test_platform_role_primary_key_has_explicit_name() -> None:
    primary_key = PlatformRole.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_platform_role"


def test_platform_role_type_is_required_string_with_expected_length() -> None:
    role_type_column = PlatformRole.__table__.columns["platform_role_type"]

    assert isinstance(role_type_column.type, String)
    assert role_type_column.type.length == 50
    assert role_type_column.nullable is False


def test_platform_role_description_is_nullable_text() -> None:
    description_column = PlatformRole.__table__.columns["description"]

    assert isinstance(description_column.type, Text)
    assert description_column.nullable is True


def test_platform_role_create_at_is_required_timezone_datetime_with_default() -> None:
    create_at_column = PlatformRole.__table__.columns["create_at"]

    assert isinstance(create_at_column.type, DateTime)
    assert create_at_column.type.timezone is True
    assert create_at_column.nullable is False
    assert create_at_column.server_default is not None


def test_platform_role_update_at_column_is_nullable_timezone_datetime() -> None:
    update_at_column = PlatformRole.__table__.columns["update_at"]

    assert isinstance(update_at_column.type, DateTime)
    assert update_at_column.type.timezone is True
    assert update_at_column.nullable is True


def test_platform_role_read_accepts_valid_data() -> None:
    created_at = datetime(2026, 10, 1, tzinfo=UTC)
    role = PlatformRoleRead(
        id_platform_role=1,
        platform_role_type="PLATFORM_ADMIN",
        description="Administra globalmente Project Guakamole.",
        created_at=created_at,
        updated_at=None,
    )

    assert role.id_platform_role == 1
    assert role.platform_role_type == "PLATFORM_ADMIN"
    assert role.description == "Administra globalmente Project Guakamole."
    assert role.created_at == created_at
    assert role.updated_at is None


def test_platform_role_create_accepts_valid_data() -> None:
    role = PlatformRoleCreate(
        platform_role_type="PLATFORM_ADMIN",
        description=None,
    )

    assert role.platform_role_type == "PLATFORM_ADMIN"
    assert role.description is None


def test_platform_role_update_allows_partial_update() -> None:
    role_update = PlatformRoleUpdate()

    assert role_update.platform_role_type is None
    assert role_update.description is None


def test_platform_role_schemas_validate_role_type_length() -> None:
    too_long_role_type = "a" * 51

    with pytest.raises(ValidationError) as exc_info:
        PlatformRoleCreate(platform_role_type=too_long_role_type)

    assert "platform_role_type" in str(exc_info.value)


def test_platform_role_migration_creates_only_tbl_platform_role_without_seeds() -> None:
    migration_content = Path(
        "alembic/versions/0004_create_tbl_platform_role.py"
    ).read_text(encoding="utf-8")

    assert "tbl_platform_role" in migration_content
    assert 'schema="sch_iam"' in migration_content
    assert "pk_tbl_platform_role" in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert "tbl_organization_role" not in migration_content
    assert "tbl_organization" not in migration_content
    assert "tbl_user" not in migration_content
    assert migration_content.count("op.create_table") == 1


def test_status_model_still_exists() -> None:
    assert Status.__tablename__ == "tbl_status"
