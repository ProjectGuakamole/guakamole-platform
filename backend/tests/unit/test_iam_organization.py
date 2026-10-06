from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict, cast

import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.sql.schema import (
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    Table,
    UniqueConstraint,
)
from sqlalchemy.sql.type_api import TypeEngine

from app.domain.iam.organizations.models import Organization
from app.domain.iam.organizations.schemas import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)

EXPECTED_COLUMNS = {
    "id_organization",
    "id_country",
    "id_state",
    "id_city",
    "id_status",
    "name",
    "slug",
    "org_registered_name",
    "org_tax",
    "org_address",
    "org_zipcode",
    "create_at",
    "update_at",
}


class OrganizationPayload(TypedDict):
    id_country: int
    id_state: int
    id_city: int
    id_status: int
    name: str
    slug: str
    org_registered_name: str
    org_tax: str
    org_address: str
    org_zipcode: str


def test_organization_model_uses_expected_table_and_schema() -> None:
    assert Organization.__tablename__ == "tbl_organization"
    assert Organization.__table__.schema == "sch_iam"


def test_organization_model_has_exact_expected_columns() -> None:
    assert set(Organization.__table__.columns.keys()) == EXPECTED_COLUMNS


@pytest.mark.parametrize(
    ("column_name", "expected_type", "nullable", "length"),
    [
        ("id_organization", BigInteger, False, None),
        ("id_country", BigInteger, False, None),
        ("id_state", BigInteger, False, None),
        ("id_city", BigInteger, False, None),
        ("id_status", BigInteger, False, None),
        ("name", String, False, 150),
        ("slug", String, False, 120),
        ("org_registered_name", String, True, 200),
        ("org_tax", String, True, 32),
        ("org_address", String, False, 255),
        ("org_zipcode", String, False, 20),
        ("create_at", DateTime, False, None),
        ("update_at", DateTime, True, None),
    ],
)
def test_organization_columns_have_expected_types_and_nullability(
    column_name: str,
    expected_type: type[TypeEngine[object]],
    nullable: bool,
    length: int | None,
) -> None:
    column = Organization.__table__.columns[column_name]

    assert isinstance(column.type, expected_type)
    assert column.nullable is nullable
    if length is not None:
        string_type = cast(String, column.type)
        assert string_type.length == length


def test_organization_primary_key_has_explicit_name() -> None:
    primary_key = Organization.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_organization"


