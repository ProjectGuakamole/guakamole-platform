"""Contratos estáticos de los valores naturales del bootstrap IAM."""

from __future__ import annotations

import pytest

from app.core.iam_bootstrap import GEO, ORG_ROLES, PLATFORM_ROLES, STATUSES


@pytest.mark.test_unit
def test_catalogos_canonicos_aprobados() -> None:
    assert tuple(value for _, value in STATUSES) == ("ACTIVE", "INACTIVE", "DISABLED")
    assert tuple(role for _, role, _ in PLATFORM_ROLES) == ("PLATFORM_ADMIN", "USER")
    assert tuple(role for _, role in ORG_ROLES) == (
        "COMPANY_ADMIN",
        "GROUP_MANAGER",
        "SCENARIO_EDITOR",
        "EMPLOYEE",
    )
    assert tuple(item[1] for item in GEO) == ("España", "España", "Portugal", "Francia")


@pytest.mark.test_unit
def test_identificadores_deterministas_son_solo_reservas_de_insercion() -> None:
    assert tuple(identifier for identifier, _ in STATUSES) == (101, 102, 103)
    assert tuple(identifier for identifier, _, _ in PLATFORM_ROLES) == (201, 202)
    assert tuple(identifier for identifier, _ in ORG_ROLES) == (301, 302, 303, 304)
