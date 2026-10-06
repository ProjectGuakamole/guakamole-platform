from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import BigInteger, String
from sqlalchemy.sql.schema import PrimaryKeyConstraint

from app.domain.iam.geography.models import Country
from app.domain.iam.geography.schemas import CountryRead, CountryUpdate

pytestmark = pytest.mark.test_unit


def test_country_model_uses_expected_table_and_schema() -> None:
    assert Country.__tablename__ == "tbl_country"
    assert Country.__table__.schema == "sch_iam"


def test_country_model_has_exact_expected_columns() -> None:
    assert set(Country.__table__.columns.keys()) == {"id_country", "country_name"}
    assert "create_at" not in Country.__table__.columns
    assert "update_at" not in Country.__table__.columns


def test_country_id_is_big_integer_primary_key() -> None:
    id_column = Country.__table__.columns["id_country"]

    assert isinstance(id_column.type, BigInteger)
    assert id_column.primary_key is True


def test_country_primary_key_has_explicit_name() -> None:
    primary_key = Country.__table__.primary_key

    assert isinstance(primary_key, PrimaryKeyConstraint)
    assert primary_key.name == "pk_tbl_country"


def test_country_name_is_required_string_with_expected_length() -> None:
    name_column = Country.__table__.columns["country_name"]

    assert isinstance(name_column.type, String)
    assert name_column.type.length == 100
    assert name_column.nullable is False


def test_country_read_accepts_valid_data() -> None:
    country = CountryRead(id_country=1, country_name="España")

    assert country.id_country == 1
    assert country.country_name == "España"


def test_country_update_allows_partial_update() -> None:
    country_update = CountryUpdate()

    assert country_update.country_name is None


def test_country_schemas_validate_country_name_length() -> None:
    too_long_name = "a" * 101

    with pytest.raises(ValidationError) as exc_info:
        CountryRead(id_country=1, country_name=too_long_name)

    assert "country_name" in str(exc_info.value)


def test_country_migration_creates_only_tbl_country_without_seeds() -> None:
    migration_content = Path("alembic/versions/0002_create_tbl_country.py").read_text(
        encoding="utf-8"
    )

    assert "tbl_country" in migration_content
    assert 'schema="sch_iam"' in migration_content
    assert "pk_tbl_country" in migration_content
    assert "IAM_SCHEMA" not in migration_content
    assert "op.bulk_insert" not in migration_content
    assert "tbl_status" not in migration_content
    assert "tbl_organization" not in migration_content
    assert "tbl_user" not in migration_content
    assert migration_content.count("op.create_table") == 1
