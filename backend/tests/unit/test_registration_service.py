from datetime import date

import pytest

from app.domains.auth.shared.config import AuthSettings
from app.domains.iam.registration.entities import (
    RegistrationOrganization,
    RegistrationUser,
)
from app.domains.iam.registration.exceptions import (
    DuplicateRegistrationError,
    RegistrationPersistenceConflictError,
)
from app.domains.iam.registration.repository import GeographyReference
from app.domains.iam.registration.schemas import RegistrationRequest
from app.domains.iam.registration.service import RegistrationService

pytestmark = pytest.mark.test_unit


class FakeHasher:
    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{plain_password}"


class FakeRepository:
    def __init__(
        self,
        duplicates: bool = False,
        flush_conflict: bool = False,
        commit_conflict: bool = False,
    ) -> None:
        self.duplicates = duplicates
        self.flush_conflict = flush_conflict
        self.commit_conflict = commit_conflict
        self.organization: RegistrationOrganization | None = None
        self.user: RegistrationUser | None = None

    def has_duplicates(self, *, email: str, slug: str, tax_id: str) -> bool:
        _ = (email, slug, tax_id)
        return self.duplicates

    def get_status_id(self, status_name: str) -> int | None:
        _ = status_name
        return 1

    def get_platform_role_id(self, role_name: str) -> int | None:
        _ = role_name
        return 2

    def get_organization_role_id(self, role_name: str) -> int | None:
        _ = role_name
        return 3

    def get_geography(
        self, *, country: str, state: str, city: str
    ) -> GeographyReference:
        _ = (country, state, city)
        return GeographyReference(country_id=4, state_id=5, city_id=6)

    def add_organization(self, organization: RegistrationOrganization) -> None:
        self.organization = organization

    def add_user(self, user: RegistrationUser) -> None:
        self.user = user

    def flush(self) -> None:
        if self.flush_conflict:
            raise RegistrationPersistenceConflictError("detalle interno durante flush")
        assert self.organization is not None
        self.organization.id = 99

    def commit(self) -> None:
        if self.commit_conflict:
            raise RegistrationPersistenceConflictError("detalle interno durante commit")

    def rollback(self) -> None:
        return


class CapturingAuditLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, str]]] = []

    def emit(self, *, action: str, metadata: dict[str, str]) -> None:
        self.events.append((action, metadata))


class FailingAuditLogger:
    def emit(self, *, action: str, metadata: dict[str, str]) -> None:
        _ = (action, metadata)
        raise RuntimeError("fallo de auditoría")


def build_request() -> RegistrationRequest:
    return RegistrationRequest.model_validate(
        {
            "organization": {
                "name": "Mi Empresa",
                "slug": "mi-empresa",
                "legal_name": "Mi Empresa S.L.",
                "tax_id": "B12345678",
                "country": "España",
                "state": "Catalunya",
                "city": "Barcelona",
                "address": "Calle Mayor 10",
                "postal_code": "08001",
            },
            "user": {
                "first_name": "Ana",
                "last_name": "García",
                "email": "ana@empresa.com",
                "birth_date": date(1990, 1, 1),
                "password": "PasswordSeguro123!",
                "password_confirm": "PasswordSeguro123!",
                "country": "España",
                "state": "Catalunya",
                "city": "Barcelona",
                "address": "Calle Mayor 10",
                "postal_code": "08001",
            },
        }
    )


def build_settings() -> AuthSettings:
    return AuthSettings.model_validate(
        {
            "app_env": "test",
            "database_url": "postgresql+psycopg://test:test@localhost/guakamole_test",
            "jwt_secret_key": "test-secret-not-for-production-with-safe-length",
        }
    )


def test_service_translates_duplicate_conflict_and_hashes_password() -> None:
    with pytest.raises(DuplicateRegistrationError):
        RegistrationService(
            FakeRepository(duplicates=True), FakeHasher(), build_settings()
        ).register(build_request())

    repository = FakeRepository()
    response = RegistrationService(repository, FakeHasher(), build_settings()).register(
        build_request()
    )
    assert response.organization_id.startswith("org_")
    assert repository.user is not None
    assert repository.user.password_hash != build_request().user.password


def test_service_translates_persistence_conflict_during_flush() -> None:
    with pytest.raises(DuplicateRegistrationError) as raised_error:
        RegistrationService(
            FakeRepository(flush_conflict=True), FakeHasher(), build_settings()
        ).register(build_request())

    assert str(raised_error.value) == ""
    assert "detalle interno durante flush" not in str(raised_error.value)


def test_service_translates_persistence_conflict_during_commit() -> None:
    with pytest.raises(DuplicateRegistrationError) as raised_error:
        RegistrationService(
            FakeRepository(commit_conflict=True), FakeHasher(), build_settings()
        ).register(build_request())

    assert str(raised_error.value) == ""
    assert "detalle interno durante commit" not in str(raised_error.value)


def test_service_audits_registration_with_only_safe_identifiers() -> None:
    audit_logger = CapturingAuditLogger()

    RegistrationService(
        FakeRepository(), FakeHasher(), build_settings(), audit_logger
    ).register(build_request())

    assert len(audit_logger.events) == 2
    metadata = [event[1] for event in audit_logger.events]
    assert metadata[0].keys() == {"organization_id"}
    assert metadata[0]["organization_id"].startswith("org_")
    assert metadata[1]["user_id"].startswith("usr_")
    assert len(metadata[1]["email_hash"]) == 64
    assert "password" not in repr(metadata).lower()
    assert "token" not in repr(metadata).lower()


def test_service_completes_registration_when_audit_logging_fails() -> None:
    response = RegistrationService(
        FakeRepository(), FakeHasher(), build_settings(), FailingAuditLogger()
    ).register(build_request())

    assert response.organization_id.startswith("org_")
    assert response.user_id.startswith("usr_")