def test_organization_foreign_keys_have_expected_targets_and_policies() -> None:
    table = Organization.__table__
    assert isinstance(table, Table)
    foreign_keys = {
        constraint.name: constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    expected_targets = {
        "fk_tbl_organization_id_country": "sch_iam.tbl_country.id_country",
        "fk_tbl_organization_id_state": "sch_iam.tbl_state.id_state",
        "fk_tbl_organization_id_city": "sch_iam.tbl_city.id_city",
        "fk_tbl_organization_id_status": "sch_iam.tbl_status.id_status",
    }
    assert set(foreign_keys) == set(expected_targets)
    for name, target in expected_targets.items():
        foreign_key = foreign_keys[name]
        assert foreign_key.ondelete == "RESTRICT"
        assert foreign_key.onupdate == "CASCADE"
        assert [element.target_fullname for element in foreign_key.elements] == [target]


def test_organization_unique_constraints_have_explicit_names() -> None:
    table = cast(Table, Organization.__table__)
    unique_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert unique_names == {
        "uq_tbl_organization_name",
        "uq_tbl_organization_slug",
        "uq_tbl_organization_org_registered_name",
        "uq_tbl_organization_org_tax",
    }


def test_organization_has_foreign_key_indexes() -> None:
    table = cast(Table, Organization.__table__)
    indexes = {
        index.name: [column.name for column in index.columns] for index in table.indexes
    }

    assert indexes == {
        "ix_tbl_organization_id_country": ["id_country"],
        "ix_tbl_organization_id_state": ["id_state"],
        "ix_tbl_organization_id_city": ["id_city"],
        "ix_tbl_organization_id_status": ["id_status"],
    }


def test_organization_timestamps_come_from_timestamp_mixin() -> None:
    created_at = Organization.__table__.columns["create_at"]
    updated_at = Organization.__table__.columns["update_at"]

    assert isinstance(created_at.type, DateTime)
    assert created_at.type.timezone is True
    assert created_at.server_default is not None
    assert isinstance(updated_at.type, DateTime)
    assert updated_at.type.timezone is True
    assert updated_at.nullable is True


def valid_organization_payload() -> OrganizationPayload:
    return {
        "id_country": 1,
        "id_state": 2,
        "id_city": 3,
        "id_status": 4,
        "name": "ACME",
        "slug": "acme",
        "org_registered_name": "ACME SL",
        "org_tax": "B12345678",
        "org_address": "Calle Mayor 1",
        "org_zipcode": "08001",
    }


def test_organization_create_accepts_valid_data() -> None:
    organization = OrganizationCreate(**valid_organization_payload())

    assert organization.id_country == 1
    assert organization.name == "ACME"
    assert organization.org_registered_name == "ACME SL"


def test_organization_update_allows_partial_update() -> None:
    organization_update = OrganizationUpdate(name="ACME Updated")

    assert organization_update.name == "ACME Updated"
    assert organization_update.id_country is None
    assert organization_update.slug is None


def test_organization_read_uses_simple_ids_and_python_timestamps() -> None:
    created_at = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    updated_at = datetime(2026, 10, 2, 12, 30, tzinfo=UTC)
    organization = OrganizationRead(
        id_organization=10,
        created_at=created_at,
        updated_at=updated_at,
        **valid_organization_payload(),
    )

    assert organization.id_organization == 10
    assert organization.id_country == 1
    assert organization.created_at == created_at
    assert organization.updated_at == updated_at


@pytest.mark.parametrize(
    ("field_name", "max_length"),
    [
        ("name", 150),
        ("slug", 120),
        ("org_registered_name", 200),
        ("org_tax", 32),
        ("org_address", 255),
        ("org_zipcode", 20),
    ],
)
def test_organization_schemas_validate_lengths(
    field_name: str,
    max_length: int,
) -> None:
    payload: dict[str, object] = dict(valid_organization_payload())
    payload[field_name] = "a" * (max_length + 1)

    with pytest.raises(ValidationError) as exc_info:
        OrganizationCreate.model_validate(payload)

    assert field_name in str(exc_info.value)


def test_organization_migration_creates_only_tbl_organization_without_seeds() -> None:
    migration_content = Path(
        "alembic/versions/0008_create_tbl_organization.py"
    ).read_text(encoding="utf-8")

    assert "tbl_organization" in migration_content
    assert 'schema="sch_iam"' in migration_content
    assert 'down_revision: str | None = "0007_create_tbl_city"' in migration_content
    for expected_fragment in (
        "pk_tbl_organization",
        "fk_tbl_organization_id_country",
        "fk_tbl_organization_id_state",
        "fk_tbl_organization_id_city",
        "fk_tbl_organization_id_status",
        "uq_tbl_organization_name",
        "uq_tbl_organization_slug",
        "uq_tbl_organization_org_registered_name",
        "uq_tbl_organization_org_tax",
        "ix_tbl_organization_id_country",
        "ix_tbl_organization_id_state",
        "ix_tbl_organization_id_city",
        "ix_tbl_organization_id_status",
        "sch_iam.tbl_country.id_country",
        "sch_iam.tbl_state.id_state",
        "sch_iam.tbl_city.id_city",
        "sch_iam.tbl_status.id_status",
        'ondelete="RESTRICT"',
        'onupdate="CASCADE"',
    ):
        assert expected_fragment in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert migration_content.count("op.create_table") == 1
    assert 'op.create_table(\n        "tbl_users"' not in migration_content
    assert 'op.create_table(\n        "tbl_department"' not in migration_content
    department_relations_create_table = (
        'op.create_table(\n        "tbl_department_relations"'
    )
    assert department_relations_create_table not in migration_content
