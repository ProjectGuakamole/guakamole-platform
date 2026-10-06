from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal, TypedDict, cast

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.engine import URL, Connection, make_url
from sqlalchemy.exc import SQLAlchemyError

IAM_SCHEMA = "sch_iam"
FIXTURE_PATH = Path(__file__).parent / "data" / "iam_demo_seed.json"
DEMO_HASH_PLACEHOLDER = "argon2id-demo-placeholder-not-valid"
REQUIRED_TABLES = (
    "tbl_status",
    "tbl_platform_role",
    "tbl_organization_role",
    "tbl_country",
    "tbl_state",
    "tbl_city",
    "tbl_organization",
    "tbl_users",
    "tbl_department",
    "tbl_department_relations",
)
ID_LOOKUPS = {
    ("tbl_status", "status", "id_status"): (
        "SELECT id_status FROM sch_iam.tbl_status WHERE status = :value"
    ),
    ("tbl_platform_role", "platform_role_type", "id_platform_role"): (
        """
        SELECT id_platform_role
        FROM sch_iam.tbl_platform_role
        WHERE platform_role_type = :value
        """
    ),
    ("tbl_organization", "slug", "id_organization"): (
        """
        SELECT id_organization
        FROM sch_iam.tbl_organization
        WHERE slug = :value
        """
    ),
    ("tbl_organization_role", "org_role_type", "id_org_role"): (
        """
        SELECT id_org_role
        FROM sch_iam.tbl_organization_role
        WHERE org_role_type = :value
        """
    ),
}


class OrganizationFixture(TypedDict):
    slug: str
    name: str
    tax: str
    zipcode: str


class UserFixture(TypedDict):
    email: str
    first_name: str
    last_name: str
    organization_slug: str
    org_role: str


class DepartmentFixture(TypedDict):
    name: str
    organization_slug: str


class DepartmentRelationFixture(TypedDict):
    department_name: str
    user_email: str


class StatusFixture(TypedDict):
    status: str


class PlatformRoleFixture(TypedDict):
    platform_role_type: str
    description: str


class OrganizationRoleFixture(TypedDict):
    org_role_type: str


class CountryFixture(TypedDict):
    country_name: str


class StateFixture(TypedDict):
    state_name: str
    country_name: str


class CityFixture(TypedDict):
    city_name: str
    state_name: str


class DemoFixture(TypedDict):
    statuses: list[StatusFixture]
    platform_roles: list[PlatformRoleFixture]
    organization_roles: list[OrganizationRoleFixture]
    countries: list[CountryFixture]
    states: list[StateFixture]
    cities: list[CityFixture]
    organizations: list[OrganizationFixture]
    users: list[UserFixture]
    departments: list[DepartmentFixture]
    department_relations: list[DepartmentRelationFixture]


@dataclass(frozen=True)
class OperationStats:
    created: int = 0
    updated: int = 0
    deleted: int = 0


@dataclass(frozen=True)
class SeedResult:
    statuses: OperationStats
    platform_roles: OperationStats
    organization_roles: OperationStats
    countries: OperationStats
    states: OperationStats
    cities: OperationStats
    organizations: OperationStats
    users: OperationStats
    departments: OperationStats
    department_relations: OperationStats


def validate_database_url(raw_url: str | None) -> URL:
    if raw_url is None or raw_url.strip() == "":
        raise ValueError("DATABASE_URL no está definida en el entorno.")
    url = make_url(raw_url)
    if url.get_backend_name() != "postgresql":
        raise ValueError(
            "DATABASE_URL debe usar PostgreSQL; ejecuta el seed contra PostgreSQL real."
        )
    return url


def load_fixture(path: Path = FIXTURE_PATH) -> DemoFixture:
    with path.open(encoding="utf-8") as file:
        raw_data = json.load(file)
    if not isinstance(raw_data, dict):
        raise ValueError("El fixture demo IAM debe ser un objeto JSON.")
    data = cast(DemoFixture, raw_data)
    validate_fixture(data)
    return data


