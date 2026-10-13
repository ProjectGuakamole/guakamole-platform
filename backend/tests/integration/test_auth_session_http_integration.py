"""Cobertura de integración de los controles de sesión de autenticación.

Estos tests usan la aplicación de producción, PostgreSQL y las dependencias
SQLAlchemy reales para los contratos HTTP. El test de repositorio verifica la
semántica de persistencia de revocación directamente.
"""

import os
from collections.abc import Generator
from datetime import UTC, date, datetime
from typing import cast

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import get_engine, get_session_factory
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.models import RevokedAccessToken
from app.domains.auth.shared.password_hasher import PwdlibPasswordHasher
from app.domains.auth.shared.session_repository import SqlAlchemySessionStateRepository
from app.domains.auth.shared.tokens import JwtAccessTokenService
from app.domains.iam.access.models import OrganizationRole, PlatformRole, Status
from app.domains.iam.geography.models import City, Country, State
from app.domains.iam.organizations.models import Organization
from app.domains.iam.users.models import User
from app.main import create_app
from tests.integration.test_login_repository import get_test_database_url

pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.security]

ORGANIZATION_ID = 81_001
USER_ID = 82_001
DISABLED_STATUS_ID = 83_001
PLATFORM_ROLE_ID = 83_002
ORGANIZATION_ROLE_ID = 83_003
COUNTRY_ID = 83_004
STATE_ID = 83_005
CITY_ID = 83_006
ACTIVE_STATUS_ID = 83_007
REGISTRATION_PLATFORM_ROLE_ID = 83_008
REGISTRATION_ORGANIZATION_ROLE_ID = 83_009
EMAIL = "auth-session-http@example.test"
PASSWORD = "Correct" + "Password123!"
SPACED_PASSWORD = "  Valid" + "Password123!  "
WHITESPACE_PASSWORD = " " * 13
ORGANIZATION_SLUG = "auth-session-http"


@pytest.fixture
def auth_http_db_session() -> Generator[Session, None, None]:
    """Sesión aislada que elimina todos los registros creados por este módulo."""

    from sqlalchemy import create_engine

    engine = create_engine(get_test_database_url(), hide_parameters=True)
    session = Session(engine)
    cleanup_auth_http_data(session)
    try:
        yield session
    finally:
        session.rollback()
        cleanup_auth_http_data(session)
        session.close()
        engine.dispose()


@pytest.fixture
def auth_http_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """Cliente de producción configurado por entorno y sin overrides HTTP."""

    monkeypatch.setenv("DATABASE_URL", get_test_database_url())
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_ENABLE_PASSWORD_BEARER_TOKEN", "true")
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    with TestClient(create_app(), base_url="https://testserver") as client:
        yield client
    get_session_factory.cache_clear()
    get_engine.cache_clear()


def cleanup_auth_http_data(session: Session) -> None:
    """Borra los datos explícitos del módulo respetando las claves foráneas."""

    user_ids = select(User.id_user).where(
        (User.id_user == USER_ID)
        | User.email.like("auth-http-registration%@example.test")
    )
    organization_ids = select(Organization.id_organization).where(
        (Organization.id_organization == ORGANIZATION_ID)
        | Organization.slug.like("auth-http-registration%")
    )
    session.execute(delete(User).where(User.id_user.in_(user_ids)))
    session.execute(
        delete(Organization).where(Organization.id_organization.in_(organization_ids))
    )
    session.execute(
        delete(RevokedAccessToken).where(
            RevokedAccessToken.jti == "test-revocation-jti"
        )
    )
    session.execute(delete(City).where(City.id_city == CITY_ID))
    session.execute(delete(State).where(State.id_state == STATE_ID))
    session.execute(delete(Country).where(Country.id_country == COUNTRY_ID))
    session.execute(delete(Status).where(Status.id_status == DISABLED_STATUS_ID))
    session.execute(delete(Status).where(Status.id_status == ACTIVE_STATUS_ID))
    session.execute(
        delete(PlatformRole).where(PlatformRole.id_platform_role == PLATFORM_ROLE_ID)
    )
    session.execute(
        delete(OrganizationRole).where(
            OrganizationRole.id_org_role == ORGANIZATION_ROLE_ID
        )
    )
    session.execute(
        delete(PlatformRole).where(
            PlatformRole.id_platform_role == REGISTRATION_PLATFORM_ROLE_ID
        )
    )
    session.execute(
        delete(OrganizationRole).where(
            OrganizationRole.id_org_role == REGISTRATION_ORGANIZATION_ROLE_ID
        )
    )
    session.commit()


