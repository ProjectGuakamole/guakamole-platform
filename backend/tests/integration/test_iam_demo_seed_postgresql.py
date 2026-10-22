"""Pruebas PostgreSQL del bootstrap y la demo IAM, aisladas por rebaseline."""

from __future__ import annotations

import os
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.iam_bootstrap import bootstrap_iam
from app.core.iam_rebaseline import rebuild_iam_baseline
from app.core.test_database import get_test_database_url
from app.domains.auth.shared.password_hasher import PwdlibPasswordHasher
from app.domains.auth.shared.public_ids import PublicIdPrefix, parse_public_uuid
from scripts import seed_demo_iam
from scripts.seed_demo_iam import (
    Organization,
    clear_demo,
    load_fixture,
    seed_demo,
)

pytestmark = [pytest.mark.integration, pytest.mark.db]

COUNT_STATEMENTS = {
    "tbl_organization": text("SELECT count(*) FROM sch_iam.tbl_organization"),
    "tbl_users": text("SELECT count(*) FROM sch_iam.tbl_users"),
    "tbl_department": text("SELECT count(*) FROM sch_iam.tbl_department"),
    "tbl_department_relations": text(
        "SELECT count(*) FROM sch_iam.tbl_department_relations"
    ),
    "tbl_status": text("SELECT count(*) FROM sch_iam.tbl_status"),
    "tbl_platform_role": text("SELECT count(*) FROM sch_iam.tbl_platform_role"),
    "tbl_organization_role": text("SELECT count(*) FROM sch_iam.tbl_organization_role"),
    "tbl_country": text("SELECT count(*) FROM sch_iam.tbl_country"),
    "tbl_state": text("SELECT count(*) FROM sch_iam.tbl_state"),
    "tbl_city": text("SELECT count(*) FROM sch_iam.tbl_city"),
}


@pytest.fixture
def iam_engine() -> Generator[Engine, None, None]:
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("Requiere TEST_DATABASE_URL explícita para ejecutar PostgreSQL.")
    engine = create_engine(get_test_database_url(os.environ), hide_parameters=True)
    config = Config("alembic.ini")
    rebuild_iam_baseline(engine, config)
    try:
        yield engine
    finally:
        rebuild_iam_baseline(engine, config)
        engine.dispose()


def _count(engine: Engine, table: str) -> int:
    with engine.connect() as connection:
        return int(connection.execute(COUNT_STATEMENTS[table]).scalar_one())


def _seed(engine: Engine) -> None:
    bootstrap_iam(engine)
    seed_demo(engine, "test-only-password", load_fixture())


def test_bootstrap_and_seed_are_idempotent_and_public_ids_fit(
    iam_engine: Engine,
) -> None:
    first = bootstrap_iam(iam_engine)
    assert first.created > 0
    assert bootstrap_iam(iam_engine).created == 0

    _seed(iam_engine)
    _seed(iam_engine)

    assert tuple(
        _count(iam_engine, table)
        for table in (
            "tbl_organization",
            "tbl_users",
            "tbl_department",
            "tbl_department_relations",
        )
    ) == (6, 8, 8, 8)
    with iam_engine.connect() as connection:
        public_ids = connection.execute(
            text(
                "SELECT public_id FROM sch_iam.tbl_organization "
                "UNION ALL SELECT public_id FROM sch_iam.tbl_users"
            )
        ).scalars()
        password_hash = connection.execute(
            text("SELECT password_hash FROM sch_iam.tbl_users LIMIT 1")
        ).scalar_one()
        organization_ids = dict(
            connection.execute(
                text("SELECT slug, public_id FROM sch_iam.tbl_organization")
            )
            .tuples()
            .all()
        )
        user_ids = dict(
            connection.execute(text("SELECT email, public_id FROM sch_iam.tbl_users"))
            .tuples()
            .all()
        )
    assert all(len(str(value)) <= 40 for value in public_ids)
    assert all(
        parse_public_uuid(
            str(value),
            PublicIdPrefix.ORGANIZATION
            if str(value).startswith("org_")
            else PublicIdPrefix.USER,
        )
        for value in public_ids
    )
    assert organization_ids == {
        item["slug"]: seed_demo_iam._public_id("org", item["slug"])
        for item in load_fixture()["organizations"]
    }
    assert user_ids == {
        item["email"]: seed_demo_iam._public_id("usr", item["email"])
        for item in load_fixture()["users"]
    }
    assert PwdlibPasswordHasher().verify("test-only-password", str(password_hash))

    clear_demo(iam_engine)
    clear_demo(iam_engine)
    assert _count(iam_engine, "tbl_organization") == 0


