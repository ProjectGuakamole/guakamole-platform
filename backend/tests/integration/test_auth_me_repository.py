"""Tests DB del repositorio SQLAlchemy de /auth/me."""

import dataclasses
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.domain.auth.me_repositories import SqlAlchemyAuthMeRepository
from app.domain.iam.access.models import OrganizationRole, PlatformRole, Status
from app.domain.iam.geography.models import City, Country, State
from app.domain.iam.organizations.models import Organization
from app.domain.iam.users.models import User

pytestmark = [pytest.mark.integration, pytest.mark.db]
pytest_plugins = ("tests.integration.test_login_repository",)

TEST_ORGANIZATION_ID = 51_001
OTHER_ORGANIZATION_ID = 51_002
ACTIVE_USER_ID = 52_001
INACTIVE_USER_ID = 52_002
ACTIVE_STATUS_ID = 53_001
INACTIVE_STATUS_ID = 53_002
PLATFORM_ROLE_ID = 53_003
ORG_ROLE_ID = 53_004
COUNTRY_ID = 53_005
STATE_ID = 53_006
CITY_ID = 53_007
SAFE_HASH = "argon2id-auth-me-test"


@pytest.fixture(autouse=True)
def auth_me_repository_cleanup(login_db_session: Session) -> None:
    cleanup_auth_me_data(login_db_session)


def cleanup_auth_me_data(session: Session) -> None:
    session.execute(
        delete(User).where(User.id_user.in_([ACTIVE_USER_ID, INACTIVE_USER_ID]))
    )
    session.execute(
        delete(Organization).where(
            Organization.id_organization.in_(
                [TEST_ORGANIZATION_ID, OTHER_ORGANIZATION_ID]
            )
        )
    )
    session.execute(delete(City).where(City.id_city == CITY_ID))
    session.execute(delete(State).where(State.id_state == STATE_ID))
    session.execute(delete(Country).where(Country.id_country == COUNTRY_ID))
    session.execute(
        delete(Status).where(
            Status.id_status.in_([ACTIVE_STATUS_ID, INACTIVE_STATUS_ID])
        )
    )
    session.execute(
        delete(PlatformRole).where(PlatformRole.id_platform_role == PLATFORM_ROLE_ID)
    )
    session.execute(
        delete(OrganizationRole).where(OrganizationRole.id_org_role == ORG_ROLE_ID)
    )
    session.commit()


def seed_auth_me_data(session: Session) -> None:
    session.add_all(
        [
            Status(id_status=ACTIVE_STATUS_ID, status="ACTIVE"),
            Status(id_status=INACTIVE_STATUS_ID, status="DISABLED"),
            PlatformRole(id_platform_role=PLATFORM_ROLE_ID, platform_role_type="USER"),
            OrganizationRole(id_org_role=ORG_ROLE_ID, org_role_type="EMPLOYEE"),
            Country(id_country=COUNTRY_ID, country_name="Auth Me Country"),
        ]
    )
    session.commit()
    session.add(
        State(id_state=STATE_ID, id_country=COUNTRY_ID, state_name="Auth Me State")
    )
    session.commit()
    session.add(City(id_city=CITY_ID, id_state=STATE_ID, city_name="Auth Me City"))
    session.commit()
    session.add_all(
        [
            build_organization(TEST_ORGANIZATION_ID, "auth-me-org", "Auth Me Org"),
            build_organization(OTHER_ORGANIZATION_ID, "auth-me-other", "Auth Me Other"),
        ]
    )
    session.commit()
    session.add_all(
        [
            build_user(
                ACTIVE_USER_ID, TEST_ORGANIZATION_ID, ACTIVE_STATUS_ID, "active"
            ),
            build_user(
                INACTIVE_USER_ID,
                TEST_ORGANIZATION_ID,
                INACTIVE_STATUS_ID,
                "inactive",
            ),
        ]
    )
    session.commit()