def validate_fixture(data: DemoFixture) -> None:
    catalog_keys: tuple[
        Literal[
            "statuses",
            "platform_roles",
            "organization_roles",
            "countries",
            "states",
            "cities",
        ],
        ...,
    ] = (
        "statuses",
        "platform_roles",
        "organization_roles",
        "countries",
        "states",
        "cities",
    )
    for key in catalog_keys:
        catalog_values = data[key]
        if not isinstance(catalog_values, list) or not 3 <= len(catalog_values) <= 10:
            raise ValueError(
                f"El fixture debe contener entre 3 y 10 elementos en {key}."
            )
    operational_keys: tuple[
        Literal["organizations", "users", "departments", "department_relations"],
        ...,
    ] = ("organizations", "users", "departments", "department_relations")
    for operational_key in operational_keys:
        operational_values = data[operational_key]
        if (
            not isinstance(operational_values, list)
            or not 5 <= len(operational_values) <= 10
        ):
            raise ValueError(
                f"El fixture debe contener entre 5 y 10 elementos en {operational_key}."
            )
    organization_slugs = {
        organization["slug"] for organization in data["organizations"]
    }
    for organization in data["organizations"]:
        if not organization["slug"].startswith("demo-"):
            raise ValueError(
                "Todos los slugs de organización demo deben empezar por demo-."
            )
        if not organization["name"].startswith("Demo"):
            raise ValueError(
                "Todos los nombres de organización demo deben empezar por Demo."
            )
    for user in data["users"]:
        if not user["email"].endswith(".demo.test"):
            raise ValueError("Todos los emails demo deben terminar en .demo.test.")
        if not user["first_name"].startswith("Demo"):
            raise ValueError(
                "Todos los nombres de usuario demo deben empezar por Demo."
            )
        if user["organization_slug"] not in organization_slugs:
            raise ValueError(
                "Cada usuario demo debe referenciar una organización existente."
            )
    for department in data["departments"]:
        if not department["name"].startswith("Demo "):
            raise ValueError("Todos los departamentos demo deben empezar por 'Demo '.")
        if department["organization_slug"] not in organization_slugs:
            raise ValueError(
                "Cada departamento demo debe referenciar una organización existente."
            )
    validate_relation_scope(data)


def validate_relation_scope(data: DemoFixture) -> None:
    departments_by_name = {
        department["name"]: department["organization_slug"]
        for department in data["departments"]
    }
    users_by_email = {
        user["email"]: user["organization_slug"] for user in data["users"]
    }
    for relation in data["department_relations"]:
        department_org = departments_by_name.get(relation["department_name"])
        user_org = users_by_email.get(relation["user_email"])
        if department_org is None or user_org is None:
            raise ValueError(
                "Las relaciones demo deben referenciar usuarios y departamentos "
                "existentes."
            )
        if department_org != user_org:
            raise ValueError(
                "Cada relación demo debe conectar usuario y departamento de la "
                "misma organización."
            )


def truncate_tables() -> tuple[str, ...]:
    return REQUIRED_TABLES


def build_truncate_statement() -> str:
    tables = ", ".join(f"{IAM_SCHEMA}.{table}" for table in truncate_tables())
    return f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"


def build_engine(url: URL) -> Engine:
    return create_engine(url, hide_parameters=True)


def assert_schema_ready(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_schema(IAM_SCHEMA):
        raise RuntimeError(
            "No existe el schema sch_iam. Ejecuta: uv run alembic upgrade head"
        )
    missing = [
        table
        for table in REQUIRED_TABLES
        if not inspector.has_table(table, schema=IAM_SCHEMA)
    ]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Faltan tablas IAM ({joined}). Ejecuta: uv run alembic upgrade head"
        )


