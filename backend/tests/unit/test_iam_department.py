from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.sql.schema import ForeignKeyConstraint, PrimaryKeyConstraint, Table
from sqlalchemy.sql.type_api import TypeEngine

from app.domain.iam.departments.models import Department
from app.domain.iam.departments.schemas import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
)

pytestmark = pytest.mark.test_unit

EXPECTED_COLUMNS = {
    "id_department",
    "id_organization",
    "name",
    "description",
    "create_at",
    "update_at",
}


def test_department_model_uses_expected_table_and_schema() -> None:
    assert Department.__tablename__ == "tbl_department"
    assert Department.__table__.schema == "sch_iam"


def test_department_model_has_exact_expected_columns() -> None:
    assert set(Department.__table__.columns.keys()) == EXPECTED_COLUMNS


@pytest.mark.parametrize(
    ("column_name", "expected_type", "nullable", "length"),
    [
        ("id_department", BigInteger, False, None),
        ("id_organization", BigInteger, False, None),
        ("name", String, False, 150),
        ("description", Text, True, None),
        ("create_at", DateTime, False, None),
        ("update_at", DateTime, True, None),
    ],
)
def test_department_columns_have_expected_types_and_nullability(
    column_name: str,
    expected_type: type[TypeEngine[object]],
    nullable: bool,
    length: int | None,
) -> None:
    column = Department.__table__.columns[column_name]

    assert isinstance(column.type, expected_type)
    assert column.nullable is nullable
    if length is not None:
        string_type = cast(String, column.type)
        assert string_type.length == length


def test_department_primary_key_has_explicit_name() -> None:
    primary_key = Department.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_department"


def test_department_foreign_key_has_expected_target_and_policies() -> None:
    table = cast(Table, Department.__table__)
    foreign_keys = {
        constraint.name: constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    assert set(foreign_keys) == {"fk_tbl_department_id_organization"}
    foreign_key = foreign_keys["fk_tbl_department_id_organization"]
    assert foreign_key.ondelete == "RESTRICT"
    assert foreign_key.onupdate == "CASCADE"
    assert [element.target_fullname for element in foreign_key.elements] == [
        "sch_iam.tbl_organization.id_organization"
    ]


def test_department_has_foreign_key_index() -> None:
    table = cast(Table, Department.__table__)
    indexes = {
        index.name: [column.name for column in index.columns] for index in table.indexes
    }

    assert indexes == {"ix_tbl_department_id_organization": ["id_organization"]}


def test_department_timestamps_are_timezone_aware() -> None:
    created_at = Department.__table__.columns["create_at"]
    updated_at = Department.__table__.columns["update_at"]

    assert isinstance(created_at.type, DateTime)
    assert created_at.type.timezone is True
    assert created_at.server_default is not None
    assert isinstance(updated_at.type, DateTime)
    assert updated_at.type.timezone is True
    assert updated_at.nullable is True


def test_department_create_accepts_valid_data() -> None:
    department = DepartmentCreate(
        id_organization=1,
        name="SOC L1",
        description="Equipo de analistas SOC L1",
    )

    assert department.id_organization == 1
    assert department.name == "SOC L1"
    assert department.description == "Equipo de analistas SOC L1"


def test_department_update_allows_partial_update() -> None:
    department_update = DepartmentUpdate(name="SOC L2")

    assert department_update.name == "SOC L2"
    assert department_update.id_organization is None
    assert department_update.description is None


def test_department_read_uses_flat_fields() -> None:
    now = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    department = DepartmentRead(
        id_department=10,
        id_organization=1,
        name="SOC L1",
        description=None,
        created_at=now,
        updated_at=None,
    )

    assert department.model_dump() == {
        "id_department": 10,
        "id_organization": 1,
        "name": "SOC L1",
        "description": None,
        "created_at": now,
        "updated_at": None,
    }


@pytest.mark.parametrize("schema", [DepartmentCreate, DepartmentUpdate])
def test_department_schemas_validate_name_length(
    schema: type[DepartmentCreate] | type[DepartmentUpdate],
) -> None:
    payload = {"id_organization": 1, "name": "a" * 151, "description": None}

    with pytest.raises(ValidationError) as exc_info:
        schema.model_validate(payload)

    assert "name" in str(exc_info.value)


def test_department_migration_creates_only_tbl_department_without_seeds() -> None:
    migration_content = Path(
        "alembic/versions/0010_create_tbl_department.py"
    ).read_text(encoding="utf-8")

    assert "tbl_department" in migration_content
    assert "sch_iam" in migration_content
    assert 'down_revision: str | None = "0009_create_tbl_users"' in migration_content
    for expected_fragment in (
        "pk_tbl_department",
        "fk_tbl_department_id_organization",
        "ix_tbl_department_id_organization",
        "sch_iam.tbl_organization.id_organization",
        'ondelete="RESTRICT"',
        'onupdate="CASCADE"',
    ):
        assert expected_fragment in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert migration_content.count("op.create_table") == 1
    department_relations_create_table = (
        'op.create_table(\n        "tbl_department_relations"'
    )
    assert department_relations_create_table not in migration_content