def build_organization(id_organization: int, slug: str, name: str) -> Organization:
    return Organization(
        id_organization=id_organization,
        id_country=COUNTRY_ID,
        id_state=STATE_ID,
        id_city=CITY_ID,
        id_status=ACTIVE_STATUS_ID,
        name=name,
        slug=slug,
        org_registered_name=f"{name} SL",
        org_tax=f"{slug}-tax",
        org_address="Calle Auth Me 1",
        org_zipcode="08001",
    )


def build_user(id_user: int, id_organization: int, id_status: int, suffix: str) -> User:
    return User(
        id_user=id_user,
        id_organization=id_organization,
        id_platform_role=PLATFORM_ROLE_ID,
        id_country=COUNTRY_ID,
        id_state=STATE_ID,
        id_city=CITY_ID,
        id_org_role=ORG_ROLE_ID,
        id_status=id_status,
        email=f"ana.{suffix}.auth-me@example.test",
        password_hash=SAFE_HASH,
        first_name="Ana",
        last_name="AuthMe",
        birthdate=date(1990, 1, 1),
        user_address="Calle Auth Me 1",
        user_zipcode="08001",
        created_at=datetime(2026, 10, 1, 10, 0, tzinfo=UTC),
        updated_at=None,
        last_login_at=None,
    )


def test_repository_finds_active_identity_by_user_and_org_public_ids(
    login_db_session: Session,
) -> None:
    seed_auth_me_data(login_db_session)
    user = login_db_session.query(User).filter_by(id_user=ACTIVE_USER_ID).one()
    organization = (
        login_db_session.query(Organization)
        .filter_by(id_organization=TEST_ORGANIZATION_ID)
        .one()
    )

    record = SqlAlchemyAuthMeRepository(login_db_session).find_active_identity(
        user_public_id=user.public_id,
        organization_public_id=organization.public_id,
    )

    assert record is not None
    assert record.user_public_id == user.public_id
    assert record.organization_public_id == organization.public_id


def test_repository_returns_none_when_org_public_id_does_not_match(
    login_db_session: Session,
) -> None:
    seed_auth_me_data(login_db_session)
    user = login_db_session.query(User).filter_by(id_user=ACTIVE_USER_ID).one()
    other_org = (
        login_db_session.query(Organization)
        .filter_by(id_organization=OTHER_ORGANIZATION_ID)
        .one()
    )

    record = SqlAlchemyAuthMeRepository(login_db_session).find_active_identity(
        user_public_id=user.public_id,
        organization_public_id=other_org.public_id,
    )

    assert record is None


def test_repository_returns_none_for_inactive_user(login_db_session: Session) -> None:
    seed_auth_me_data(login_db_session)
    user = login_db_session.query(User).filter_by(id_user=INACTIVE_USER_ID).one()
    organization = (
        login_db_session.query(Organization)
        .filter_by(id_organization=TEST_ORGANIZATION_ID)
        .one()
    )

    record = SqlAlchemyAuthMeRepository(login_db_session).find_active_identity(
        user_public_id=user.public_id,
        organization_public_id=organization.public_id,
    )

    assert record is None


def test_repository_record_does_not_expose_internal_ids(
    login_db_session: Session,
) -> None:
    seed_auth_me_data(login_db_session)
    user = login_db_session.query(User).filter_by(id_user=ACTIVE_USER_ID).one()
    organization = (
        login_db_session.query(Organization)
        .filter_by(id_organization=TEST_ORGANIZATION_ID)
        .one()
    )

    record = SqlAlchemyAuthMeRepository(login_db_session).find_active_identity(
        user_public_id=user.public_id,
        organization_public_id=organization.public_id,
    )

    assert record is not None
    record_fields = {field.name for field in dataclasses.fields(record)}
    assert "id_user" not in record_fields
    assert "id_organization" not in record_fields
    assert not hasattr(record, "id_user")
    assert not hasattr(record, "id_organization")
