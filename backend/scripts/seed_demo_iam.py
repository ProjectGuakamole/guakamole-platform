"""Carga o elimina exclusivamente la demo IAM bajo confirmación explícita."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from base64 import urlsafe_b64encode
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import TypedDict, cast

from alembic.util.exc import CommandError
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.iam_bootstrap import (
    assert_baseline_schema,
    assert_canonical_bootstrap_catalogs,
)
from app.core.iam_rebaseline import validate_safe_target
from app.domains.auth.shared.password_hasher import PwdlibPasswordHasher
from app.domains.auth.shared.public_ids import PublicIdPrefix, parse_public_uuid

FIXTURE_PATH = Path(__file__).parent / "data" / "iam_demo_seed.json"
DEMO_PUBLIC_ID_NAMESPACE = uuid.UUID("8d86c76e-5903-5647-b9ec-70c93f99a8c4")

ForeignKeyContract = tuple[str, str, str, str, str, str]

EXPECTED_DEMO_FOREIGN_KEYS: frozenset[ForeignKeyContract] = frozenset(
    {
        (
            "sch_iam",
            "tbl_users",
            "id_organization",
            "sch_iam",
            "tbl_organization",
            "id_organization",
        ),
        (
            "sch_iam",
            "tbl_department",
            "id_organization",
            "sch_iam",
            "tbl_organization",
            "id_organization",
        ),
        (
            "sch_iam",
            "tbl_department_relations",
            "id_department,id_organization",
            "sch_iam",
            "tbl_department",
            "id_department,id_organization",
        ),
        (
            "sch_iam",
            "tbl_department_relations",
            "id_user,id_organization",
            "sch_iam",
            "tbl_users",
            "id_user,id_organization",
        ),
    }
)


class Organization(TypedDict):
    slug: str
    name: str
    tax: str
    zipcode: str


class User(TypedDict):
    email: str
    first_name: str
    last_name: str
    organization_slug: str
    org_role: str


class Department(TypedDict):
    name: str
    organization_slug: str


class Relation(TypedDict):
    department_name: str
    user_email: str


class Fixture(TypedDict):
    organizations: list[Organization]
    users: list[User]
    departments: list[Department]
    department_relations: list[Relation]


def load_fixture(path: Path = FIXTURE_PATH) -> Fixture:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("El fixture demo IAM no es legible.") from error
    if not isinstance(raw, dict):
        raise ValueError("El fixture demo IAM debe ser un objeto.")
    collection_names = (
        "organizations",
        "users",
        "departments",
        "department_relations",
    )
    if any(not isinstance(raw.get(name), list) for name in collection_names):
        raise ValueError("El fixture demo tiene colecciones inválidas.")
    fixture = cast(Fixture, raw)
    validate_fixture(fixture)
    return fixture


def validate_fixture(fixture: Fixture) -> None:
    if (
        len(fixture["organizations"]),
        len(fixture["users"]),
        len(fixture["departments"]),
        len(fixture["department_relations"]),
    ) != (6, 8, 8, 8):
        raise ValueError("El fixture demo debe contener exactamente 6/8/8/8 registros.")
    organizations = fixture["organizations"]
    users = fixture["users"]
    departments = fixture["departments"]
    relations = fixture["department_relations"]
    _require_fields(organizations, ("slug", "name", "tax", "zipcode"))
    _require_fields(
        users, ("email", "first_name", "last_name", "organization_slug", "org_role")
    )
    _require_fields(departments, ("name", "organization_slug"))
    _require_fields(relations, ("department_name", "user_email"))
    slugs = _unique(organizations, "slug", "slugs de organización")
    _unique(users, "email", "emails de usuario")
    department_keys = {
        (item["organization_slug"], item["name"]) for item in departments
    }
    if len(department_keys) != len(departments):
        raise ValueError("Los departamentos demo deben ser únicos por organización.")
    if any(
        not item["slug"].startswith("demo-") or not item["name"].startswith("Demo ")
        for item in organizations
    ):
        raise ValueError("Las organizaciones deben pertenecer al espacio demo exacto.")
    if any(
        not item["email"].endswith(".demo.test")
        or not item["first_name"].startswith("Demo ")
        for item in users
    ):
        raise ValueError("Los usuarios deben pertenecer al espacio demo exacto.")
    if any(not item["name"].startswith("Demo ") for item in departments):
        raise ValueError("Los departamentos deben pertenecer al espacio demo exacto.")
    if any(item["organization_slug"] not in slugs for item in users) or any(
        item["organization_slug"] not in slugs for item in departments
    ):
        raise ValueError("Las referencias de organización demo deben existir.")
    users_by_email = {item["email"]: item["organization_slug"] for item in users}
    departments_by_name = {
        item["name"]: item["organization_slug"] for item in departments
    }
    relation_keys = {
        (item["department_name"], item["user_email"]) for item in relations
    }
    if len(relation_keys) != len(relations):
        raise ValueError("Las relaciones demo deben ser únicas.")
    for relation in relations:
        department_org = departments_by_name.get(relation["department_name"])
        user_org = users_by_email.get(relation["user_email"])
        if department_org is None or user_org is None:
            raise ValueError(
                "Las relaciones demo deben referenciar entidades existentes."
            )
        if department_org != user_org:
            raise ValueError(
                "Las relaciones demo deben mantener la misma organización."
            )


def _require_fields(
    records: Sequence[Mapping[str, object]], fields: tuple[str, ...]
) -> None:
    if any(
        not isinstance(record, dict)
        or any(
            not isinstance(record.get(field), str) or not record[field]
            for field in fields
        )
        for record in records
    ):
        raise ValueError("El fixture demo contiene registros inválidos.")


def _unique(
    records: Sequence[Mapping[str, object]], field: str, label: str
) -> set[str]:
    values = {str(record[field]) for record in records}
    if len(values) != len(records):
        raise ValueError(f"El fixture demo contiene {label} duplicados.")
    return values


def seed_demo(engine: Engine, password: str, fixture: Fixture | None = None) -> None:
    data = fixture or load_fixture()
    validate_fixture(data)
    assert_baseline_schema(engine)
    with engine.begin() as connection:
        assert_canonical_bootstrap_catalogs(connection)
        _replace_demo(connection, data, password)


def clear_demo(engine: Engine, fixture: Fixture | None = None) -> None:
    data = fixture or load_fixture()
    validate_fixture(data)
    assert_baseline_schema(engine)
    with engine.begin() as connection:
        assert_canonical_bootstrap_catalogs(connection)
        _delete_demo(connection, data)


def _replace_demo(connection: Connection, fixture: Fixture, password: str) -> None:
    _delete_demo(connection, fixture)
    country, state, city = _geo(connection)
    active = _catalog_id(connection, "tbl_status", "id_status", "status", "ACTIVE")
    platform = _catalog_id(
        connection,
        "tbl_platform_role",
        "id_platform_role",
        "platform_role_type",
        "USER",
    )
    organizations = {
        item["slug"]: _upsert_organization(
            connection, item, country, state, city, active
        )
        for item in fixture["organizations"]
    }
    password_hash = PwdlibPasswordHasher().hash(password)
    users = {
        item["email"]: _upsert_user(
            connection,
            item,
            organizations[item["organization_slug"]],
            country,
            state,
            city,
            active,
            platform,
            password_hash,
        )
        for item in fixture["users"]
    }
    departments = {
        item["name"]: _upsert_department(
            connection, item, organizations[item["organization_slug"]], 700 + index
        )
        for index, item in enumerate(fixture["departments"], 1)
    }
    for index, relation in enumerate(fixture["department_relations"], 1):
        _upsert_relation(
            connection,
            800 + index,
            departments[relation["department_name"]],
            users[relation["user_email"]],
        )


def _delete_demo(connection: Connection, fixture: Fixture) -> None:
    _assert_contained(connection, fixture)
    slugs = [item["slug"] for item in fixture["organizations"]]
    connection.execute(
        text(
            "DELETE FROM sch_iam.tbl_department_relations WHERE id_organization IN (SELECT id_organization FROM sch_iam.tbl_organization WHERE slug = ANY(:slugs))"
        ),
        {"slugs": slugs},
    )
    connection.execute(
        text(
            "DELETE FROM sch_iam.tbl_department WHERE id_organization IN (SELECT id_organization FROM sch_iam.tbl_organization WHERE slug = ANY(:slugs))"
        ),
        {"slugs": slugs},
    )
    connection.execute(
        text(
            "DELETE FROM sch_iam.tbl_users WHERE id_organization IN (SELECT id_organization FROM sch_iam.tbl_organization WHERE slug = ANY(:slugs))"
        ),
        {"slugs": slugs},
    )
    connection.execute(
        text("DELETE FROM sch_iam.tbl_organization WHERE slug = ANY(:slugs)"),
        {"slugs": slugs},
    )


def _assert_contained(connection: Connection, fixture: Fixture) -> None:
    slugs = [item["slug"] for item in fixture["organizations"]]
    emails = [item["email"] for item in fixture["users"]]
    expected_organizations = {
        (item["slug"], item["name"], item["tax"], item["zipcode"])
        for item in fixture["organizations"]
    }
    expected_users = {
        (item["email"], item["organization_slug"]) for item in fixture["users"]
    }
    expected_departments = {
        (item["organization_slug"], item["name"]) for item in fixture["departments"]
    }
    expected_relations = {
        (
            department["organization_slug"],
            relation["department_name"],
            relation["user_email"],
        )
        for relation in fixture["department_relations"]
        for department in fixture["departments"]
        if department["name"] == relation["department_name"]
    }
    extra_namespace = connection.execute(
        text(
            "SELECT 1 FROM sch_iam.tbl_organization WHERE slug LIKE 'demo-%' AND NOT (slug = ANY(:slugs))"
        ),
        {"slugs": slugs},
    ).scalar_one_or_none()
    if extra_namespace is not None:
        raise RuntimeError("Existe una organización adicional en el espacio demo.")
    organizations = set(
        connection.execute(
            text(
                "SELECT slug, name, org_tax, org_zipcode FROM sch_iam.tbl_organization WHERE slug = ANY(:slugs)"
            ),
            {"slugs": slugs},
        ).tuples()
    )
    if not organizations.issubset(expected_organizations):
        raise RuntimeError("Una organización demo no coincide con el fixture.")
    organization_public_ids = connection.execute(
        text(
            "SELECT slug, public_id FROM sch_iam.tbl_organization WHERE slug = ANY(:slugs)"
        ),
        {"slugs": slugs},
    ).tuples()
    _assert_managed_public_ids("org", organization_public_ids)
    users = set(
        connection.execute(
            text(
                "SELECT u.email, o.slug FROM sch_iam.tbl_users u JOIN sch_iam.tbl_organization o ON o.id_organization = u.id_organization WHERE o.slug = ANY(:slugs)"
            ),
            {"slugs": slugs},
        ).tuples()
    )
    if not users.issubset(expected_users):
        raise RuntimeError("Un usuario demo no coincide con el fixture.")
    foreign_fixture_user = connection.execute(
        text(
            "SELECT 1 FROM sch_iam.tbl_users u JOIN sch_iam.tbl_organization o ON o.id_organization = u.id_organization WHERE u.email = ANY(:emails) AND o.slug <> ALL(:slugs)"
        ),
        {"slugs": slugs, "emails": emails},
    ).scalar_one_or_none()
    user_public_ids = connection.execute(
        text(
            "SELECT u.email, u.public_id FROM sch_iam.tbl_users u "
            "JOIN sch_iam.tbl_organization o "
            "ON o.id_organization = u.id_organization "
            "WHERE o.slug = ANY(:slugs)"
        ),
        {"slugs": slugs},
    ).tuples()
    _assert_managed_public_ids("usr", user_public_ids)
    departments = set(
        connection.execute(
            text(
                "SELECT o.slug, d.name FROM sch_iam.tbl_department d JOIN sch_iam.tbl_organization o ON o.id_organization = d.id_organization WHERE o.slug = ANY(:slugs)"
            ),
            {"slugs": slugs},
        ).tuples()
    )
    if not departments.issubset(expected_departments):
        raise RuntimeError("Un departamento demo no coincide con el fixture.")
    relations = set(
        connection.execute(
            text(
                "SELECT o.slug, d.name, u.email FROM sch_iam.tbl_department_relations r JOIN sch_iam.tbl_organization o ON o.id_organization = r.id_organization JOIN sch_iam.tbl_department d ON d.id_department = r.id_department JOIN sch_iam.tbl_users u ON u.id_user = r.id_user WHERE o.slug = ANY(:slugs)"
            ),
            {"slugs": slugs},
        ).tuples()
    )
    if not relations.issubset(expected_relations):
        raise RuntimeError("Una relación demo no coincide con el fixture.")
    if foreign_fixture_user is not None:
        raise RuntimeError("Una referencia no demo impide limpiar la demo.")
    if _foreign_key_contracts(connection) != EXPECTED_DEMO_FOREIGN_KEYS:
        raise RuntimeError("Una dependencia futura impide limpiar la demo.")


def _assert_managed_public_ids(
    prefix: str, public_ids: Iterable[tuple[object, object]]
) -> None:
    if any(
        not isinstance(natural_key, str)
        or not _is_managed_public_id(prefix, natural_key, public_id)
        for natural_key, public_id in public_ids
    ):
        raise RuntimeError("Una referencia no demo impide limpiar la demo.")


def _is_managed_public_id(prefix: str, natural_key: str, value: object) -> bool:
    if not isinstance(value, str) or value != _public_id(prefix, natural_key):
        return False
    try:
        parse_public_uuid(value, PublicIdPrefix(prefix))
    except ValueError:
        return False
    return True


def _foreign_key_contracts(connection: Connection) -> frozenset[ForeignKeyContract]:
    rows = connection.execute(
        text(
            "SELECT child_schema.nspname AS child_schema, child.relname AS child_table, "
            "string_agg(child_attribute.attname, ',' ORDER BY child_key.ordinality) "
            "AS child_columns, parent_schema.nspname AS parent_schema, "
            "parent.relname AS parent_table, "
            "string_agg(parent_attribute.attname, ',' ORDER BY parent_key.ordinality) "
            "AS parent_columns "
            "FROM pg_constraint fk "
            "JOIN pg_class child ON child.oid = fk.conrelid "
            "JOIN pg_namespace child_schema ON child_schema.oid = child.relnamespace "
            "JOIN pg_class parent ON parent.oid = fk.confrelid "
            "JOIN pg_namespace parent_schema ON parent_schema.oid = parent.relnamespace "
            "JOIN unnest(fk.conkey) WITH ORDINALITY AS child_key(attribute_number, ordinality) ON true "
            "JOIN pg_attribute child_attribute ON child_attribute.attrelid = child.oid "
            "AND child_attribute.attnum = child_key.attribute_number "
            "JOIN unnest(fk.confkey) WITH ORDINALITY AS parent_key(attribute_number, ordinality) "
            "ON parent_key.ordinality = child_key.ordinality "
            "JOIN pg_attribute parent_attribute ON parent_attribute.attrelid = parent.oid "
            "AND parent_attribute.attnum = parent_key.attribute_number "
            "WHERE fk.contype = 'f' AND parent_schema.nspname = 'sch_iam' "
            "AND parent.relname IN ('tbl_organization', 'tbl_users', 'tbl_department') "
            "GROUP BY fk.oid, child_schema.nspname, child.relname, parent_schema.nspname, parent.relname"
        )
    ).tuples()
    return frozenset(
        (str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]))
        for row in rows
    )


def _catalog_id(
    connection: Connection, table: str, identifier: str, column: str, value: str
) -> int:
    result = connection.execute(
        text(
            f"SELECT {identifier} FROM sch_iam.{table} WHERE lower({column}) = lower(:value)"
        ),
        {"value": value},
    ).scalar_one_or_none()
    if result is None:
        raise RuntimeError("Falta un catálogo IAM canónico.")
    return int(result)


def _geo(connection: Connection) -> tuple[int, int, int]:
    row = connection.execute(
        text(
            "SELECT c.id_country, s.id_state, city.id_city FROM sch_iam.tbl_country c JOIN sch_iam.tbl_state s ON s.id_country = c.id_country JOIN sch_iam.tbl_city city ON city.id_state = s.id_state WHERE lower(c.country_name) = 'españa' AND lower(s.state_name) = 'catalunya' AND lower(city.city_name) = 'barcelona'"
        )
    ).one_or_none()
    if row is None:
        raise RuntimeError("Falta la geografía IAM canónica.")
    return int(row[0]), int(row[1]), int(row[2])


def _public_id(prefix: str, natural_key: str) -> str:
    public_prefix = PublicIdPrefix(prefix)
    value = uuid.uuid5(DEMO_PUBLIC_ID_NAMESPACE, natural_key)
    encoded = urlsafe_b64encode(value.bytes).decode("ascii").rstrip("=")
    return f"{public_prefix.value}_{encoded}"


def _upsert_organization(
    connection: Connection,
    item: Organization,
    country: int,
    state: int,
    city: int,
    active: int,
) -> int:
    result = connection.execute(
        text(
            "INSERT INTO sch_iam.tbl_organization (public_id,id_country,id_state,id_city,id_status,name,slug,org_registered_name,org_tax,org_address,org_zipcode) VALUES (:public,:country,:state,:city,:status,:name,:slug,:registered,:tax,:address,:zipcode) ON CONFLICT (slug) DO NOTHING RETURNING id_organization"
        ),
        {
            "public": _public_id("org", item["slug"]),
            "country": country,
            "state": state,
            "city": city,
            "status": active,
            "name": item["name"],
            "slug": item["slug"],
            "registered": f"{item['name']} SL",
            "tax": item["tax"],
            "address": "Dirección demo",
            "zipcode": item["zipcode"],
        },
    ).scalar_one_or_none()
    return (
        int(result)
        if result is not None
        else _lookup(
            connection, "tbl_organization", "id_organization", "slug", item["slug"]
        )
    )


def _upsert_user(
    connection: Connection,
    item: User,
    organization: int,
    country: int,
    state: int,
    city: int,
    active: int,
    platform: int,
    password_hash: str,
) -> int:
    role = _catalog_id(
        connection,
        "tbl_organization_role",
        "id_org_role",
        "org_role_type",
        item["org_role"],
    )
    result = connection.execute(
        text(
            "INSERT INTO sch_iam.tbl_users (public_id,id_organization,id_platform_role,id_country,id_state,id_city,id_org_role,id_status,email,password_hash,first_name,last_name,birthdate,user_address,user_zipcode) VALUES (:public,:organization,:platform,:country,:state,:city,:role,:status,:email,:hash,:first,:last,:birth,:address,:zipcode) ON CONFLICT (email) DO NOTHING RETURNING id_user"
        ),
        {
            "public": _public_id("usr", item["email"]),
            "organization": organization,
            "platform": platform,
            "country": country,
            "state": state,
            "city": city,
            "role": role,
            "status": active,
            "email": item["email"],
            "hash": password_hash,
            "first": item["first_name"],
            "last": item["last_name"],
            "birth": date(1990, 1, 1),
            "address": "Dirección demo",
            "zipcode": "08001",
        },
    ).scalar_one_or_none()
    return (
        int(result)
        if result is not None
        else _lookup(connection, "tbl_users", "id_user", "email", item["email"])
    )


def _upsert_department(
    connection: Connection, item: Department, organization: int, identifier: int
) -> int:
    parameters = {
        "id": identifier,
        "organization": organization,
        "name": item["name"],
        "description": "Departamento demo",
    }
    result = _insert_demo_canonical(
        connection,
        "INSERT INTO sch_iam.tbl_department (id_department,id_organization,name,description) VALUES (:id,:organization,:name,:description) ON CONFLICT (id_organization, lower(name)) DO NOTHING RETURNING id_department",
        parameters,
        lambda: _lookup_department(connection, organization, item["name"]),
    )
    return (
        int(result)
        if result is not None
        else _lookup_department(connection, organization, item["name"])
    )


def _upsert_relation(
    connection: Connection, identifier: int, department: int, user: int
) -> None:
    _insert_demo_canonical(
        connection,
        "INSERT INTO sch_iam.tbl_department_relations (id_department_relation,id_department,id_user,id_organization) SELECT :id,:department,:user,id_organization FROM sch_iam.tbl_users WHERE id_user = :user ON CONFLICT (id_department,id_user) DO NOTHING RETURNING id_department_relation",
        {"id": identifier, "department": department, "user": user},
        lambda: _lookup_relation(connection, department, user),
    )


def _insert_demo_canonical(
    connection: Connection,
    statement: str,
    parameters: Mapping[str, object],
    lookup: Callable[[], int],
) -> int | None:
    try:
        with connection.begin_nested():
            result = connection.execute(
                text(statement), parameters
            ).scalar_one_or_none()
    except IntegrityError as error:
        try:
            return lookup()
        except RuntimeError:
            raise RuntimeError("Colisión de identificador interno demo.") from error
    return int(result) if result is not None else lookup()


def _lookup(
    connection: Connection, table: str, identifier: str, column: str, value: str
) -> int:
    result = connection.execute(
        text(f"SELECT {identifier} FROM sch_iam.{table} WHERE {column} = :value"),
        {"value": value},
    ).scalar_one_or_none()
    if result is None:
        raise RuntimeError("No se pudo recuperar la entidad demo.")
    return int(result)


def _lookup_department(connection: Connection, organization: int, name: str) -> int:
    result = connection.execute(
        text(
            "SELECT id_department FROM sch_iam.tbl_department WHERE id_organization = :organization AND lower(name) = lower(:name)"
        ),
        {"organization": organization, "name": name},
    ).scalar_one_or_none()
    if result is None:
        raise RuntimeError("No se pudo recuperar el departamento demo.")
    return int(result)


def _lookup_relation(connection: Connection, department: int, user: int) -> int:
    result = connection.execute(
        text(
            "SELECT id_department_relation FROM sch_iam.tbl_department_relations WHERE id_department = :department AND id_user = :user"
        ),
        {"department": department, "user": user},
    ).scalar_one_or_none()
    if result is None:
        raise RuntimeError("No se pudo recuperar la relación demo.")
    return int(result)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reemplaza sólo datos demo IAM; requiere --yes."
    )
    parser.add_argument("--clear", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    try:
        if not args.yes:
            raise ValueError("La operación demo requiere --yes.")
        fixture = load_fixture()
        variable = (
            "TEST_DATABASE_URL"
            if os.environ.get("APP_ENV") == "test"
            else "DEMO_DEVELOPMENT_DATABASE_URL"
        )
        engine = create_engine(
            validate_safe_target(os.environ, variable), hide_parameters=True
        )
        try:
            if args.clear:
                clear_demo(engine, fixture)
            else:
                password = os.environ.get("DEMO_SEED_PASSWORD")
                if not password:
                    raise ValueError("DEMO_SEED_PASSWORD es obligatoria.")
                seed_demo(engine, password, fixture)
        finally:
            engine.dispose()
    except (CommandError, OSError, RuntimeError, SQLAlchemyError, ValueError):
        print('{"event":"demo.failed"}')
        return 1
    print('{"event":"demo.complete"}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
