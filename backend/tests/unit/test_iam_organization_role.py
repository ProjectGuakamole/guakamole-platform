from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.sql.schema import PrimaryKeyConstraint

from app.domain.iam.access.models import OrganizationRole, PlatformRole, Status
from app.domain.iam.access.schemas import (
    OrganizationRoleCreate,
    OrganizationRoleRead,
    OrganizationRoleUpdate,
)

pytestmark = pytest.mark.test_unit


def test_organization_role_model_uses_expected_table_and_schema() -> None:
    assert OrganizationRole.__tablename__ == "tbl_organization_role"
    assert OrganizationRole.__table__.schema == "sch_iam"


def test_organization_role_model_has_exact_expected_columns() -> None:
    assert set(OrganizationRole.__table__.columns.keys()) == {
        "id_org_role",
        "org_role_type",
        "create_at",
        "update_at",
    }


def test_organization_role_id_is_big_integer_primary_key() -> None:
    id_column = OrganizationRole.__table__.columns["id_org_role"]

    assert isinstance(id_column.type, BigInteger)
    assert id_column.primary_key is True


def test_organization_role_primary_key_has_explicit_name() -> None:
    primary_key = OrganizationRole.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_organization_role"


def test_organization_role_type_is_required_string_with_expected_length() -> None:
    role_type_column = OrganizationRole.__table__.columns["org_role_type"]

    assert isinstance(role_type_column.type, String)
    assert role_type_column.type.length == 50
    assert role_type_column.nullable is False


def test_organization_role_create_at_is_required_datetime_with_default() -> None:
    create_at_column = OrganizationRole.__table__.columns["create_at"]

    assert isinstance(create_at_column.type, DateTime)
    assert create_at_column.type.timezone is True
    assert create_at_column.nullable is False
    assert create_at_column.server_default is not None


def test_organization_role_update_at_column_is_nullable_timezone_datetime() -> None:
    update_at_column = OrganizationRole.__table__.columns["update_at"]

    assert isinstance(update_at_column.type, DateTime)
    assert update_at_column.type.timezone is True
    assert update_at_column.nullable is True


def test_organization_role_read_accepts_valid_data() -> None:
    created_at = datetime(2026, 10, 1, tzinfo=UTC)
    role = OrganizationRoleRead(
        id_org_role=1,
        org_role_type="COMPANY_ADMIN",
        created_at=created_at,
        updated_at=None,
    )

    assert role.id_org_role == 1
    assert role.org_role_type == "COMPANY_ADMIN"
    assert role.created_at == created_at
    assert role.updated_at is None


def test_organization_role_create_accepts_valid_data() -> None:
    role = OrganizationRoleCreate(org_role_type="COMPANY_ADMIN")

    assert role.org_role_type == "COMPANY_ADMIN"


def test_organization_role_update_allows_partial_update() -> None:
    role_update = OrganizationRoleUpdate()

    assert role_update.org_role_type is None


def test_organization_role_schemas_validate_role_type_length() -> None:
    too_long_role_type = "a" * 51

    with pytest.raises(ValidationError) as exc_info:
        OrganizationRoleCreate(org_role_type=too_long_role_type)

    assert "org_role_type" in str(exc_info.value)


def test_organization_role_migration_creates_only_expected_table() -> None:
    migration_content = Path(
        "alembic/versions/0005_create_tbl_organization_role.py"
    ).read_text(encoding="utf-8")

    assert "tbl_organization_role" in migration_content
    assert 'schema="sch_iam"' in migration_content
    assert "pk_tbl_organization_role" in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert "tbl_state" not in migration_content
    assert "tbl_city" not in migration_content
    assert "tbl_organization" not in migration_content.replace(
        "tbl_organization_role", ""
    )
    assert "tbl_users" not in migration_content
    assert "tbl_department" not in migration_content
    assert "tbl_department_relations" not in migration_content
    assert migration_content.count("op.create_table") == 1


def test_previous_access_models_still_exist() -> None:
    assert Status.__tablename__ == "tbl_status"
    assert PlatformRole.__tablename__ == "tbl_platform_role"
