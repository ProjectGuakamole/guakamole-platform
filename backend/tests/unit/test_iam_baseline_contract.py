import ast
import re
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import Identity
from sqlalchemy.sql.schema import ForeignKeyConstraint, Table, UniqueConstraint

from app.domains.auth.shared.models import RevokedAccessToken
from app.domains.iam.access.models import OrganizationRole, PlatformRole, Status
from app.domains.iam.departments.models import Department, DepartmentRelation
from app.domains.iam.geography.models import City, Country, State
from app.domains.iam.organizations.models import Organization
from app.domains.iam.users.models import User

pytestmark = pytest.mark.test_unit

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_iam_contract_exposes_exactly_eleven_tables() -> None:
    tables: tuple[Table, ...] = (
        cast(Table, Country.__table__),
        cast(Table, State.__table__),
        cast(Table, City.__table__),
        cast(Table, Organization.__table__),
        cast(Table, User.__table__),
        cast(Table, Department.__table__),
        cast(Table, DepartmentRelation.__table__),
        cast(Table, RevokedAccessToken.__table__),
    )
    tables += (
        cast(Table, Status.__table__),
        cast(Table, PlatformRole.__table__),
        cast(Table, OrganizationRole.__table__),
    )
    assert {table.fullname for table in tables} == {
        "sch_iam.tbl_country",
        "sch_iam.tbl_state",
        "sch_iam.tbl_city",
        "sch_iam.tbl_organization",
        "sch_iam.tbl_users",
        "sch_iam.tbl_department",
        "sch_iam.tbl_department_relations",
        "sch_iam.tbl_revoked_access_token",
        "sch_iam.tbl_status",
        "sch_iam.tbl_platform_role",
        "sch_iam.tbl_organization_role",
    }


def test_baseline_contains_only_ddl_operations() -> None:
    tree = ast.parse(
        (BACKEND_ROOT / "alembic/versions/iam_baseline.py").read_text("utf-8")
    )
    operation_names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "op":
            operation_names.add(node.func.attr)
    assert operation_names == {
        "create_table",
        "create_index",
        "execute",
    }


def test_postgresql_catalog_seed_statements_specify_columns() -> None:
    """Evita que los defaults de timestamps desplacen los valores del catálogo."""

    integration_test = (
        BACKEND_ROOT / "tests" / "integration" / "test_iam_baseline_postgresql.py"
    )
    source = integration_test.read_text("utf-8")
    tree = ast.parse(source)
    seed_catalogs = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_seed_catalogs"
    )
    seed_source = ast.get_source_segment(source, seed_catalogs)

    assert seed_source is not None
    assert not re.search(r"INSERT INTO sch_iam\.tbl_\w+\s+VALUES", seed_source)


def test_registration_identifiers_and_public_ids_follow_contract() -> None:
    for model, column_name in ((Organization, "id_organization"), (User, "id_user")):
        column = model.__table__.columns[column_name]
        assert isinstance(column.identity, Identity)
        assert column.identity.start == 1
        public_id = model.__table__.columns["public_id"]
        assert public_id.nullable is False
        assert public_id.server_default is None


def test_department_relation_is_scoped_to_its_organization() -> None:
    table = cast(Table, DepartmentRelation.__table__)
    assert "id_organization" in table.columns
    foreign_keys = {
        constraint.name: constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    assert [
        item.target_fullname
        for item in foreign_keys[
            "fk_tbl_department_relations_department_organization"
        ].elements
    ] == [
        "sch_iam.tbl_department.id_department",
        "sch_iam.tbl_department.id_organization",
    ]
    assert [
        item.target_fullname
        for item in foreign_keys[
            "fk_tbl_department_relations_user_organization"
        ].elements
    ] == [
        "sch_iam.tbl_users.id_user",
        "sch_iam.tbl_users.id_organization",
    ]


def test_geography_and_tenant_composite_candidates_exist() -> None:
    candidates: tuple[tuple[Table, set[str]], ...] = (
        (cast(Table, State.__table__), {"id_state", "id_country"}),
        (cast(Table, City.__table__), {"id_city", "id_state", "id_country"}),
        (cast(Table, Department.__table__), {"id_department", "id_organization"}),
        (cast(Table, User.__table__), {"id_user", "id_organization"}),
    )
    for table, columns in candidates:
        unique_columns = {
            frozenset(column.name for column in constraint.columns)
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert frozenset(columns) in unique_columns


def test_revocation_jti_is_unique_and_indexed() -> None:
    index = next(
        item
        for item in cast(Table, RevokedAccessToken.__table__).indexes
        if item.name == "ix_tbl_revoked_access_token_jti"
    )
    assert index.unique is True