def test_seed_falla_sin_bootstrap_y_no_crea_catalogos_ni_demo(
    iam_engine: Engine,
) -> None:
    with pytest.raises(RuntimeError, match="make backend-bootstrap"):
        seed_demo(iam_engine, "test-only-password", load_fixture())

    assert tuple(
        _count(iam_engine, table)
        for table in (
            "tbl_status",
            "tbl_platform_role",
            "tbl_organization_role",
            "tbl_country",
            "tbl_state",
            "tbl_city",
            "tbl_organization",
            "tbl_users",
        )
    ) == (0, 0, 0, 0, 0, 0, 0, 0)


@pytest.mark.parametrize(
    ("table", "malformed_public_id"),
    [
        ("tbl_organization", "org_demasiado_corto"),
        ("tbl_users", "usr_abcdefghijklmnopqrstu"),
    ],
)
def test_clear_rechaza_ids_publicos_demo_malformados_antes_de_borrar(
    iam_engine: Engine, table: str, malformed_public_id: str
) -> None:
    _seed(iam_engine)
    before = tuple(
        _count(iam_engine, item)
        for item in (
            "tbl_organization",
            "tbl_users",
            "tbl_department",
            "tbl_department_relations",
        )
    )
    with iam_engine.begin() as connection:
        if table == "tbl_organization":
            connection.execute(
                text(
                    "UPDATE sch_iam.tbl_organization SET public_id = :public_id "
                    "WHERE slug = 'demo-acme-soc'"
                ),
                {"public_id": malformed_public_id},
            )
        else:
            connection.execute(
                text(
                    "UPDATE sch_iam.tbl_users SET public_id = :public_id "
                    "WHERE email = 'ana.acme@iam.demo.test'"
                ),
                {"public_id": malformed_public_id},
            )

    with pytest.raises(RuntimeError, match="referencia no demo"):
        clear_demo(iam_engine)

    assert (
        tuple(
            _count(iam_engine, item)
            for item in (
                "tbl_organization",
                "tbl_users",
                "tbl_department",
                "tbl_department_relations",
            )
        )
        == before
    )


def test_seed_concurrente_no_modifica_datos_no_demo(iam_engine: Engine) -> None:
    bootstrap_iam(iam_engine)
    with iam_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_organization "
                "(id_organization, public_id, id_country, id_state, id_city, "
                "id_status, "
                "name, slug, org_address, org_zipcode) "
                "VALUES (900, 'org_external_abcdefghijklmnopqrstuv', 401, 501, 601, "
                "101, 'External', 'external', 'x', 'x')"
            )
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda _: _seed(iam_engine), range(2)))

    assert _count(iam_engine, "tbl_organization") == 7
    with iam_engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT slug FROM sch_iam.tbl_organization "
                    "WHERE id_organization = 900"
                )
            ).scalar_one()
            == "external"
        )


@pytest.mark.parametrize(
    ("statement", "injected_table", "verification"),
    [
        (
            "INSERT INTO sch_iam.tbl_department "
            "(id_department, id_organization, name) SELECT 999, id_organization, "
            "'Demo Extra' FROM sch_iam.tbl_organization "
            "WHERE slug = 'demo-acme-soc'",
            "tbl_department",
            "SELECT id_department FROM sch_iam.tbl_department "
            "WHERE id_department = 999",
        ),
        (
            "INSERT INTO sch_iam.tbl_users (public_id, id_organization, "
            "id_platform_role, id_country, id_state, id_city, id_org_role, id_status, "
            "email, password_hash, first_name, last_name, birthdate, user_address, "
            "user_zipcode) SELECT 'usr_demo_extra', id_organization, 202, 401, 501, "
            "601, 304, 101, 'extra@iam.demo.test', 'x', 'Demo', 'Extra', "
            "'1990-01-01', 'x', 'x' FROM sch_iam.tbl_organization "
            "WHERE slug = 'demo-acme-soc'",
            "tbl_users",
            "SELECT email FROM sch_iam.tbl_users WHERE email = 'extra@iam.demo.test'",
        ),
        (
            "INSERT INTO sch_iam.tbl_department_relations "
            "(id_department_relation, id_department, id_user, id_organization) "
            "SELECT 999, d.id_department, u.id_user, d.id_organization "
            "FROM sch_iam.tbl_department d JOIN sch_iam.tbl_users u "
            "ON u.id_organization = d.id_organization WHERE d.name = 'Demo SOC L2' "
            "AND u.email = 'ana.acme@iam.demo.test'",
            "tbl_department_relations",
            "SELECT id_department_relation FROM sch_iam.tbl_department_relations "
            "WHERE id_department_relation = 999",
        ),
    ],
)
def test_clear_rechaza_dependientes_no_gestionados_sin_borrarlos(
    iam_engine: Engine, statement: str, injected_table: str, verification: str
) -> None:
    _seed(iam_engine)
    before = tuple(
        _count(iam_engine, table)
        for table in (
            "tbl_organization",
            "tbl_users",
            "tbl_department",
            "tbl_department_relations",
        )
    )
    with iam_engine.begin() as connection:
        connection.execute(text(statement))

    with pytest.raises(RuntimeError):
        clear_demo(iam_engine)

    after = tuple(
        _count(iam_engine, table)
        for table in (
            "tbl_organization",
            "tbl_users",
            "tbl_department",
            "tbl_department_relations",
        )
    )
    table_positions = {
        "tbl_organization": 0,
        "tbl_users": 1,
        "tbl_department": 2,
        "tbl_department_relations": 3,
    }
    expected = list(before)
    expected[table_positions[injected_table]] += 1
    assert after == tuple(expected)
    with iam_engine.connect() as connection:
        assert connection.execute(text(verification)).scalar_one_or_none() is not None


