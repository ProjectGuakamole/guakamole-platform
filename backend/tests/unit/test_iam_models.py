from datetime import UTC, datetime
from typing import cast

import pytest
from sqlalchemy.sql.ddl import CreateIndex
from sqlalchemy.sql.schema import Table

from app.db.base import Base
from app.domains.iam.access.models import OrganizationRole, PlatformRole, Status
from app.domains.iam.departments.models import Department, DepartmentRelation
from app.domains.iam.departments.schemas import (
    DepartmentRelationCreate,
    DepartmentRelationRead,
    DepartmentRelationUpdate,
)
from app.domains.iam.geography.models import City, Country, State
from app.domains.iam.geography.schemas import CityCreate, CityRead, CityUpdate

pytestmark = pytest.mark.test_unit


@pytest.mark.parametrize(
    ("model", "index_name", "expected"),
    [
        (Country, "uq_tbl_country_country_name_ci", "lower(country_name)"),
        (Status, "uq_tbl_status_status_ci", "lower(status)"),
        (PlatformRole, "uq_tbl_platform_role_type_ci", "lower(platform_role_type)"),
        (OrganizationRole, "uq_tbl_organization_role_type_ci", "lower(org_role_type)"),
        (State, "uq_tbl_state_country_name_ci", "lower(state_name)"),
        (City, "uq_tbl_city_state_name_ci", "lower(city_name)"),
        (Department, "uq_tbl_department_organization_name_ci", "lower(name)"),
    ],
)
def test_case_insensitive_indexes_compile_like_baseline(
    model: type[Base],
    index_name: str,
    expected: str,
) -> None:
    table = cast(Table, model.__table__)
    index = next(item for item in table.indexes if item.name == index_name)
    compiled = str(CreateIndex(index).compile())
    assert expected in compiled


def test_city_schemas_require_country_scope() -> None:
    city = CityCreate(id_state=2, id_country=1, city_name="Madrid")
    assert CityRead(id_city=3, **city.model_dump()).id_country == 1
    assert CityUpdate(id_country=1).id_country == 1


def test_department_relation_schemas_include_organization_scope() -> None:
    relation = DepartmentRelationCreate(id_department=1, id_user=2, id_organization=3)
    assert (
        DepartmentRelationRead(
            id_department_relation=4,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=None,
            **relation.model_dump(),
        ).id_organization
        == 3
    )
    assert DepartmentRelationUpdate(id_organization=3).id_organization == 3
    assert "id_organization" in DepartmentRelation.__table__.columns
