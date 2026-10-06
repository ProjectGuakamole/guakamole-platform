from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import BigInteger, DateTime
from sqlalchemy.sql.schema import (
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    Table,
    UniqueConstraint,
)
from sqlalchemy.sql.type_api import TypeEngine

from app.domain.iam.departments.models import Department, DepartmentRelation
from app.domain.iam.departments.schemas import (
    DepartmentRelationCreate,
    DepartmentRelationRead,
    DepartmentRelationUpdate,
)

pytestmark = pytest.mark.test_unit

EXPECTED_COLUMNS = {
    "id_department_relation",
    "id_department",
    "id_user",
    "create_at",
    "update_at",
}


def test_department_relation_model_uses_expected_table_and_schema() -> None:
    assert DepartmentRelation.__tablename__ == "tbl_department_relations"
    assert DepartmentRelation.__table__.schema == "sch_iam"


def test_department_relation_model_has_exact_expected_columns() -> None:
    assert set(DepartmentRelation.__table__.columns.keys()) == EXPECTED_COLUMNS


@pytest.mark.parametrize(
    ("column_name", "expected_type", "nullable"),
    [
        ("id_department_relation", BigInteger, False),
        ("id_department", BigInteger, False),
        ("id_user", BigInteger, False),
        ("create_at", DateTime, False),
        ("update_at", DateTime, True),
    ],
)
def test_department_relation_columns_have_expected_types_and_nullability(
    column_name: str,
    expected_type: type[TypeEngine[object]],
    nullable: bool,
) -> None:
    column = DepartmentRelation.__table__.columns[column_name]

    assert isinstance(column.type, expected_type)
    assert column.nullable is nullable


def test_department_relation_primary_key_has_explicit_name() -> None:
    primary_key = DepartmentRelation.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_department_relations"


def test_department_relation_foreign_keys_have_expected_targets_and_policies() -> None:
    table = cast(Table, DepartmentRelation.__table__)
    foreign_keys = {
        constraint.name: constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    expected_targets = {
        "fk_tbl_department_relations_id_department": (
            "sch_iam.tbl_department.id_department"
        ),
        "fk_tbl_department_relations_id_user": "sch_iam.tbl_users.id_user",
    }

    assert set(foreign_keys) == set(expected_targets)
    for name, target in expected_targets.items():
        foreign_key = foreign_keys[name]
        assert foreign_key.ondelete == "CASCADE"
        assert foreign_key.onupdate == "CASCADE"
        assert [element.target_fullname for element in foreign_key.elements] == [target]


def test_department_relation_unique_constraint_has_explicit_name() -> None:
    table = cast(Table, DepartmentRelation.__table__)
    unique_constraints = {
        constraint.name: [column.name for column in constraint.columns]
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert unique_constraints == {
        "uq_tbl_department_relations_id_department_id_user": [
            "id_department",
            "id_user",
        ]
    }


def test_department_relation_has_foreign_key_indexes() -> None:
    table = cast(Table, DepartmentRelation.__table__)
    indexes = {
        index.name: [column.name for column in index.columns] for index in table.indexes
    }

    assert indexes == {
        "ix_tbl_department_relations_id_department": ["id_department"],
        "ix_tbl_department_relations_id_user": ["id_user"],
    }


def test_department_relation_timestamps_are_timezone_aware() -> None:
    created_at = DepartmentRelation.__table__.columns["create_at"]
    updated_at = DepartmentRelation.__table__.columns["update_at"]

    assert isinstance(created_at.type, DateTime)
    assert created_at.type.timezone is True
    assert created_at.server_default is not None
    assert isinstance(updated_at.type, DateTime)
    assert updated_at.type.timezone is True
    assert updated_at.nullable is True


def test_department_relation_create_accepts_valid_data() -> None:
    relation = DepartmentRelationCreate(id_department=1, id_user=2)

    assert relation.id_department == 1
    assert relation.id_user == 2


def test_department_relation_update_allows_partial_update() -> None:
    relation_update = DepartmentRelationUpdate(id_user=3)

    assert relation_update.id_department is None
    assert relation_update.id_user == 3


def test_department_relation_read_uses_flat_fields() -> None:
    now = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    relation = DepartmentRelationRead(
        id_department_relation=10,
        id_department=1,
        id_user=2,
        created_at=now,
        updated_at=None,
    )

    assert relation.model_dump() == {
        "id_department_relation": 10,
        "id_department": 1,
        "id_user": 2,
        "created_at": now,
        "updated_at": None,
    }


def test_department_relation_migration_creates_only_relation_table_without_seeds() -> (
    None
):
    migration_content = Path(
        "alembic/versions/0011_create_tbl_department_relations.py"
    ).read_text(encoding="utf-8")

    assert "tbl_department_relations" in migration_content
    assert "sch_iam" in migration_content
    assert (
        'down_revision: str | None = "0010_create_tbl_department"' in migration_content
    )
    for expected_fragment in (
        "pk_tbl_department_relations",
        "fk_tbl_department_relations_id_department",
        "fk_tbl_department_relations_id_user",
        "uq_tbl_department_relations_id_department_id_user",
        "ix_tbl_department_relations_id_department",
        "ix_tbl_department_relations_id_user",
        "sch_iam.tbl_department.id_department",
        "sch_iam.tbl_users.id_user",
        'ondelete="CASCADE"',
        'onupdate="CASCADE"',
    ):
        assert expected_fragment in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert migration_content.count("op.create_table") == 1
    assert 'op.create_table(\n        "tbl_department"' not in migration_content
    assert 'op.create_table(\n        "tbl_users"' not in migration_content


def test_department_model_still_uses_original_table() -> None:
    assert Department.__tablename__ == "tbl_department"
    assert Department.__table__.schema == "sch_iam"