def seed_active_identity(session: Session, password_hash: str | None = None) -> None:
    """Crea una identidad IAM activa con una contraseña Argon2 real."""

    cleanup_auth_http_data(session)
    session.add_all(
        [
            Status(id_status=DISABLED_STATUS_ID, status="DISABLED_AUTH_HTTP"),
            PlatformRole(
                id_platform_role=PLATFORM_ROLE_ID, platform_role_type="USER_AUTH_HTTP"
            ),
            OrganizationRole(
                id_org_role=ORGANIZATION_ROLE_ID,
                org_role_type="EMPLOYEE_AUTH_HTTP",
            ),
            Country(id_country=COUNTRY_ID, country_name="Auth HTTP Country"),
        ]
    )
    session.commit()
    session.add(
        State(id_state=STATE_ID, id_country=COUNTRY_ID, state_name="Auth HTTP State")
    )
    session.commit()
    session.add(City(id_city=CITY_ID, id_state=STATE_ID, city_name="Auth HTTP City"))
    session.commit()
    active_status_id = get_or_create_status(session, "ACTIVE")
    session.add(
        Organization(
            id_organization=ORGANIZATION_ID,
            id_country=COUNTRY_ID,
            id_state=STATE_ID,
            id_city=CITY_ID,
            id_status=active_status_id,
            name="Auth HTTP Organization",
            slug=ORGANIZATION_SLUG,
            org_registered_name="Auth HTTP Organization SL",
            org_tax="AUTH-HTTP-TAX",
            org_address="Calle HTTP 1",
            org_zipcode="08001",
        )
    )
    session.add(
        User(
            id_user=USER_ID,
            id_organization=ORGANIZATION_ID,
            id_platform_role=PLATFORM_ROLE_ID,
            id_country=COUNTRY_ID,
            id_state=STATE_ID,
            id_city=CITY_ID,
            id_org_role=ORGANIZATION_ROLE_ID,
            id_status=active_status_id,
            email=EMAIL,
            password_hash=(
                PwdlibPasswordHasher().hash(PASSWORD)
                if password_hash is None
                else password_hash
            ),
            first_name="Ana",
            last_name="HTTP",
            birthdate=date(1990, 1, 1),
            user_address="Calle HTTP 1",
            user_zipcode="08001",
            created_at=datetime(2026, 10, 1, tzinfo=UTC),
        )
    )
    session.commit()


def get_or_create_status(session: Session, name: str) -> int:
    status_id = session.scalar(select(Status.id_status).where(Status.status == name))
    if status_id is not None:
        return status_id
    status = Status(id_status=ACTIVE_STATUS_ID, status=name)
    session.add(status)
    session.commit()
    return status.id_status


def login(client: TestClient, email: str = EMAIL, password: str = PASSWORD) -> Response:
    return cast(
        Response,
        client.post("/api/v1/auth/login", json={"email": email, "password": password}),
    )


def test_logout_revokes_session_and_rejects_reused_cookie(
    auth_http_db_session: Session, auth_http_client: TestClient
) -> None:
    seed_active_identity(auth_http_db_session)

    login_response = login(auth_http_client)
    assert login_response.status_code == 200
    raw_token = auth_http_client.cookies.get("guak_access_token")
    assert raw_token is not None
    csrf_response = auth_http_client.get("/api/v1/auth/csrf")
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.json()["csrf_token"]

    logout_response = auth_http_client.post(
        "/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_token}
    )
    assert logout_response.status_code == 200
    assert 'guak_access_token=""' in logout_response.headers["set-cookie"]

    settings = AuthSettings(jwt_secret_key=os.environ["JWT_SECRET_KEY"])
    verified_token = JwtAccessTokenService(settings).verify_access_token(raw_token)
    revoked = auth_http_db_session.scalar(
        select(RevokedAccessToken).where(RevokedAccessToken.jti == verified_token.jti)
    )
    assert revoked is not None
    assert not hasattr(revoked, "access_token")
    assert raw_token not in {
        column.name for column in RevokedAccessToken.__table__.columns
    }

    with TestClient(create_app(), base_url="https://testserver") as reused_client:
        reused_client.cookies.set("guak_access_token", raw_token, path="/api")
        assert reused_client.get("/api/v1/auth/me").status_code == 401
        assert reused_client.get("/api/v1/auth/csrf").status_code == 401
        assert (
            reused_client.post(
                "/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_token}
            ).status_code
            == 401
        )
    auth_http_db_session.delete(revoked)
    auth_http_db_session.commit()


def test_disabled_organization_invalidates_login_and_existing_session(
    auth_http_db_session: Session, auth_http_client: TestClient
) -> None:
    seed_active_identity(auth_http_db_session)
    assert login(auth_http_client).status_code == 200
    csrf_token = auth_http_client.get("/api/v1/auth/csrf").json()["csrf_token"]
    auth_http_db_session.query(Organization).filter_by(
        id_organization=ORGANIZATION_ID
    ).update({Organization.id_status: DISABLED_STATUS_ID})
    auth_http_db_session.commit()

    assert login(auth_http_client).status_code == 401
    assert auth_http_client.get("/api/v1/auth/me").status_code == 401
    assert auth_http_client.get("/api/v1/auth/csrf").status_code == 401
    assert (
        auth_http_client.post(
            "/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_token}
        ).status_code
        == 401
    )