@pytest.mark.parametrize(
    ("table", "identifier"),
    [
        *(("tbl_department", identifier) for identifier in range(701, 709)),
        *(("tbl_department_relations", identifier) for identifier in range(801, 809)),
    ],
)
def test_colision_de_ids_demo_fijos_revierte_sin_tocar_filas_ajenas(
    iam_engine: Engine, table: str, identifier: int
) -> None:
    bootstrap_iam(iam_engine)
    with iam_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_organization "
                "(id_organization, public_id, id_country, id_state, id_city, "
                "id_status, "
                "name, slug, org_address, org_zipcode) VALUES "
                "(900, 'org_external_abcdefghijklmnopqrstuv', 401, 501, 601, 101, "
                "'External', 'external', 'x', 'x')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_users "
                "(id_user, public_id, id_organization, id_platform_role, id_country, "
                "id_state, id_city, id_org_role, id_status, email, password_hash, "
                "first_name, last_name, birthdate, user_address, user_zipcode) VALUES "
                "(900, 'usr_external_abcdefghijklmnopqrstuv', 900, 202, 401, 501, "
                "601, 304, 101, 'external@example.test', 'x', 'External', 'User', "
                "'1990-01-01', 'x', 'x')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_department "
                "(id_department, id_organization, name) VALUES (900, 900, 'External')"
            )
        )
        if table == "tbl_department":
            connection.execute(
                text(
                    "INSERT INTO sch_iam.tbl_department "
                    "(id_department, id_organization, name) VALUES "
                    "(:identifier, 900, 'Collision')"
                ),
                {"identifier": identifier},
            )
        else:
            connection.execute(
                text(
                    "INSERT INTO sch_iam.tbl_department_relations "
                    "(id_department_relation, id_department, id_user, id_organization) "
                    "VALUES (:identifier, 900, 900, 900)"
                ),
                {"identifier": identifier},
            )

    with pytest.raises(RuntimeError, match="Colisión de identificador interno demo"):
        _seed(iam_engine)

    assert _count(iam_engine, "tbl_organization") == 1
    collision_queries = {
        "tbl_department": text(
            "SELECT count(*) FROM sch_iam.tbl_department "
            "WHERE id_department = :identifier"
        ),
        "tbl_department_relations": text(
            "SELECT count(*) FROM sch_iam.tbl_department_relations "
            "WHERE id_department_relation = :identifier"
        ),
    }
    with iam_engine.connect() as connection:
        assert (
            connection.execute(
                collision_queries[table], {"identifier": identifier}
            ).scalar_one()
            == 1
        )


def test_clear_rechaza_fk_desde_esquema_externo_sin_borrar_demo(
    iam_engine: Engine,
) -> None:
    _seed(iam_engine)
    try:
        with iam_engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA test_demo_external_dependency"))
            connection.execute(
                text(
                    "CREATE TABLE test_demo_external_dependency.tbl_users "
                    "(id bigint primary key, "
                    "organization_id bigint references "
                    "sch_iam.tbl_organization(id_organization))"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO test_demo_external_dependency.tbl_users "
                    "(id, organization_id) "
                    "SELECT 1, id_organization FROM sch_iam.tbl_organization "
                    "WHERE slug = 'demo-acme-soc'"
                )
            )
    except SQLAlchemyError:
        pytest.skip("El rol de prueba no puede crear esquemas externos.")
    try:
        with pytest.raises(RuntimeError, match="dependencia futura"):
            clear_demo(iam_engine)
        assert _count(iam_engine, "tbl_organization") == 6
        with iam_engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT count(*) FROM test_demo_external_dependency.tbl_users")
                ).scalar_one()
                == 1
            )
    finally:
        with iam_engine.begin() as connection:
            connection.execute(
                text("DROP SCHEMA IF EXISTS test_demo_external_dependency CASCADE")
            )