def seed_demo(engine: Engine, fixture: DemoFixture) -> SeedResult:
    assert_schema_ready(engine)
    with engine.begin() as connection:
        truncate_iam(connection)
        status_stats = insert_statuses(connection, fixture["statuses"])
        platform_role_stats = insert_platform_roles(
            connection, fixture["platform_roles"]
        )
        org_role_stats = insert_organization_roles(
            connection, fixture["organization_roles"]
        )
        country_stats = insert_countries(connection, fixture["countries"])
        state_stats = insert_states(connection, fixture["states"])
        city_stats = insert_cities(connection, fixture["cities"])
        geo = load_first_geo(connection)
        active_status = scalar_id(
            connection, "tbl_status", "status", "ACTIVE", "id_status"
        )
        user_role = scalar_id(
            connection,
            "tbl_platform_role",
            "platform_role_type",
            "USER",
            "id_platform_role",
        )

        org_stats = upsert_organizations(
            connection, fixture["organizations"], geo, active_status
        )
        user_stats = upsert_users(
            connection, fixture["users"], geo, active_status, user_role
        )
        dept_stats = upsert_departments(connection, fixture["departments"])
        relation_stats = upsert_relations(connection, fixture["department_relations"])
    return SeedResult(
        status_stats,
        platform_role_stats,
        org_role_stats,
        country_stats,
        state_stats,
        city_stats,
        org_stats,
        user_stats,
        dept_stats,
        relation_stats,
    )


def clear_demo(engine: Engine) -> SeedResult:
    assert_schema_ready(engine)
    with engine.begin() as connection:
        truncate_iam(connection)
    empty = OperationStats(deleted=0)
    return SeedResult(
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
        empty,
    )


def truncate_iam(connection: Connection) -> None:
    connection.execute(text(build_truncate_statement()))


def load_first_geo(connection: Connection) -> Mapping[str, object]:
    geo = (
        connection.execute(
            text("""
            SELECT c.id_country, s.id_state, ci.id_city
            FROM sch_iam.tbl_country c
            JOIN sch_iam.tbl_state s ON s.id_country = c.id_country
            JOIN sch_iam.tbl_city ci ON ci.id_state = s.id_state
            ORDER BY ci.id_city
            LIMIT 1
            """),
        )
        .mappings()
        .one()
    )
    return cast(Mapping[str, object], geo)


def insert_statuses(
    connection: Connection, statuses: list[StatusFixture]
) -> OperationStats:
    for index, item in enumerate(statuses, start=1):
        connection.execute(
            text(
                """
                INSERT INTO sch_iam.tbl_status (id_status, status)
                VALUES (:id, :status)
                """
            ),
            {"id": index, "status": item["status"]},
        )
    return OperationStats(created=len(statuses))


def insert_platform_roles(
    connection: Connection, roles: list[PlatformRoleFixture]
) -> OperationStats:
    for index, item in enumerate(roles, start=1):
        connection.execute(
            text("""
            INSERT INTO sch_iam.tbl_platform_role
            (id_platform_role, platform_role_type, description)
            VALUES (:id, :role, :description)
            """),
            {
                "id": index,
                "role": item["platform_role_type"],
                "description": item["description"],
            },
        )
    return OperationStats(created=len(roles))


def insert_organization_roles(
    connection: Connection, roles: list[OrganizationRoleFixture]
) -> OperationStats:
    for index, item in enumerate(roles, start=1):
        connection.execute(
            text("""
            INSERT INTO sch_iam.tbl_organization_role (id_org_role, org_role_type)
            VALUES (:id, :role)
            """),
            {"id": index, "role": item["org_role_type"]},
        )
    return OperationStats(created=len(roles))


def insert_countries(
    connection: Connection, countries: list[CountryFixture]
) -> OperationStats:
    for index, item in enumerate(countries, start=1):
        connection.execute(
            text("""
            INSERT INTO sch_iam.tbl_country (id_country, country_name)
            VALUES (:id, :name)
            """),
            {"id": index, "name": item["country_name"]},
        )
    return OperationStats(created=len(countries))


