"""Contratos de la línea base contra una base PostgreSQL exclusiva de test."""

import os
from collections.abc import Generator
from datetime import date

import pytest
from alembic.config import Config
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.iam_rebaseline import rebuild_iam_baseline
from app.core.test_database import get_test_database_url
from app.domains.iam.organizations.models import Organization
from app.domains.iam.users.models import User

pytestmark = [pytest.mark.integration, pytest.mark.db]


@pytest.fixture(scope="module")
def baseline_engine() -> Generator[Engine, None, None]:
    """Reconstruye la DB de test y la deja determinísticamente en ``head``."""

    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("Requiere TEST_DATABASE_URL explícita para ejecutar PostgreSQL.")
    database_url = get_test_database_url(os.environ)
    engine = create_engine(database_url, hide_parameters=True)
    config = Config("alembic.ini")
    try:
        rebuild_iam_baseline(engine, config)
        yield engine
    finally:
        rebuild_iam_baseline(engine, config)
        engine.dispose()


def _seed_catalogs(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_status (id_status, status) "
                "VALUES (1, 'ACTIVE')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_platform_role "
                "(id_platform_role, platform_role_type, description) "
                "VALUES (1, 'USER', NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_organization_role "
                "(id_org_role, org_role_type) VALUES (1, 'EMPLOYEE')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_country (id_country, country_name) "
                "VALUES (1, 'Spain'), (2, 'France')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_state "
                "(id_state, id_country, state_name) VALUES "
                "(1, 1, 'Madrid'), (2, 2, 'Ile-de-France')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_city "
                "(id_city, id_state, id_country, city_name) VALUES "
                "(1, 1, 1, 'Madrid'), (2, 2, 2, 'Paris')"
            )
        )


def _rejects(connection: Connection, statement: str) -> None:
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(text(statement))


def test_baseline_constraints_and_identity_contract(baseline_engine: Engine) -> None:
    _seed_catalogs(baseline_engine)
    session = Session(baseline_engine)
    try:
        organization = Organization(
            id_country=1,
            id_state=1,
            id_city=1,
            id_status=1,
            name="Acme",
            slug="acme",
            org_address="Calle 1",
            org_zipcode="28001",
        )
        session.add(organization)
        session.flush()
        user = User(
            id_organization=organization.id_organization,
            id_platform_role=1,
            id_country=1,
            id_state=1,
            id_city=1,
            id_org_role=1,
            id_status=1,
            email="ana@example.test",
            password_hash="test-hash",  # noqa: S106
            first_name="Ana",
            last_name="García",
            birthdate=date(1990, 1, 1),
            user_address="Calle 1",
            user_zipcode="28001",
        )
        session.add(user)
        session.commit()
        assert organization.id_organization == 1
        assert user.id_user == 1
        assert organization.public_id.startswith("org_")
        assert user.public_id.startswith("usr_")
    finally:
        session.close()

    with baseline_engine.begin() as connection:
        _rejects(
            connection,
            "INSERT INTO sch_iam.tbl_city "
            "(id_city, id_state, id_country, city_name) VALUES (3, 999, 1, 'Invalid')",
        )
        _rejects(
            connection,
            """INSERT INTO sch_iam.tbl_organization (
                public_id, id_country, id_state, id_city, id_status, name, slug,
                org_address, org_zipcode
            ) VALUES ('org_invalid', 1, 2, 2, 1, 'Invalid', 'invalid', 'x', 'x')""",
        )
        _rejects(
            connection,
            """INSERT INTO sch_iam.tbl_users (
                public_id, id_organization, id_platform_role, id_country, id_state,
                id_city, id_org_role, id_status, email, password_hash, first_name,
                last_name, birthdate, user_address, user_zipcode
            ) VALUES (
                'usr_invalid', 1, 1, 1, 2, 2, 1, 1, 'invalid@example.test', 'x',
                'x', 'x', '1990-01-01', 'x', 'x'
            )""",
        )
        _rejects(
            connection,
            "INSERT INTO sch_iam.tbl_status (id_status, status) VALUES (2, 'active')",
        )
        _rejects(
            connection,
            "INSERT INTO sch_iam.tbl_platform_role "
            "(id_platform_role, platform_role_type, description) "
            "VALUES (2, 'user', NULL)",
        )
        _rejects(
            connection,
            "INSERT INTO sch_iam.tbl_organization_role "
            "(id_org_role, org_role_type) VALUES (2, 'employee')",
        )
        _rejects(
            connection,
            "INSERT INTO sch_iam.tbl_country (id_country, country_name) "
            "VALUES (3, 'spain')",
        )
        _rejects(
            connection,
            "INSERT INTO sch_iam.tbl_state (id_state, id_country, state_name) "
            "VALUES (3, 1, 'madrid')",
        )
        _rejects(
            connection,
            "INSERT INTO sch_iam.tbl_city "
            "(id_city, id_state, id_country, city_name) VALUES (4, 1, 1, 'madrid')",
        )
        connection.execute(
            text(
                """INSERT INTO sch_iam.tbl_organization (
                    id_organization, public_id, id_country, id_state, id_city,
                    id_status, name, slug, org_address, org_zipcode
                ) VALUES (2, 'org_two', 1, 1, 1, 1, 'Other', 'other', 'x', 'x')"""
            )
        )
        connection.execute(
            text(
                """INSERT INTO sch_iam.tbl_users (
                    id_user, public_id, id_organization, id_platform_role,
                    id_country, id_state, id_city, id_org_role, id_status, email,
                    password_hash, first_name, last_name, birthdate, user_address,
                    user_zipcode
                ) VALUES (
                    2, 'usr_two', 2, 1, 1, 1, 1, 1, 1, 'two@example.test', 'x',
                    'x', 'x', '1990-01-01', 'x', 'x'
                )"""
            )
        )
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_department "
                "(id_department, id_organization, name, description) "
                "VALUES (1, 1, 'SOC', NULL)"
            )
        )
        _rejects(
            connection,
            "INSERT INTO sch_iam.tbl_department "
            "(id_department, id_organization, name, description) "
            "VALUES (2, 1, 'soc', NULL)",
        )
        _rejects(
            connection,
            "INSERT INTO sch_iam.tbl_department_relations "
            "(id_department_relation, id_department, id_user, id_organization) "
            "VALUES (1, 1, 2, 1)",
        )
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_department_relations "
                "(id_department_relation, id_department, id_user, id_organization) "
                "VALUES (2, 1, 1, 1)"
            )
        )
        assert (
            connection.execute(
                text("SELECT version_num FROM public.alembic_version")
            ).scalar_one()
            == "iam_baseline"
        )
