import os
from collections.abc import Generator
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from app.domain.iam.access.models import OrganizationRole, PlatformRole, Status
from app.domain.iam.geography.models import City, Country, State
from app.domain.iam.organizations.models import Organization
from app.domain.iam.users.models import User
from app.domain.iam.users.repositories import SqlAlchemyOrganizationUsersRepository
from app.domain.iam.users.schemas import UserListQuery

pytestmark = [pytest.mark.integration, pytest.mark.db]

SAFE_HASH = "argon2id" + "-repository-test"
DATABASE_URL_ENV_VAR = "DATABASE_URL"
TEST_DATABASE_URL_ENV_VAR = "TEST_DATABASE_URL"
POSTGRES_ENV_VARS = (
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)
POSTGRESQL_DATABASE_URL_PREFIXES = (
    "postgresql://",
    "postgresql+psycopg://",
    "postgresql+psycopg2://",
    "postgres://",
)
PLACEHOLDER_MARKERS = ("change-me", "example", "placeholder")
TEST_ORGANIZATION_IDS = (10_001, 10_002)
TEST_USER_IDS = (20_001, 20_002, 20_003, 20_004)
TEST_STATUS_ID = 30_001
TEST_PLATFORM_ROLE_ID = 30_002
TEST_ORGANIZATION_ROLE_ID = 30_003
TEST_COUNTRY_ID = 30_004
TEST_STATE_ID = 30_005
TEST_CITY_ID = 30_006


def read_environment_file(file_path: Path) -> dict[str, str]:
    if not file_path.exists():
        return {}

    environment: dict[str, str] = {}
    for line in file_path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if (
            not stripped_line
            or stripped_line.startswith("#")
            or "=" not in stripped_line
        ):
            continue

        key, value = stripped_line.split("=", maxsplit=1)
        normalized_key = key.removeprefix("export ").strip()
        environment[normalized_key] = value.strip().strip('"').strip("'")

    return environment


def build_postgresql_url_from_environment(environment: dict[str, str]) -> str | None:
    if not all(environment.get(variable) for variable in POSTGRES_ENV_VARS):
        return None

    user = quote_plus(environment["POSTGRES_USER"])
    password = quote_plus(environment["POSTGRES_PASSWORD"])
    host = environment["POSTGRES_HOST"]
    port = environment["POSTGRES_PORT"]
    database = quote_plus(environment["POSTGRES_DB"])

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


def ensure_postgresql_database_url(database_url: str) -> str:
    if database_url.startswith(POSTGRESQL_DATABASE_URL_PREFIXES):
        return database_url

    raise RuntimeError(
        "Los tests de repository IAM/users deben ejecutarse contra PostgreSQL real. "
        f"URL rechazada para {DATABASE_URL_ENV_VAR}: dialecto no permitido."
    )


def ensure_not_placeholder_database_url(database_url: str) -> str:
    normalized_url = database_url.lower()
    if any(marker in normalized_url for marker in PLACEHOLDER_MARKERS):
        raise RuntimeError(
            "Los tests de repository IAM/users no aceptan URLs de base de datos "
            "con valores placeholder. Define TEST_DATABASE_URL o variables "
            "POSTGRES_* coherentes para PostgreSQL real."
        )

    return database_url


def ensure_valid_test_database_url(database_url: str) -> str:
    return ensure_not_placeholder_database_url(
        ensure_postgresql_database_url(database_url)
    )


def get_repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_database_url_from_environment(
    environment: dict[str, str],
) -> str | None:
    database_url = environment.get(TEST_DATABASE_URL_ENV_VAR)
    if database_url:
        return ensure_valid_test_database_url(database_url)

    database_url = build_postgresql_url_from_environment(environment)
    if database_url:
        return ensure_valid_test_database_url(database_url)

    return None


def get_test_database_url() -> str:
    database_url = os.environ.get(TEST_DATABASE_URL_ENV_VAR)
    if database_url:
        return ensure_valid_test_database_url(database_url)

    database_url = build_postgresql_url_from_environment(dict(os.environ))
    if database_url:
        return ensure_valid_test_database_url(database_url)

    repository_root = get_repository_root()
    example_environment = read_environment_file(repository_root / ".env.example")
    database_url = example_environment.get(DATABASE_URL_ENV_VAR)
    if database_url:
        return ensure_valid_test_database_url(database_url)

    database_url = get_database_url_from_environment(example_environment)
    if database_url:
        return database_url

    environment = read_environment_file(repository_root / ".env")
    database_url = get_database_url_from_environment(environment)
    if database_url:
        return database_url

    database_url = os.environ.get(DATABASE_URL_ENV_VAR)
    if database_url:
        return ensure_valid_test_database_url(database_url)

    raise RuntimeError(
        f"La variable {TEST_DATABASE_URL_ENV_VAR} o una configuración POSTGRES_* "
        "coherente debe estar definida para ejecutar los tests de repository "
        "contra PostgreSQL real."
    )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(get_test_database_url(), hide_parameters=True)
    session = Session(engine)
    try:
        cleanup_repository_test_data(session)
        yield session
    finally:
        session.rollback()
        cleanup_repository_test_data(session)
        session.close()
        engine.dispose()


