"""Tests DB del repositorio SQLAlchemy de login."""

import dataclasses
import os
from collections.abc import Generator
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from app.domain.auth.login_repositories import SqlAlchemyLoginUserRepository
from app.domain.iam.access.models import OrganizationRole, PlatformRole, Status
from app.domain.iam.geography.models import City, Country, State
from app.domain.iam.organizations.models import Organization
from app.domain.iam.users.models import User

pytestmark = [pytest.mark.integration, pytest.mark.db]

SAFE_HASH = "argon2id-login-repository-test"
TEST_DATABASE_URL_ENV_VAR = "TEST_DATABASE_URL"
DATABASE_URL_ENV_VAR = "DATABASE_URL"
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
TEST_ORGANIZATION_ID = 11_001
TEST_USER_ID = 21_001
TEST_STATUS_ID = 31_001
TEST_PLATFORM_ROLE_ID = 31_002
TEST_ORGANIZATION_ROLE_ID = 31_003
TEST_COUNTRY_ID = 31_004
TEST_STATE_ID = 31_005
TEST_CITY_ID = 31_006


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
        "Define TEST_DATABASE_URL o variables POSTGRES_* coherentes para "
        "PostgreSQL real."
    )


def ensure_postgresql_database_url(database_url: str) -> str:
    if database_url.startswith(POSTGRESQL_DATABASE_URL_PREFIXES):
        return database_url
    raise RuntimeError("Los tests de login repository requieren PostgreSQL real.")


def ensure_not_placeholder_database_url(database_url: str) -> str:
    normalized_url = database_url.lower()
    if any(marker in normalized_url for marker in PLACEHOLDER_MARKERS):
        raise RuntimeError(
            "Los tests de login repository no aceptan URLs de base de datos "
            "con valores placeholder."
        )

    return database_url


def ensure_valid_test_database_url(database_url: str) -> str:
    return ensure_not_placeholder_database_url(
        ensure_postgresql_database_url(database_url)
    )


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
        environment[key.removeprefix("export ").strip()] = (
            value.strip().strip('"').strip("'")
        )
    return environment


def build_postgresql_url_from_environment(environment: dict[str, str]) -> str | None:
    if not all(environment.get(variable) for variable in POSTGRES_ENV_VARS):
        return None
    user = quote_plus(environment["POSTGRES_USER"])
    password = quote_plus(environment["POSTGRES_PASSWORD"])
    database = quote_plus(environment["POSTGRES_DB"])
    return (
        "postgresql+psycopg://"
        f"{user}:{password}@{environment['POSTGRES_HOST']}:"
        f"{environment['POSTGRES_PORT']}/{database}"
    )


def get_database_url_from_environment(environment: dict[str, str]) -> str | None:
    database_url = environment.get(TEST_DATABASE_URL_ENV_VAR)
    if database_url:
        return ensure_valid_test_database_url(database_url)

    database_url = build_postgresql_url_from_environment(environment)
    if database_url:
        return ensure_valid_test_database_url(database_url)

    return None


def get_repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture
def login_db_session() -> Generator[Session, None, None]:
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
    session.execute(delete(User).where(User.id_user == TEST_USER_ID))
    session.execute(
        delete(Organization).where(Organization.id_organization == TEST_ORGANIZATION_ID)
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


def seed_users(session: Session) -> None:
    session.add_all(
        [
            Status(id_status=TEST_STATUS_ID, status="ACTIVE_LOGIN_REPOSITORY_TEST"),
            PlatformRole(
                id_platform_role=TEST_PLATFORM_ROLE_ID,
                platform_role_type="USER_LOGIN_REPOSITORY_TEST",
                description="Rol de test de login repository.",
            ),
            OrganizationRole(
                id_org_role=TEST_ORGANIZATION_ROLE_ID,
                org_role_type="EMPLOYEE_LOGIN_REPOSITORY_TEST",
            ),
        ]
    )
    session.commit()
    session.add(Country(id_country=TEST_COUNTRY_ID, country_name="Login Test Country"))
    session.commit()
    session.add(
        State(
            id_state=TEST_STATE_ID,
            id_country=TEST_COUNTRY_ID,
            state_name="Login Test State",
        )
    )
    session.commit()
    session.add(
        City(id_city=TEST_CITY_ID, id_state=TEST_STATE_ID, city_name="Login City")
    )
    session.commit()
    session.add(
        Organization(
            id_organization=TEST_ORGANIZATION_ID,
            id_country=TEST_COUNTRY_ID,
            id_state=TEST_STATE_ID,
            id_city=TEST_CITY_ID,
            id_status=TEST_STATUS_ID,
            name="Login Repository Test",
            slug="login-repository-test",
            org_registered_name="Login Repository Test SL",
            org_tax="LOGIN-REPOSITORY-TEST",
            org_address="Calle Login Test 1",
            org_zipcode="08001",
        )
    )
    session.commit()
    session.add(
        User(
            id_user=TEST_USER_ID,
            id_organization=TEST_ORGANIZATION_ID,
            id_platform_role=TEST_PLATFORM_ROLE_ID,
            id_country=TEST_COUNTRY_ID,
            id_state=TEST_STATE_ID,
            id_city=TEST_CITY_ID,
            id_org_role=TEST_ORGANIZATION_ROLE_ID,
            id_status=TEST_STATUS_ID,
            email="ana.login@example.test",
            password_hash=SAFE_HASH,
            first_name="Ana",
            last_name="Login",
            birthdate=date(1990, 1, 1),
            user_address="Calle Login Test 1",
            user_zipcode="08001",
            created_at=datetime(2026, 10, 1, 10, 0, tzinfo=UTC),
            updated_at=None,
            last_login_at=None,
        )
    )
    session.commit()


def test_finds_user_by_case_insensitive_normalized_email(
    login_db_session: Session,
) -> None:
    seed_users(login_db_session)
    repository = SqlAlchemyLoginUserRepository(login_db_session)

    record = repository.find_by_normalized_email("ANA.LOGIN@EXAMPLE.TEST")

    assert record is not None
    user = login_db_session.query(User).filter_by(email="ana.login@example.test").one()
    assert record.user_public_id == user.public_id
    assert record.organization_public_id is not None
    assert record.password_hash == SAFE_HASH
    assert record.status == "ACTIVE_LOGIN_REPOSITORY_TEST"


def test_login_user_record_does_not_expose_internal_database_ids(
    login_db_session: Session,
) -> None:
    seed_users(login_db_session)
    repository = SqlAlchemyLoginUserRepository(login_db_session)

    record = repository.find_by_normalized_email("ana.login@example.test")

    assert record is not None
    record_fields = {field.name for field in dataclasses.fields(record)}
    assert "id_user" not in record_fields
    assert "id_organization" not in record_fields
    assert not hasattr(record, "id_user")
    assert not hasattr(record, "id_organization")


def test_returns_none_when_email_does_not_exist(login_db_session: Session) -> None:
    seed_users(login_db_session)
    repository = SqlAlchemyLoginUserRepository(login_db_session)

    assert repository.find_by_normalized_email("missing@example.test") is None