def insert_states(connection: Connection, states: list[StateFixture]) -> OperationStats:
    for index, item in enumerate(states, start=1):
        country_id = connection.execute(
            text(
                "SELECT id_country FROM sch_iam.tbl_country WHERE country_name = :name"
            ),
            {"name": item["country_name"]},
        ).scalar_one()
        connection.execute(
            text("""
            INSERT INTO sch_iam.tbl_state (id_state, id_country, state_name)
            VALUES (:id, :country_id, :name)
            """),
            {"id": index, "country_id": country_id, "name": item["state_name"]},
        )
    return OperationStats(created=len(states))


def insert_cities(connection: Connection, cities: list[CityFixture]) -> OperationStats:
    for index, item in enumerate(cities, start=1):
        state_id = connection.execute(
            text("SELECT id_state FROM sch_iam.tbl_state WHERE state_name = :name"),
            {"name": item["state_name"]},
        ).scalar_one()
        connection.execute(
            text("""
            INSERT INTO sch_iam.tbl_city (id_city, id_state, city_name)
            VALUES (:id, :state_id, :name)
            """),
            {"id": index, "state_id": state_id, "name": item["city_name"]},
        )
    return OperationStats(created=len(cities))


def scalar_id(
    connection: Connection,
    table: str,
    key: str,
    value: str,
    id_column: str,
) -> int:
    lookup = ID_LOOKUPS.get((table, key, id_column))
    if lookup is None:
        raise ValueError("Lookup IAM no permitido para el seed demo.")
    result = connection.execute(
        text(lookup),
        {"value": value},
    ).scalar_one_or_none()
    if result is None:
        raise RuntimeError(f"Falta catálogo IAM requerido: {table}.{key}={value}")
    return int(result)


def upsert_organizations(
    connection: Connection,
    organizations: list[OrganizationFixture],
    geo: Mapping[str, object],
    status_id: int,
) -> OperationStats:
    created = 0
    updated = 0
    next_pk = int(
        connection.execute(
            text(
                """
                SELECT COALESCE(MAX(id_organization), 0) + 1
                FROM sch_iam.tbl_organization
                """
            )
        ).scalar_one()
    )
    geo_map = cast(Mapping[str, int], geo)
    for item in organizations:
        existing = connection.execute(
            text(
                """
                SELECT id_organization
                FROM sch_iam.tbl_organization
                WHERE slug = :slug
                """
            ),
            {"slug": item["slug"]},
        ).scalar_one_or_none()
        params = {
            "id": existing or next_pk,
            "id_country": geo_map["id_country"],
            "id_state": geo_map["id_state"],
            "id_city": geo_map["id_city"],
            "id_status": status_id,
            "name": item["name"],
            "slug": item["slug"],
            "registered": f"{item['name']} SL Demo",
            "tax": item["tax"],
            "address": f"Demo Calle Seguridad {item['zipcode']}",
            "zipcode": item["zipcode"],
        }
        if existing is None:
            connection.execute(
                text("""
                INSERT INTO sch_iam.tbl_organization
                (id_organization, id_country, id_state, id_city, id_status, name, slug,
                 org_registered_name, org_tax, org_address, org_zipcode)
                VALUES (:id, :id_country, :id_state, :id_city, :id_status, :name, :slug,
                        :registered, :tax, :address, :zipcode)
            """),
                params,
            )
            created += 1
            next_pk += 1
        else:
            connection.execute(
                text("""
                UPDATE sch_iam.tbl_organization
                SET name=:name, id_status=:id_status, org_registered_name=:registered,
                    org_tax=:tax, org_address=:address, org_zipcode=:zipcode,
                    update_at=NOW()
                WHERE slug=:slug
            """),
                params,
            )
            updated += 1
    return OperationStats(created=created, updated=updated)


