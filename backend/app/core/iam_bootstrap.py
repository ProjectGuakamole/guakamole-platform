"""Carga transaccional de los catálogos IAM definidos por la línea base."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import Engine, inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import Executable

IAM_SCHEMA = "sch_iam"
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
    "tbl_revoked_access_token",
)
STATUSES = ((101, "ACTIVE"), (102, "INACTIVE"), (103, "DISABLED"))
PLATFORM_ROLES = (
    (201, "PLATFORM_ADMIN", "Administrador global de Project Guakamole"),
    (202, "USER", "Usuario estándar de plataforma"),
)
ORG_ROLES = (
    (301, "COMPANY_ADMIN"),
    (302, "GROUP_MANAGER"),
    (303, "SCENARIO_EDITOR"),
    (304, "EMPLOYEE"),
)
GEO = (
    (401, "España", 501, "Catalunya", 601, "Barcelona"),
    (401, "España", 502, "Madrid", 602, "Madrid"),
    (402, "Portugal", 503, "Lisboa", 603, "Lisboa"),
    (403, "Francia", None, None, None, None),
)


@dataclass(frozen=True)
class BootstrapResult:
    created: int


def assert_baseline_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    missing = [
        name
        for name in REQUIRED_TABLES
        if not inspector.has_table(name, schema=IAM_SCHEMA)
    ]
    if not inspector.has_schema(IAM_SCHEMA) or missing:
        raise RuntimeError(
            "Falta la línea base IAM; ejecuta Alembic antes del bootstrap."
        )


def bootstrap_iam(engine: Engine) -> BootstrapResult:
    """Carga los catálogos en una única transacción aislada."""
    assert_baseline_schema(engine)
    with engine.begin() as connection:
        return bootstrap_iam_connection(connection)


def assert_canonical_bootstrap_catalogs(connection: Connection) -> None:
    """Comprueba, sin escribir, los catálogos requeridos por los datos demo.

    El seed demo es deliberadamente independiente del bootstrap. Esta comprobación
    confirma que los valores naturales requeridos existen. Los identificadores
    internos son un detalle de bootstrap y no forman parte de este contrato.
    """
    try:
        for _, value in STATUSES:
            _require_natural_id(connection, "tbl_status", "id_status", "status", value)
        for _, value, _ in PLATFORM_ROLES:
            _require_natural_id(
                connection,
                "tbl_platform_role",
                "id_platform_role",
                "platform_role_type",
                value,
            )
        for _, value in ORG_ROLES:
            _require_natural_id(
                connection,
                "tbl_organization_role",
                "id_org_role",
                "org_role_type",
                value,
            )
        for _, country, _, state, _, city in GEO:
            country_id = _require_natural_id(
                connection, "tbl_country", "id_country", "country_name", country
            )
            if state is None or city is None:
                continue
            state_id = _require_geo_id(
                connection,
                "tbl_state",
                "id_state",
                "state_name",
                state,
                "id_country",
                country_id,
            )
            _require_geo_id(
                connection,
                "tbl_city",
                "id_city",
                "city_name",
                city,
                "id_state",
                state_id,
            )
    except RuntimeError as error:
        raise RuntimeError(
            "Falta o no coincide el catálogo IAM canónico; ejecuta "
            "`make backend-bootstrap` antes de operar con la demo."
        ) from error


def bootstrap_iam_connection(connection: Connection) -> BootstrapResult:
    """Carga catálogos usando la transacción que posee el llamador.

    La migración base no genera las claves de catálogo/geografía. Los
    identificadores deterministas sólo se usan para insertar valores ausentes. Las
    referencias posteriores se resuelven siempre por sus claves naturales.
    """
    created = 0
    for identifier, value in STATUSES:
        created += _upsert_catalog(
            connection, "tbl_status", "id_status", identifier, "status", value
        )
    for identifier, value, description in PLATFORM_ROLES:
        created += _upsert_catalog(
            connection,
            "tbl_platform_role",
            "id_platform_role",
            identifier,
            "platform_role_type",
            value,
            description,
        )
    for identifier, value in ORG_ROLES:
        created += _upsert_catalog(
            connection,
            "tbl_organization_role",
            "id_org_role",
            identifier,
            "org_role_type",
            value,
        )
    for country_id, country, state_id, state, city_id, city in GEO:
        created += _upsert_catalog(
            connection, "tbl_country", "id_country", country_id, "country_name", country
        )
        if state_id is None or state is None or city_id is None or city is None:
            continue
        resolved_country_id = _require_natural_id(
            connection, "tbl_country", "id_country", "country_name", country
        )
        created += _upsert_geo(
            connection,
            "tbl_state",
            "id_state",
            state_id,
            "state_name",
            state,
            "id_country",
            resolved_country_id,
        )
        resolved_state_id = _require_geo_id(
            connection,
            "tbl_state",
            "id_state",
            "state_name",
            state,
            "id_country",
            resolved_country_id,
        )
        created += _upsert_city(
            connection, city_id, city, resolved_state_id, resolved_country_id
        )
    return BootstrapResult(created)


def _upsert_catalog(
    connection: Connection,
    table: str,
    id_column: str,
    identifier: int,
    column: str,
    value: str,
    description: str | None = None,
) -> int:
    if description is None:
        statement = text(
            f"INSERT INTO sch_iam.{table} ({id_column}, {column}) VALUES (:id, :value) ON CONFLICT (lower({column})) DO NOTHING RETURNING {id_column}"
        )
        parameters = {"id": identifier, "value": value}
    else:
        statement = text(
            f"INSERT INTO sch_iam.{table} ({id_column}, {column}, description) VALUES (:id, :value, :description) ON CONFLICT (lower({column})) DO NOTHING RETURNING {id_column}"
        )
        parameters = {"id": identifier, "value": value, "description": description}
    inserted = _insert_canonical(
        connection, statement, parameters, table, id_column, column, value
    )
    _require_natural_id(connection, table, id_column, column, value)
    return int(inserted is not None)


def _upsert_geo(
    connection: Connection,
    table: str,
    id_column: str,
    identifier: int,
    column: str,
    value: str,
    parent: str,
    parent_id: int,
) -> int:
    statement = text(
        f"INSERT INTO sch_iam.{table} ({id_column}, {parent}, {column}) VALUES (:id, :parent, :value) ON CONFLICT ({parent}, lower({column})) DO NOTHING RETURNING {id_column}"
    )
    inserted = _insert_canonical(
        connection,
        statement,
        {"id": identifier, "parent": parent_id, "value": value},
        table,
        id_column,
        column,
        value,
        parent,
        parent_id,
    )
    _require_geo_id(connection, table, id_column, column, value, parent, parent_id)
    return int(inserted is not None)


def _upsert_city(
    connection: Connection, identifier: int, value: str, state_id: int, country_id: int
) -> int:
    statement = text(
        "INSERT INTO sch_iam.tbl_city (id_city, id_state, id_country, city_name) VALUES (:id, :state, :country, :value) ON CONFLICT (id_state, lower(city_name)) DO NOTHING RETURNING id_city"
    )
    inserted = _insert_canonical(
        connection,
        statement,
        {"id": identifier, "state": state_id, "country": country_id, "value": value},
        "tbl_city",
        "id_city",
        "city_name",
        value,
        "id_state",
        state_id,
    )
    _require_geo_id(
        connection, "tbl_city", "id_city", "city_name", value, "id_state", state_id
    )
    return int(inserted is not None)


def _insert_canonical(
    connection: Connection,
    statement: Executable,
    parameters: Mapping[str, object],
    table: str,
    id_column: str,
    column: str,
    value: str,
    parent: str | None = None,
    parent_id: int | None = None,
) -> int | None:
    """Inserta sin carrera; una colisión de PK sólo vale si ya existe la natural."""
    try:
        with connection.begin_nested():
            result = connection.execute(statement, parameters).scalar_one_or_none()
    except IntegrityError as error:
        if _natural_exists(
            connection, table, id_column, column, value, parent, parent_id
        ):
            return None
        raise RuntimeError(
            "Colisión de identificador interno del catálogo IAM."
        ) from error
    return int(result) if result is not None else None


def _natural_exists(
    connection: Connection,
    table: str,
    id_column: str,
    column: str,
    value: str,
    parent: str | None,
    parent_id: int | None,
) -> bool:
    if parent is None:
        return (
            _require_natural_id(connection, table, id_column, column, value) is not None
        )
    if parent_id is None:
        return False
    return (
        _require_geo_id(connection, table, id_column, column, value, parent, parent_id)
        is not None
    )


def _require_natural_id(
    connection: Connection, table: str, id_column: str, column: str, value: str
) -> int:
    rows = (
        connection.execute(
            text(
                f"SELECT {id_column} FROM sch_iam.{table} WHERE lower({column}) = lower(:value)"
            ),
            {"value": value},
        )
        .scalars()
        .all()
    )
    if len(rows) != 1:
        raise RuntimeError("Clave natural ambigua en catálogo IAM.")
    return int(rows[0])


def _require_geo_id(
    connection: Connection,
    table: str,
    id_column: str,
    column: str,
    value: str,
    parent: str,
    parent_id: int,
) -> int:
    rows = (
        connection.execute(
            text(
                f"SELECT {id_column} FROM sch_iam.{table} WHERE {parent} = :parent AND lower({column}) = lower(:value)"
            ),
            {"parent": parent_id, "value": value},
        )
        .scalars()
        .all()
    )
    if len(rows) != 1:
        raise RuntimeError("Clave natural geográfica ambigua.")
    return int(rows[0])