def test_password_bearer_token_rejects_disabled_organization_without_leaks(
    auth_http_db_session: Session, auth_http_client: TestClient
) -> None:
    """El flujo OAuth2 real aplica el estado actual de la organización."""

    seed_active_identity(auth_http_db_session)
    auth_http_db_session.query(Organization).filter_by(
        id_organization=ORGANIZATION_ID
    ).update({Organization.id_status: DISABLED_STATUS_ID})
    auth_http_db_session.commit()

    response = auth_http_client.post(
        "/api/v1/auth/token", data={"username": EMAIL, "password": PASSWORD}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciales inválidas."}
    assert "access_token" not in response.text
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize("password_hash", ["", "not-a-password-hash", "$2b$invalid"])
def test_invalid_password_hashes_return_generic_authentication_errors(
    auth_http_db_session: Session,
    auth_http_client: TestClient,
    password_hash: str,
) -> None:
    seed_active_identity(auth_http_db_session, password_hash)

    login_response = login(auth_http_client)
    token_response = auth_http_client.post(
        "/api/v1/auth/token", data={"username": EMAIL, "password": PASSWORD}
    )

    for response in (login_response, token_response):
        assert response.status_code == 401
        assert response.json() == {"detail": "Credenciales inválidas."}
        assert "access_token" not in response.text
        assert "set-cookie" not in response.headers


def test_registration_preserves_password_spaces_for_real_login(
    auth_http_db_session: Session, auth_http_client: TestClient
) -> None:
    seed_registration_catalogs(auth_http_db_session)
    password = SPACED_PASSWORD
    payload = registration_payload(password)

    registration_response = auth_http_client.post(
        "/api/v1/organizations/register", json=payload
    )
    assert registration_response.status_code == 201
    assert (
        login(
            auth_http_client, "auth-http-registration@example.test", password
        ).status_code
        == 200
    )

    whitespace_payload = registration_payload(WHITESPACE_PASSWORD)
    whitespace_payload["organization"]["slug"] = "auth-http-registration-whitespace"
    whitespace_payload["organization"]["tax_id"] = "AUTH-HTTP-WHITE"
    whitespace_payload["user"]["email"] = "auth-http-registration-white@example.test"
    whitespace_payload["user"]["password_confirm"] = WHITESPACE_PASSWORD
    assert (
        auth_http_client.post(
            "/api/v1/organizations/register", json=whitespace_payload
        ).status_code
        == 422
    )


def seed_registration_catalogs(session: Session) -> None:
    """Prepara los catálogos que consume el registro HTTP real."""

    get_or_create_status(session, "ACTIVE")
    if (
        session.scalar(
            select(PlatformRole).where(PlatformRole.platform_role_type == "USER")
        )
        is None
    ):
        session.add(
            PlatformRole(
                id_platform_role=REGISTRATION_PLATFORM_ROLE_ID,
                platform_role_type="USER",
            )
        )
        session.commit()
    if (
        session.scalar(
            select(OrganizationRole).where(
                OrganizationRole.org_role_type == "COMPANY_ADMIN"
            )
        )
        is None
    ):
        session.add(
            OrganizationRole(
                id_org_role=REGISTRATION_ORGANIZATION_ROLE_ID,
                org_role_type="COMPANY_ADMIN",
            )
        )
        session.commit()
    session.add(Country(id_country=COUNTRY_ID, country_name="Auth HTTP Country"))
    session.commit()
    session.add(
        State(id_state=STATE_ID, id_country=COUNTRY_ID, state_name="Auth HTTP State")
    )
    session.commit()
    session.add(City(id_city=CITY_ID, id_state=STATE_ID, city_name="Auth HTTP City"))
    session.commit()


def registration_payload(password: str) -> dict[str, dict[str, str]]:
    return {
        "organization": {
            "name": "Registration HTTP",
            "slug": "auth-http-registration",
            "legal_name": "Registration HTTP SL",
            "tax_id": "AUTH-HTTP-REGISTER",
            "country": "Auth HTTP Country",
            "state": "Auth HTTP State",
            "city": "Auth HTTP City",
            "address": "Calle Registro 1",
            "postal_code": "08001",
        },
        "user": {
            "first_name": "Ana",
            "last_name": "Registro",
            "email": "auth-http-registration@example.test",
            "birth_date": "1990-01-01",
            "password": password,
            "password_confirm": password,
            "country": "Auth HTTP Country",
            "state": "Auth HTTP State",
            "city": "Auth HTTP City",
            "address": "Calle Registro 1",
            "postal_code": "08001",
        },
    }


def test_revocation_repository_is_idempotent(auth_http_db_session: Session) -> None:
    """Integración directa del repositorio: revocar dos veces no duplica el JTI."""

    repository = SqlAlchemySessionStateRepository(auth_http_db_session)
    expires_at = datetime(2026, 12, 1, tzinfo=UTC)

    repository.revoke("test-revocation-jti", expires_at)
    repository.revoke("test-revocation-jti", expires_at)

    assert repository.is_jti_revoked("test-revocation-jti")
    assert (
        auth_http_db_session.scalar(
            select(RevokedAccessToken).where(
                RevokedAccessToken.jti == "test-revocation-jti"
            )
        )
        is not None
    )