def upsert_users(
    connection: Connection,
    users: list[UserFixture],
    geo: Mapping[str, object],
    status_id: int,
    platform_role_id: int,
) -> OperationStats:
    created = 0
    updated = 0
    next_pk = int(
        connection.execute(
            text("SELECT COALESCE(MAX(id_user), 0) + 1 FROM sch_iam.tbl_users")
        ).scalar_one()
    )
    geo_map = cast(Mapping[str, int], geo)
    for item in users:
        organization_id = scalar_id(
            connection,
            "tbl_organization",
            "slug",
            item["organization_slug"],
            "id_organization",
        )
        org_role_id = scalar_id(
            connection,
            "tbl_organization_role",
            "org_role_type",
            item["org_role"],
            "id_org_role",
        )
        existing = connection.execute(
            text("SELECT id_user FROM sch_iam.tbl_users WHERE email = :email"),
            {"email": item["email"]},
        ).scalar_one_or_none()
        params = {
            "id": existing or next_pk,
            "id_organization": organization_id,
            "id_platform_role": platform_role_id,
            "id_country": geo_map["id_country"],
            "id_state": geo_map["id_state"],
            "id_city": geo_map["id_city"],
            "id_org_role": org_role_id,
            "id_status": status_id,
            "email": item["email"],
            "password_hash": DEMO_HASH_PLACEHOLDER,
            "first_name": item["first_name"],
            "last_name": item["last_name"],
            "birthdate": date(1990, 1, 1),
            "address": "Demo Avenida IAM 1",
            "zipcode": "08001",
        }
        if existing is None:
            connection.execute(
                text("""
                INSERT INTO sch_iam.tbl_users
                (id_user, id_organization, id_platform_role, id_country, id_state,
                 id_city, id_org_role, id_status, email, password_hash, first_name,
                 last_name, birthdate, user_address, user_zipcode)
                VALUES (:id, :id_organization, :id_platform_role, :id_country,
                        :id_state, :id_city, :id_org_role, :id_status, :email,
                        :password_hash, :first_name, :last_name, :birthdate,
                        :address, :zipcode)
            """),
                params,
            )
            created += 1
            next_pk += 1
        else:
            connection.execute(
                text("""
                UPDATE sch_iam.tbl_users
                SET id_organization=:id_organization, id_org_role=:id_org_role,
                    id_status=:id_status, password_hash=:password_hash,
                    first_name=:first_name, last_name=:last_name, update_at=NOW()
                WHERE email=:email
            """),
                params,
            )
            updated += 1
    return OperationStats(created=created, updated=updated)


def upsert_departments(
    connection: Connection,
    departments: list[DepartmentFixture],
) -> OperationStats:
    created = 0
    updated = 0
    next_pk = int(
        connection.execute(
            text(
                "SELECT COALESCE(MAX(id_department), 0) + 1 FROM sch_iam.tbl_department"
            )
        ).scalar_one()
    )
    for item in departments:
        organization_id = scalar_id(
            connection,
            "tbl_organization",
            "slug",
            item["organization_slug"],
            "id_organization",
        )
        existing = connection.execute(
            text("""
            SELECT id_department FROM sch_iam.tbl_department
            WHERE id_organization = :org AND name = :name
        """),
            {"org": organization_id, "name": item["name"]},
        ).scalar_one_or_none()
        params = {
            "id": existing or next_pk,
            "org": organization_id,
            "name": item["name"],
            "description": f"{item['name']} temporal para demo IAM",
        }
        if existing is None:
            connection.execute(
                text("""
                INSERT INTO sch_iam.tbl_department
                (id_department, id_organization, name, description)
                VALUES (:id, :org, :name, :description)
            """),
                params,
            )
            created += 1
            next_pk += 1
        else:
            connection.execute(
                text("""
                UPDATE sch_iam.tbl_department
                SET description=:description, update_at=NOW()
                WHERE id_department=:id
            """),
                params,
            )
            updated += 1
    return OperationStats(created=created, updated=updated)


