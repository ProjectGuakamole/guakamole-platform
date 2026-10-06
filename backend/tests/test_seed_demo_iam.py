import json
from pathlib import Path
from types import TracebackType
from typing import cast

import pytest
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.sql.elements import TextClause

import scripts.seed_demo_iam as seed_demo_iam
from scripts.seed_demo_iam import (
    build_truncate_statement,
    clear_demo,
    load_fixture,
    seed_demo,
    truncate_tables,
    validate_database_url,
    validate_fixture,
)


class FakeInspector:
    def __init__(
        self, *, has_schema: bool = True, missing_tables: set[str] | None = None
    ) -> None:
        self._has_schema = has_schema
        self._missing_tables = missing_tables or set()

    def has_schema(self, schema_name: str) -> bool:
        return self._has_schema and schema_name == seed_demo_iam.IAM_SCHEMA

    def has_table(self, table_name: str, *, schema: str | None = None) -> bool:
        return (
            schema == seed_demo_iam.IAM_SCHEMA
            and table_name not in self._missing_tables
        )


class FakeResult:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class FakeConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, statement: TextClause) -> FakeResult:
        self.statements.append(str(statement))
        return FakeResult(len(self.statements))


class FakeTransaction:
    def __init__(self, connection: FakeConnection) -> None:
        self._connection = connection

    def __enter__(self) -> FakeConnection:
        return self._connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None


class FakeEngine:
    def __init__(self) -> None:
        self.connection = FakeConnection()

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self.connection)


def test_validate_database_url_accepts_postgresql() -> None:
    url = validate_database_url("postgresql+psycopg://user:pass@localhost:5432/db")

    assert url.drivername == "postgresql+psycopg"


def test_validate_database_url_rejects_non_postgresql_prefix() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        validate_database_url("postgresqlite:///demo.db")


def test_validate_database_url_rejects_missing_value() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        validate_database_url(None)


def test_validate_database_url_rejects_sqlite() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        validate_database_url("sqlite:///demo.db")


def test_load_fixture_validates_demo_identifiers() -> None:
    fixture = load_fixture()

    assert len(fixture["organizations"]) == 6
    assert all(item["slug"].startswith("demo-") for item in fixture["organizations"])
    assert all(item["email"].endswith(".demo.test") for item in fixture["users"])


def test_validate_fixture_rejects_non_demo_slug(tmp_path: Path) -> None:
    fixture = load_fixture()
    fixture["organizations"][0]["slug"] = "acme"
    path = tmp_path / "iam_demo_seed.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")

    with pytest.raises(ValueError, match="demo-"):
        load_fixture(path)


def test_validate_fixture_rejects_out_of_range_collections() -> None:
    fixture = load_fixture()
    fixture["users"] = fixture["users"][:4]

    with pytest.raises(ValueError, match="entre 5 y 10"):
        validate_fixture(fixture)


def test_validate_fixture_requires_demo_department_name() -> None:
    fixture = load_fixture()
    fixture["departments"][0]["name"] = "Incident Response"

    with pytest.raises(ValueError, match="departamentos demo.*Demo"):
        validate_fixture(fixture)


def test_validate_fixture_requires_existing_user_organization() -> None:
    fixture = load_fixture()
    fixture["users"][0]["organization_slug"] = "demo-organizacion-inexistente"

    with pytest.raises(ValueError, match="usuario demo.*organización existente"):
        validate_fixture(fixture)


def test_validate_fixture_requires_existing_department_organization() -> None:
    fixture = load_fixture()
    fixture["departments"][0]["organization_slug"] = "demo-organizacion-inexistente"

    with pytest.raises(ValueError, match="departamento demo.*organización existente"):
        validate_fixture(fixture)


def test_validate_fixture_requires_relation_same_organization() -> None:
    fixture = load_fixture()
    fixture["department_relations"][0]["department_name"] = "Demo Incident Response"

    with pytest.raises(ValueError, match="misma organización"):
        validate_fixture(fixture)


def test_truncate_statement_contains_expected_tables_and_restart_cascade() -> None:
    statement = build_truncate_statement()

    assert "TRUNCATE TABLE" in statement
    assert "RESTART IDENTITY CASCADE" in statement
    assert truncate_tables() == seed_demo_iam.REQUIRED_TABLES
    for table in seed_demo_iam.REQUIRED_TABLES:
        assert f"sch_iam.{table}" in statement