def cleanup_repository_test_data(session: Session) -> None:
    session.execute(delete(User).where(User.id_user.in_(TEST_USER_IDS)))
    session.execute(
        delete(Organization).where(
            Organization.id_organization.in_(TEST_ORGANIZATION_IDS)
        )
    )
    session.execute(delete(City).where(City.id_city == TEST_CITY_ID))
    session.execute(delete(State).where(State.id_state == TEST_STATE_ID))
    session.execute(delete(Country).where(Country.id_country == TEST_COUNTRY_ID))
    session.execute(delete(Status).where(Status.id_status == TEST_STATUS_ID))
    session.execute(
        delete(PlatformRole).where(
            PlatformRole.id_platform_role == TEST_PLATFORM_ROLE_ID
        )
    )
    session.execute(
        delete(OrganizationRole).where(
            OrganizationRole.id_org_role == TEST_ORGANIZATION_ROLE_ID
        )
    )
    session.commit()


def test_database_url_helper_rejects_sqlite() -> None:
    with pytest.raises(RuntimeError, match="PostgreSQL real"):
        ensure_valid_test_database_url("sqlite:///repository-test.db")


def test_database_url_helper_prioritizes_test_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_url = "postgresql+psycopg://test_user:test_pass@localhost:5432/test_db"
    monkeypatch.setenv(TEST_DATABASE_URL_ENV_VAR, expected_url)
    monkeypatch.setenv(
        DATABASE_URL_ENV_VAR,
        "postgresql+psycopg://guakamole_user:wrong@localhost:5432/guakamole_db",
    )

    assert get_test_database_url() == expected_url


def test_database_url_helper_uses_postgres_environment_before_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(TEST_DATABASE_URL_ENV_VAR, raising=False)
    monkeypatch.setenv(
        DATABASE_URL_ENV_VAR,
        "postgresql+psycopg://guakamole_user:wrong@localhost:5432/guakamole_db",
    )
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "guakamole_db")
    monkeypatch.setenv("POSTGRES_USER", "guakamole_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgre")

    assert get_test_database_url() == (
        "postgresql+psycopg://guakamole_user:postgre@localhost:5432/guakamole_db"
    )


def test_database_url_helper_rejects_placeholders() -> None:
    with pytest.raises(RuntimeError, match="placeholder"):
        ensure_valid_test_database_url(
            "postgresql+psycopg://guakamole_user:change-me@localhost:5432/db"
        )


def seed_catalogs(session: Session) -> None:
    session.add_all(
        [
            Status(id_status=TEST_STATUS_ID, status="ACTIVE_REPOSITORY_TEST"),
            PlatformRole(
                id_platform_role=TEST_PLATFORM_ROLE_ID,
                platform_role_type="USER_REPOSITORY_TEST",
                description="Rol de test de repository.",
            ),
            OrganizationRole(
                id_org_role=TEST_ORGANIZATION_ROLE_ID,
                org_role_type="EMPLOYEE_REPOSITORY_TEST",
            ),
        ]
    )
    session.commit()
    session.add(
        Country(id_country=TEST_COUNTRY_ID, country_name="Repository Test Country")
    )
    session.commit()
    session.add(
        State(
            id_state=TEST_STATE_ID,
            id_country=TEST_COUNTRY_ID,
            state_name="Repository Test State",
        )
    )
    session.commit()
    session.add(
        City(
            id_city=TEST_CITY_ID,
            id_state=TEST_STATE_ID,
            city_name="Repository Test City",
        )
    )
    session.commit()


def seed_organizations(session: Session) -> None:
    session.add_all(
        [
            make_organization(
                organization_id=10_001,
                name="Acme Repository Test",
                slug="acme-repository-test",
            ),
            make_organization(
                organization_id=10_002,
                name="CyberCorp Repository Test",
                slug="cybercorp-repository-test",
            ),
        ]
    )
    session.commit()


