from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.sql.schema import PrimaryKeyConstraint

from app.domain.iam.access.models import Status
from app.domain.iam.access.schemas import StatusCreate, StatusRead, StatusUpdate


def test_status_model_uses_expected_table_and_schema() -> None:
    assert Status.__tablename__ == "tbl_status"
    assert Status.__table__.schema == "sch_iam"


def test_status_model_has_exact_expected_columns() -> None:
    assert set(Status.__table__.columns.keys()) == {
        "id_status",
        "status",
        "create_at",
        "update_at",
    }


def test_status_id_is_big_integer_primary_key() -> None:
    id_column = Status.__table__.columns["id_status"]

    assert isinstance(id_column.type, BigInteger)
    assert id_column.primary_key is True


def test_status_primary_key_has_explicit_name() -> None:
    primary_key = Status.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_status"


def test_status_column_is_required_string_with_expected_length() -> None:
    status_column = Status.__table__.columns["status"]

    assert isinstance(status_column.type, String)
    assert status_column.type.length == 50
    assert status_column.nullable is False


def test_status_create_at_column_is_required_timezone_datetime_with_default() -> None:
    create_at_column = Status.__table__.columns["create_at"]

    assert isinstance(create_at_column.type, DateTime)
    assert create_at_column.type.timezone is True
    assert create_at_column.nullable is False
    assert create_at_column.server_default is not None


def test_status_update_at_column_is_nullable_timezone_datetime() -> None:
    update_at_column = Status.__table__.columns["update_at"]

    assert isinstance(update_at_column.type, DateTime)
    assert update_at_column.type.timezone is True
    assert update_at_column.nullable is True


def test_status_read_accepts_valid_data() -> None:
    created_at = datetime(2026, 10, 1, tzinfo=UTC)
    status = StatusRead(
        id_status=1,
        status="ACTIVE",
        created_at=created_at,
        updated_at=None,
    )

    assert status.id_status == 1
    assert status.status == "ACTIVE"
    assert status.created_at == created_at
    assert status.updated_at is None


def test_status_create_accepts_valid_data() -> None:
    status = StatusCreate(status="ACTIVE")

    assert status.status == "ACTIVE"


def test_status_update_allows_partial_update() -> None:
    status_update = StatusUpdate()

    assert status_update.status is None


def test_status_schemas_validate_status_length() -> None:
    too_long_status = "a" * 51

    with pytest.raises(ValidationError) as exc_info:
        StatusCreate(status=too_long_status)

    assert "status" in str(exc_info.value)


def test_status_migration_creates_only_tbl_status_without_seeds() -> None:
    migration_content = Path("alembic/versions/0003_create_tbl_status.py").read_text(
        encoding="utf-8"
    )

    assert "tbl_status" in migration_content
    assert 'schema="sch_iam"' in migration_content
    assert "pk_tbl_status" in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert "tbl_platform_role" not in migration_content
    assert "tbl_organization" not in migration_content
    assert "tbl_user" not in migration_content
    assert migration_content.count("op.create_table") == 1
