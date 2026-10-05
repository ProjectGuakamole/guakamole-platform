from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, String
from sqlalchemy.sql.schema import ForeignKeyConstraint, PrimaryKeyConstraint, Table

from app.domain.iam.geography.models import City, Country, State
from app.domain.iam.geography.schemas import CityCreate, CityRead, CityUpdate


def test_country_and_state_models_still_exist() -> None:
    assert Country.__tablename__ == "tbl_country"
    assert State.__tablename__ == "tbl_state"


def test_city_model_uses_expected_table_and_schema() -> None:
    assert City.__tablename__ == "tbl_city"
    assert City.__table__.schema == "sch_iam"


def test_city_model_has_exact_expected_columns() -> None:
    assert set(City.__table__.columns.keys()) == {
        "id_city",
        "id_state",
        "city_name",
    }
    assert "create_at" not in City.__table__.columns
    assert "update_at" not in City.__table__.columns


def test_city_id_is_big_integer_primary_key() -> None:
    id_column = City.__table__.columns["id_city"]

    assert isinstance(id_column.type, BigInteger)
    assert id_column.primary_key is True


def test_city_primary_key_has_explicit_name() -> None:
    primary_key = City.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_city"


def test_city_state_id_is_required_big_integer() -> None:
    state_id_column = City.__table__.columns["id_state"]

    assert isinstance(state_id_column.type, BigInteger)
    assert state_id_column.nullable is False


def test_city_foreign_key_has_expected_target_and_policies() -> None:
    table = City.__table__
    assert isinstance(table, Table)
    foreign_keys = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert len(foreign_keys) == 1
    foreign_key = foreign_keys[0]
    assert foreign_key.name == "fk_tbl_city_id_state"
    assert foreign_key.ondelete == "RESTRICT"
    assert foreign_key.onupdate == "CASCADE"
    assert [element.target_fullname for element in foreign_key.elements] == [
        "sch_iam.tbl_state.id_state"
    ]


def test_city_has_state_id_index() -> None:
    table = City.__table__
    assert isinstance(table, Table)
    city_index = next(
        index for index in table.indexes if index.name == "ix_tbl_city_id_state"
    )

    assert [column.name for column in city_index.columns] == ["id_state"]


def test_city_name_is_required_string_with_expected_length() -> None:
    name_column = City.__table__.columns["city_name"]

    assert isinstance(name_column.type, String)
    assert name_column.type.length == 120
    assert name_column.nullable is False


def test_city_read_accepts_valid_data() -> None:
    city = CityRead(id_city=1, id_state=8, city_name="Barcelona")

    assert city.id_city == 1
    assert city.id_state == 8
    assert city.city_name == "Barcelona"


def test_city_create_accepts_valid_data() -> None:
    city = CityCreate(id_state=8, city_name="Madrid")

    assert city.id_state == 8
    assert city.city_name == "Madrid"


def test_city_update_allows_partial_update() -> None:
    city_update = CityUpdate(city_name="Valencia")

    assert city_update.id_state is None
    assert city_update.city_name == "Valencia"


def test_city_schemas_validate_city_name_length() -> None:
    too_long_name = "a" * 121

    with pytest.raises(ValidationError) as exc_info:
        CityCreate(id_state=8, city_name=too_long_name)

    assert "city_name" in str(exc_info.value)


def test_city_migration_creates_only_tbl_city_without_seeds() -> None:
    migration_content = Path("alembic/versions/0007_create_tbl_city.py").read_text(
        encoding="utf-8"
    )
    department_relations_create_table = (
        'op.create_table(\n        "tbl_department_relations"'
    )

    assert "tbl_city" in migration_content
    assert 'schema="sch_iam"' in migration_content
    assert "pk_tbl_city" in migration_content
    assert "fk_tbl_city_id_state" in migration_content
    assert "ix_tbl_city_id_state" in migration_content
    assert 'ondelete="RESTRICT"' in migration_content
    assert 'onupdate="CASCADE"' in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert migration_content.count("op.create_table") == 1
    assert 'op.create_table(\n        "tbl_organization"' not in migration_content
    assert 'op.create_table(\n        "tbl_users"' not in migration_content
    assert 'op.create_table(\n        "tbl_department"' not in migration_content
    assert department_relations_create_table not in migration_content