def test_clear_rechaza_fk_futura(iam_engine: Engine) -> None:
    _seed(iam_engine)
    with iam_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE sch_iam.test_demo_future_dependency "
                "(id bigint primary key, organization_id bigint references "
                "sch_iam.tbl_organization(id_organization))"
            )
        )
    try:
        with pytest.raises(RuntimeError, match="dependencia futura"):
            clear_demo(iam_engine)
        assert _count(iam_engine, "tbl_organization") == 6
    finally:
        with iam_engine.begin() as connection:
            connection.execute(text("DROP TABLE sch_iam.test_demo_future_dependency"))


def test_bootstrap_concurrente_no_duplica_catalogos(iam_engine: Engine) -> None:
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: bootstrap_iam(iam_engine), range(2)))

    assert sum(result.created for result in results) == 18
    assert _count(iam_engine, "tbl_status") == 3
    assert _count(iam_engine, "tbl_platform_role") == 2
    assert _count(iam_engine, "tbl_organization_role") == 4


def test_bootstrap_y_seed_resuelven_catalogos_por_clave_natural(
    iam_engine: Engine,
) -> None:
    with iam_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_status (id_status, status) "
                "VALUES (999, 'active'), (101, 'UNRELATED')"
            )
        )

    bootstrap_iam(iam_engine)
    seed_demo(iam_engine, "test-only-password", load_fixture())

    assert _count(iam_engine, "tbl_organization") == 6
    assert _count(iam_engine, "tbl_users") == 8
    with iam_engine.connect() as connection:
        statuses = (
            connection.execute(
                text(
                    "SELECT id_status, status FROM sch_iam.tbl_status "
                    "WHERE lower(status) IN ('active', 'unrelated') ORDER BY id_status"
                )
            )
            .tuples()
            .all()
        )
        organization_statuses = (
            connection.execute(
                text(
                    "SELECT DISTINCT id_status FROM sch_iam.tbl_organization "
                    "ORDER BY id_status"
                )
            )
            .scalars()
            .all()
        )

    assert statuses == [(101, "UNRELATED"), (999, "active")]
    assert organization_statuses == [999]


def test_colision_de_id_reservado_ausente_aborta_bootstrap_atomicamente(
    iam_engine: Engine,
) -> None:
    with iam_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO sch_iam.tbl_status (id_status, status) "
                "VALUES (101, 'UNRELATED')"
            )
        )

    catalog_tables = (
        "tbl_status",
        "tbl_platform_role",
        "tbl_organization_role",
        "tbl_country",
        "tbl_state",
        "tbl_city",
    )
    before = tuple(_count(iam_engine, table) for table in catalog_tables)

    with pytest.raises(RuntimeError):
        bootstrap_iam(iam_engine)

    assert tuple(_count(iam_engine, table) for table in catalog_tables) == before


def test_error_de_seed_revierte_la_eliminacion_previa(
    iam_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed(iam_engine)
    tables = (
        "tbl_organization",
        "tbl_users",
        "tbl_department",
        "tbl_department_relations",
    )
    before = tuple(_count(iam_engine, table) for table in tables)

    def fail_organization_insert(
        connection: Connection,
        item: Organization,
        country: int,
        state: int,
        city: int,
        active: int,
    ) -> int:
        del item, country, state, city, active
        assert tuple(
            int(connection.execute(COUNT_STATEMENTS[table]).scalar_one())
            for table in tables
        ) == (0, 0, 0, 0)
        raise IntegrityError(
            "Fallo de escritura forzado durante el seed demo.",
            {},
            RuntimeError("Fallo de escritura forzado."),
        )

    monkeypatch.setattr(seed_demo_iam, "_upsert_organization", fail_organization_insert)

    with pytest.raises(IntegrityError, match="Fallo de escritura forzado"):
        seed_demo(iam_engine, "test-only-password", load_fixture())

    assert tuple(_count(iam_engine, table) for table in tables) == before