def seed_users(session: Session) -> None:
    seed_catalogs(session)
    seed_organizations(session)
    session.add_all(
        [
            make_user(
                user_id=20_001,
                organization_id=10_001,
                email="ana.acme@example.test",
                first_name="Ana",
                last_name="García",
            ),
            make_user(
                user_id=20_002,
                organization_id=10_001,
                email="carlos.acme@example.test",
                first_name="Carlos",
                last_name="López",
            ),
            make_user(
                user_id=20_003,
                organization_id=10_001,
                email="maria.acme@example.test",
                first_name="María",
                last_name="Pérez",
            ),
            make_user(
                user_id=20_004,
                organization_id=10_002,
                email="ana.cybercorp@example.test",
                first_name="Ana",
                last_name="García",
            ),
        ]
    )
    session.commit()


def make_organization(*, organization_id: int, name: str, slug: str) -> Organization:
    return Organization(
        id_organization=organization_id,
        id_country=TEST_COUNTRY_ID,
        id_state=TEST_STATE_ID,
        id_city=TEST_CITY_ID,
        id_status=TEST_STATUS_ID,
        name=name,
        slug=slug,
        org_registered_name=f"{name} Repository Test SL",
        org_tax=f"TEST-{organization_id}",
        org_address="Calle Repository Test 1",
        org_zipcode="08001",
    )


def make_user(
    *,
    user_id: int,
    organization_id: int,
    email: str,
    first_name: str,
    last_name: str,
) -> User:
    return User(
        id_user=user_id,
        id_organization=organization_id,
        id_platform_role=TEST_PLATFORM_ROLE_ID,
        id_country=TEST_COUNTRY_ID,
        id_state=TEST_STATE_ID,
        id_city=TEST_CITY_ID,
        id_org_role=TEST_ORGANIZATION_ROLE_ID,
        id_status=TEST_STATUS_ID,
        email=email,
        password_hash=SAFE_HASH,
        first_name=first_name,
        last_name=last_name,
        birthdate=date(1990, 1, 1),
        user_address="Calle Test 1",
        user_zipcode="08001",
        created_at=datetime(2026, 10, 1, 10, user_id % 60, tzinfo=UTC),
        updated_at=None,
        last_login_at=None,
    )


def test_lists_only_requested_organization_users(db_session: Session) -> None:
    seed_users(db_session)
    repository = SqlAlchemyOrganizationUsersRepository(db_session)

    response = repository.list_by_organization(
        organization_id=10_001,
        query=UserListQuery(sort_by="id_user"),
    )

    assert response.total == 3
    assert [user.id_user for user in response.items] == [20_001, 20_002, 20_003]
    assert {user.id_organization for user in response.items} == {10_001}


def test_pagination_limits_results_and_respects_offset(db_session: Session) -> None:
    seed_users(db_session)
    repository = SqlAlchemyOrganizationUsersRepository(db_session)

    response = repository.list_by_organization(
        organization_id=10_001,
        query=UserListQuery(limit=1, offset=1, sort_by="id_user"),
    )

    assert response.total == 3
    assert response.limit == 1
    assert response.offset == 1
    assert [user.id_user for user in response.items] == [20_002]


def test_search_filter_uses_allowed_fields(db_session: Session) -> None:
    seed_users(db_session)
    repository = SqlAlchemyOrganizationUsersRepository(db_session)

    response = repository.list_by_organization(
        organization_id=10_001,
        query=UserListQuery(search="carlos", sort_by="email"),
    )

    assert response.total == 1
    assert [user.email for user in response.items] == ["carlos.acme@example.test"]


def test_search_does_not_leak_matching_users_from_other_tenants(
    db_session: Session,
) -> None:
    seed_users(db_session)
    repository = SqlAlchemyOrganizationUsersRepository(db_session)

    response = repository.list_by_organization(
        organization_id=10_001,
        query=UserListQuery(search="cybercorp"),
    )

    assert response.total == 0
    assert response.items == []


def test_sort_allowlist_is_applied_to_allowed_schema_fields(
    db_session: Session,
) -> None:
    seed_users(db_session)
    repository = SqlAlchemyOrganizationUsersRepository(db_session)

    response = repository.list_by_organization(
        organization_id=10_001,
        query=UserListQuery(sort_by="last_name", sort_dir="desc"),
    )

    assert [user.last_name for user in response.items] == ["Pérez", "López", "García"]


def test_repository_output_does_not_expose_sensitive_fields(
    db_session: Session,
) -> None:
    seed_users(db_session)
    repository = SqlAlchemyOrganizationUsersRepository(db_session)

    response = repository.list_by_organization(
        organization_id=10_001,
        query=UserListQuery(limit=1),
    )

    dumped_user = response.items[0].model_dump()
    assert "password_hash" not in dumped_user
    assert not hasattr(response.items[0], "password_hash")


def test_repository_does_not_import_fastapi() -> None:
    repository_source = Path("app/domain/iam/users/repositories.py").read_text(
        encoding="utf-8"
    )

    assert "fastapi" not in repository_source.lower()