def test_build_engine_hides_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_engine(url: URL, *, hide_parameters: bool) -> Engine:
        captured["url"] = url
        captured["hide_parameters"] = hide_parameters
        return cast(Engine, object())

    monkeypatch.setattr(seed_demo_iam, "create_engine", fake_create_engine)

    url = make_url("postgresql+psycopg://user:pass@localhost/db")

    seed_demo_iam.build_engine(url)

    assert captured == {"url": url, "hide_parameters": True}


def test_assert_schema_ready_fails_when_schema_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        seed_demo_iam, "inspect", lambda _engine: FakeInspector(has_schema=False)
    )

    with pytest.raises(RuntimeError, match="uv run alembic upgrade head"):
        seed_demo_iam.assert_schema_ready(cast(Engine, object()))


def test_assert_schema_ready_fails_when_required_table_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inspector = FakeInspector(missing_tables={"tbl_users"})
    monkeypatch.setattr(seed_demo_iam, "inspect", lambda _engine: inspector)

    with pytest.raises(RuntimeError, match="tbl_users.*uv run alembic upgrade head"):
        seed_demo_iam.assert_schema_ready(cast(Engine, object()))


def test_clear_demo_truncates_managed_iam_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_engine = FakeEngine()
    monkeypatch.setattr(seed_demo_iam, "assert_schema_ready", lambda _engine: None)

    clear_demo(cast(Engine, fake_engine))

    statements = fake_engine.connection.statements
    assert statements == [build_truncate_statement()]


def test_seed_demo_truncates_before_inserts(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    def fake_truncate(_connection: object) -> None:
        events.append("truncate")

    def fake_insert_statuses(
        _connection: object, _items: object
    ) -> seed_demo_iam.OperationStats:
        events.append("insert_statuses")
        return seed_demo_iam.OperationStats(created=5)

    monkeypatch.setattr(seed_demo_iam, "assert_schema_ready", lambda _engine: None)
    monkeypatch.setattr(seed_demo_iam, "truncate_iam", fake_truncate)
    monkeypatch.setattr(seed_demo_iam, "insert_statuses", fake_insert_statuses)
    monkeypatch.setattr(
        seed_demo_iam,
        "insert_platform_roles",
        lambda _connection, _items: seed_demo_iam.OperationStats(created=5),
    )
    monkeypatch.setattr(
        seed_demo_iam,
        "insert_organization_roles",
        lambda _connection, _items: seed_demo_iam.OperationStats(created=5),
    )
    monkeypatch.setattr(
        seed_demo_iam,
        "insert_countries",
        lambda _connection, _items: seed_demo_iam.OperationStats(created=5),
    )
    monkeypatch.setattr(
        seed_demo_iam,
        "insert_states",
        lambda _connection, _items: seed_demo_iam.OperationStats(created=5),
    )
    monkeypatch.setattr(
        seed_demo_iam,
        "insert_cities",
        lambda _connection, _items: seed_demo_iam.OperationStats(created=5),
    )
    monkeypatch.setattr(seed_demo_iam, "load_first_geo", lambda _connection: {})
    monkeypatch.setattr(seed_demo_iam, "scalar_id", lambda *_args: 1)
    monkeypatch.setattr(
        seed_demo_iam,
        "upsert_organizations",
        lambda *_args: seed_demo_iam.OperationStats(created=6),
    )
    monkeypatch.setattr(
        seed_demo_iam,
        "upsert_users",
        lambda *_args: seed_demo_iam.OperationStats(created=8),
    )
    monkeypatch.setattr(
        seed_demo_iam,
        "upsert_departments",
        lambda *_args: seed_demo_iam.OperationStats(created=8),
    )
    monkeypatch.setattr(
        seed_demo_iam,
        "upsert_relations",
        lambda *_args: seed_demo_iam.OperationStats(created=8),
    )

    seed_demo(cast(Engine, FakeEngine()), load_fixture())

    assert events == ["truncate", "insert_statuses"]


def test_help_reflects_yes_and_destructive_behavior(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr("sys.argv", ["seed_demo_iam.py", "--help"])
        with pytest.raises(SystemExit) as exc_info:
            seed_demo_iam.parse_args()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--yes" in help_text
    assert "DESTRUCTIVO" in help_text
    assert "trunca" in help_text
