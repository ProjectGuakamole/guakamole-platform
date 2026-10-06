import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "0012_seed_initial_iam_catalogs.py"
)
MIGRATION_CONTENT = MIGRATION_PATH.read_text(encoding="utf-8")


def test_seed_migration_exists_with_expected_revision() -> None:
    assert MIGRATION_PATH.exists()
    assert 'revision = "0012_seed_initial_iam_catalogs"' in MIGRATION_CONTENT
    assert 'down_revision = "0011_create_tbl_department_relations"' in MIGRATION_CONTENT


def test_seed_migration_uses_literal_schema_without_iam_schema_import() -> None:
    assert "sch_iam" in MIGRATION_CONTENT
    assert "IAM_SCHEMA" not in MIGRATION_CONTENT


def test_seed_migration_does_not_create_tables() -> None:
    forbidden_tokens = ("op.create_table", "CREATE TABLE", "create_table(")

    for token in forbidden_tokens:
        assert token not in MIGRATION_CONTENT


def test_seed_migration_inserts_only_target_catalog_tables() -> None:
    expected_tables = (
        "tbl_status",
        "tbl_platform_role",
        "tbl_organization_role",
        "tbl_country",
        "tbl_state",
        "tbl_city",
    )

    for table_name in expected_tables:
        assert f"INSERT INTO sch_iam.{table_name}" in MIGRATION_CONTENT

    forbidden_tables = (
        "tbl_users",
        "tbl_organization",
        "tbl_department",
        "tbl_department_relations",
    )
    for forbidden_table in forbidden_tables:
        pattern = rf"INSERT\s+INTO\s+sch_iam\.{forbidden_table}\b"
        assert re.search(pattern, MIGRATION_CONTENT) is None


def test_seed_migration_contains_expected_seed_values() -> None:
    expected_values = (
        "ACTIVE",
        "INACTIVE",
        "DISABLED",
        "PLATFORM_ADMIN",
        "Administrador global de la plataforma.",
        "USER",
        "Usuario estándar de la plataforma.",
        "COMPANY_ADMIN",
        "GROUP_MANAGER",
        "EMPLOYEE",
        "España",
        "Portugal",
        "Francia",
        "Catalunya",
        "Madrid",
        "Lisboa",
        "Barcelona",
    )

    for expected_value in expected_values:
        assert expected_value in MIGRATION_CONTENT


def test_seed_migration_contains_expected_downgrade_deletes() -> None:
    expected_deletes = (
        "DELETE FROM sch_iam.tbl_city",
        "DELETE FROM sch_iam.tbl_state",
        "DELETE FROM sch_iam.tbl_country",
        "DELETE FROM sch_iam.tbl_organization_role",
        "DELETE FROM sch_iam.tbl_platform_role",
        "DELETE FROM sch_iam.tbl_status",
    )

    for expected_delete in expected_deletes:
        assert expected_delete in MIGRATION_CONTENT


def test_seed_migration_downgrade_order_respects_dependencies() -> None:
    city_index = MIGRATION_CONTENT.index("DELETE FROM sch_iam.tbl_city")
    state_index = MIGRATION_CONTENT.index("DELETE FROM sch_iam.tbl_state")
    country_index = MIGRATION_CONTENT.index("DELETE FROM sch_iam.tbl_country")
    organization_role_index = MIGRATION_CONTENT.index(
        "DELETE FROM sch_iam.tbl_organization_role",
    )
    platform_role_index = MIGRATION_CONTENT.index(
        "DELETE FROM sch_iam.tbl_platform_role",
    )
    status_index = MIGRATION_CONTENT.index("DELETE FROM sch_iam.tbl_status")

    assert city_index < state_index < country_index
    assert country_index < organization_role_index
    assert organization_role_index < platform_role_index < status_index
