from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, String
from sqlalchemy.sql.schema import ForeignKeyConstraint, PrimaryKeyConstraint, Table

from app.domain.iam.geography.models import Country, State
from app.domain.iam.geography.schemas import StateCreate, StateRead, StateUpdate


def test_country_model_still_exists() -> None:
    assert Country.__tablename__ == "tbl_country"


def test_state_model_uses_expected_table_and_schema() -> None:
    assert State.__tablename__ == "tbl_state"
    assert State.__table__.schema == "sch_iam"


def test_state_model_has_exact_expected_columns() -> None:
    assert set(State.__table__.columns.keys()) == {
        "id_state",
        "id_country",
        "state_name",
    }
    assert "create_at" not in State.__table__.columns
    assert "update_at" not in State.__table__.columns


def test_state_id_is_big_integer_primary_key() -> None:
    id_column = State.__table__.columns["id_state"]

    assert isinstance(id_column.type, BigInteger)
    assert id_column.primary_key is True


def test_state_primary_key_has_explicit_name() -> None:
    primary_key = State.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_state"


def test_state_country_id_is_required_big_integer() -> None:
    country_id_column = State.__table__.columns["id_country"]

    assert isinstance(country_id_column.type, BigInteger)
    assert country_id_column.nullable is False


def test_state_foreign_key_has_expected_target_and_policies() -> None:
    table = State.__table__
    assert isinstance(table, Table)
    foreign_keys = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_keys) == 1
    foreign_key = foreign_keys[0]
    assert foreign_key.name == "fk_tbl_state_id_country"
    assert foreign_key.ondelete == "RESTRICT"
    assert foreign_key.onupdate == "CASCADE"
    assert [element.target_fullname for element in foreign_key.elements] == [
        "sch_iam.tbl_country.id_country"
    ]


def test_state_has_country_id_index() -> None:
    table = State.__table__
    assert isinstance(table, Table)
    state_index = next(
        index for index in table.indexes if index.name == "ix_tbl_state_id_country"
    )

    assert [column.name for column in state_index.columns] == ["id_country"]


def test_state_name_is_required_string_with_expected_length() -> None:
    name_column = State.__table__.columns["state_name"]

    assert isinstance(name_column.type, String)
    assert name_column.type.length == 100
    assert name_column.nullable is False


def test_state_read_accepts_valid_data() -> None:
    state = StateRead(id_state=1, id_country=34, state_name="Barcelona")

    assert state.id_state == 1
    assert state.id_country == 34
    assert state.state_name == "Barcelona"


def test_state_create_accepts_valid_data() -> None:
    state = StateCreate(id_country=34, state_name="Madrid")

    assert state.id_country == 34
    assert state.state_name == "Madrid"


def test_state_update_allows_partial_update() -> None:
    state_update = StateUpdate(state_name="Valencia")

    assert state_update.id_country is None
    assert state_update.state_name == "Valencia"


def test_state_schemas_validate_state_name_length() -> None:
    too_long_name = "a" * 101

    with pytest.raises(ValidationError) as exc_info:
        StateCreate(id_country=34, state_name=too_long_name)

    assert "state_name" in str(exc_info.value)


def test_state_migration_creates_only_tbl_state_without_seeds() -> None:
    migration_content = Path("alembic/versions/0006_create_tbl_state.py").read_text(
        encoding="utf-8"
    )
    department_relations_create_table = (
        'op.create_table(\n        "tbl_department_relations"'
    )

    assert "tbl_state" in migration_content
    assert 'schema="sch_iam"' in migration_content
    assert "pk_tbl_state" in migration_content
    assert "fk_tbl_state_id_country" in migration_content
    assert "ix_tbl_state_id_country" in migration_content
    assert 'ondelete="RESTRICT"' in migration_content
    assert 'onupdate="CASCADE"' in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert migration_content.count("op.create_table") == 1
    assert 'op.create_table(\n        "tbl_city"' not in migration_content
    assert 'op.create_table(\n        "tbl_organization"' not in migration_content
    assert 'op.create_table(\n        "tbl_users"' not in migration_content
    assert 'op.create_table(\n        "tbl_department"' not in migration_content
    assert department_relations_create_table not in migration_content
