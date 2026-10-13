"""Contratos de seguridad de la reconstrucción destructiva de IAM."""

from typing import cast

import pytest
from alembic.config import Config
from sqlalchemy import Engine

from alembic import command
from app.core import iam_rebaseline

pytestmark = pytest.mark.test_unit


def environment(**overrides: str) -> dict[str, str]:
    """Construye el mínimo entorno válido para la operación administrativa."""

    values = {
        "APP_ENV": "test",
        "TEST_DATABASE_URL": "postgresql+psycopg://test:test@localhost/guakamole_test",
    }
    values.update(overrides)
    return values


def test_rebaseline_requires_the_explicit_confirmation() -> None:
    with pytest.raises(ValueError, match="Confirmación destructiva"):
        iam_rebaseline.validate_rebaseline_request(environment(), "yes")


@pytest.mark.parametrize("app_env", ["staging", "production", "unknown", ""])
def test_rebaseline_rejects_protected_and_unknown_environments(app_env: str) -> None:
    with pytest.raises(ValueError, match="sólo se permite"):
        iam_rebaseline.validate_rebaseline_request(
            environment(APP_ENV=app_env), iam_rebaseline.CONFIRMATION_TOKEN
        )


def test_rebaseline_allows_test_database_with_dedicated_test_url() -> None:
    url = iam_rebaseline.validate_rebaseline_request(
        environment(), iam_rebaseline.CONFIRMATION_TOKEN
    )

    assert url.database == "guakamole_test"


@pytest.mark.parametrize(
    "test_database_url",
    [
        "postgresql+psycopg://test:test@localhost/guakamole_test",
        "postgresql+psycopg://test:test@127.0.0.1/guakamole_test",
        "postgresql+psycopg://test:test@[::1]/guakamole_test",
        "postgresql+psycopg:///guakamole_test?host=/var/run/postgresql",
    ],
)
def test_rebaseline_accepts_dedicated_local_test_database(
    test_database_url: str,
) -> None:
    url = iam_rebaseline.validate_rebaseline_request(
        environment(TEST_DATABASE_URL=test_database_url),
        iam_rebaseline.CONFIRMATION_TOKEN,
    )

    assert url.database == "guakamole_test"


@pytest.mark.parametrize(
    "test_database_url",
    [
        "",
        "sqlite:///guakamole_test",
        "postgresql+psycopg://localhost/",
        "postgresql+psycopg://test:test@localhost/guakamole_dev",
        "postgresql+psycopg://test:test@remote/guakamole_test",
    ],
)
def test_rebaseline_rejects_missing_or_unsafe_test_database_url(
    test_database_url: str,
) -> None:
    with pytest.raises(ValueError, match="TEST_DATABASE_URL"):
        iam_rebaseline.validate_rebaseline_request(
            environment(TEST_DATABASE_URL=test_database_url),
            iam_rebaseline.CONFIRMATION_TOKEN,
        )


def test_test_rebaseline_never_falls_back_to_database_url() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL no se usa"):
        iam_rebaseline.validate_rebaseline_request(
            {"APP_ENV": "test", "DATABASE_URL": "postgresql://remote/protected"},
            iam_rebaseline.CONFIRMATION_TOKEN,
        )


def test_development_rebaseline_accepts_dedicated_local_development_database() -> None:
    url = iam_rebaseline.validate_rebaseline_request(
        environment(
            APP_ENV="development",
            REBASELINE_DEVELOPMENT_DATABASE_URL=(
                "postgresql+psycopg://dev:dev@localhost/guakamole_dev"
            ),
        ),
        iam_rebaseline.CONFIRMATION_TOKEN,
    )

    assert url.database == "guakamole_dev"


def test_development_rebaseline_never_falls_back_to_database_url() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL no se usa"):
        iam_rebaseline.validate_rebaseline_request(
            {
                "APP_ENV": "development",
                "DATABASE_URL": "postgresql://staging.example/guakamole_staging",
            },
            iam_rebaseline.CONFIRMATION_TOKEN,
        )