def upsert_relations(
    connection: Connection,
    relations: list[DepartmentRelationFixture],
) -> OperationStats:
    created = 0
    updated = 0
    next_pk = int(
        connection.execute(
            text(
                """
                SELECT COALESCE(MAX(id_department_relation), 0) + 1
                FROM sch_iam.tbl_department_relations
                """
            )
        ).scalar_one()
    )
    for item in relations:
        user = (
            connection.execute(
                text(
                    """
                    SELECT id_user, id_organization
                    FROM sch_iam.tbl_users
                    WHERE email = :email
                    """
                ),
                {"email": item["user_email"]},
            )
            .mappings()
            .one()
        )
        department_id = connection.execute(
            text("""
            SELECT id_department FROM sch_iam.tbl_department
            WHERE name = :name AND id_organization = :org
        """),
            {"name": item["department_name"], "org": user["id_organization"]},
        ).scalar_one()
        existing = connection.execute(
            text("""
            SELECT id_department_relation FROM sch_iam.tbl_department_relations
            WHERE id_department = :department AND id_user = :user
        """),
            {"department": department_id, "user": user["id_user"]},
        ).scalar_one_or_none()
        if existing is None:
            connection.execute(
                text("""
                INSERT INTO sch_iam.tbl_department_relations
                (id_department_relation, id_department, id_user)
                VALUES (:id, :department, :user)
            """),
                {"id": next_pk, "department": department_id, "user": user["id_user"]},
            )
            created += 1
            next_pk += 1
        else:
            connection.execute(
                text(
                    """
                    UPDATE sch_iam.tbl_department_relations
                    SET update_at=NOW()
                    WHERE id_department_relation=:id
                    """
                ),
                {"id": existing},
            )
            updated += 1
    return OperationStats(created=created, updated=updated)


def print_result(result: SeedResult, mode: Literal["seed", "clear"]) -> None:
    action = "eliminadas" if mode == "clear" else "creadas/actualizadas"
    print(format_stats("Estados", action, result.statuses))
    print(format_stats("Roles plataforma", action, result.platform_roles))
    print(format_stats("Roles organización", action, result.organization_roles))
    print(format_stats("Países", action, result.countries))
    print(format_stats("Provincias/estados", action, result.states))
    print(format_stats("Ciudades", action, result.cities))
    print(format_stats("Organizaciones", action, result.organizations))
    print(format_stats("Usuarios", action, result.users))
    print(format_stats("Departamentos", action, result.departments))
    print(format_stats("Relaciones", action, result.department_relations))


def format_stats(label: str, action: str, stats: OperationStats) -> str:
    return (
        f"{label} {action}: {stats.created}/{stats.updated}; "
        f"eliminadas: {stats.deleted}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "DESTRUCTIVO: trunca sch_iam gestionado por el seed demo IAM antes de "
            "insertar datos en PostgreSQL."
        )
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help=(
            "DESTRUCTIVO: trunca las tablas IAM gestionadas en sch_iam y no inserta "
            "datos demo. Requiere --yes."
        ),
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help=(
            "Confirma la acción destructiva: TRUNCATE sch_iam con "
            "RESTART IDENTITY CASCADE."
        ),
    )
    return parser.parse_args()


def require_destructive_confirmation(confirmed: bool) -> None:
    if confirmed:
        return
    raise RuntimeError(
        "DESTRUCTIVO: truncará sch_iam. Ejecuta de nuevo con --yes si "
        "quieres continuar."
    )


def main() -> int:
    args = parse_args()
    try:
        require_destructive_confirmation(bool(args.yes))
        url = validate_database_url(os.getenv("DATABASE_URL"))
        engine = build_engine(url)
        print("DESTRUCTIVO: truncará sch_iam gestionado por el seed demo IAM.")
        if args.clear:
            print_result(clear_demo(engine), "clear")
        else:
            print_result(seed_demo(engine, load_fixture()), "seed")
    except (ValueError, RuntimeError, SQLAlchemyError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