@pytest.mark.parametrize(
    "development_url",
    [
        "postgresql+psycopg://dev:dev@staging.example/guakamole_dev",
        "postgresql+psycopg://dev:dev@localhost/guakamole_staging",
    ],
)
def test_spoofed_development_environment_rejects_protected_database_target(
    development_url: str,
) -> None:
    with pytest.raises(ValueError, match="REBASELINE_DEVELOPMENT_DATABASE_URL"):
        iam_rebaseline.validate_rebaseline_request(
            environment(
                APP_ENV="development",
                REBASELINE_DEVELOPMENT_DATABASE_URL=development_url,
            ),
            iam_rebaseline.CONFIRMATION_TOKEN,
        )


def test_rebaseline_drops_schema_and_missing_alembic_metadata_before_upgrade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    statements: list[str] = []
    upgrades: list[str] = []
    upgrade_connections: list[object] = []

    class FakeConnection:
        def execute(self, statement: object) -> None:
            statements.append(str(statement))

    class Transaction:
        def __enter__(self) -> FakeConnection:
            return fake_connection

        def __exit__(self, *_: object) -> None:
            return None

    class FakeEngine:
        def begin(self) -> Transaction:
            return Transaction()

    fake_connection = FakeConnection()

    def fake_upgrade(config: Config, revision: str) -> None:
        upgrades.append(revision)
        upgrade_connections.append(config.attributes["connection"])

    monkeypatch.setattr(command, "upgrade", fake_upgrade)

    config = Config()
    config.set_main_option(
        "sqlalchemy.url", "postgresql+psycopg://protected:protected@remote/protected"
    )
    iam_rebaseline.rebuild_iam_baseline(cast(Engine, FakeEngine()), config)

    assert statements == [
        "DROP SCHEMA IF EXISTS sch_iam CASCADE",
        "DROP TABLE IF EXISTS public.alembic_version",
    ]
    assert upgrades == ["head"]
    assert upgrade_connections == [fake_connection]
    assert config.attributes.get("connection") is None


def test_rebaseline_does_not_run_during_application_startup() -> None:
    main_source = "app/main.py"

    with open(main_source, encoding="utf-8") as main_file:
        assert "rebaseline" not in main_file.read()


@pytest.mark.parametrize("app_env", ["staging", "production", "unknown", ""])
def test_configured_rebaseline_validates_before_creating_an_engine(
    monkeypatch: pytest.MonkeyPatch,
    app_env: str,
) -> None:
    created = False

    def fake_create_engine(_: object, **__: object) -> Engine:
        nonlocal created
        created = True
        raise AssertionError("No debe abrirse una conexión insegura")

    monkeypatch.setattr(iam_rebaseline, "create_engine", fake_create_engine)

    with pytest.raises(ValueError, match="sólo se permite"):
        iam_rebaseline.rebaseline_configured_database(
            environment(
                APP_ENV=app_env,
                REBASELINE_DEVELOPMENT_DATABASE_URL=(
                    "postgresql+psycopg://dev:dev@staging.example/guakamole_dev"
                ),
            ),
            iam_rebaseline.CONFIRMATION_TOKEN,
            Config(),
        )

    assert created is False


def test_test_rebaseline_rejects_remote_target_before_creating_an_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = False

    def fake_create_engine(_: object, **__: object) -> Engine:
        nonlocal created
        created = True
        raise AssertionError("No debe abrirse una conexión remota")

    monkeypatch.setattr(iam_rebaseline, "create_engine", fake_create_engine)

    with pytest.raises(ValueError, match="socket Unix local"):
        iam_rebaseline.rebaseline_configured_database(
            environment(
                TEST_DATABASE_URL=(
                    "postgresql+psycopg://test:test@remote/guakamole_test"
                )
            ),
            iam_rebaseline.CONFIRMATION_TOKEN,
            Config(),
        )

    assert created is False
